"""Do the measurable behaviours actually PREDICT how a manager does?

Everything prior to this was correlational: six behaviours, six correlations with
a shrunk manager effect, n=14. That cannot separate signal from overfitting. Here
the unit is the manager-SEASON (n=56), the outcome is that season's WIN TOTAL, and the model
is scored by leave-one-out cross-validation, so the reported fit is
out-of-sample.

Wins is used rather than points because lineup efficiency is defined as
actual/optimal points: regressing points on it is partly circular. Wins is
determined by points but is not mechanically identical to any predictor.

Ridge regularisation is used because the predictors are collinear (a manager who
claims often also spends more) and n is small relative to p.
"""
import collections, json, math, statistics, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
SK = json.loads((OUT / "sleeper" / "season_skill_cache.json").read_text())
BW = json.loads((OUT / "sleeper" / "weekly_stats_byweek.json").read_text())
GR = json.loads((OUT / "draft_grades.json").read_text())
FLEX = {"FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
        "REC_FLEX": {"WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"}}
FEATURES = ["waiver claims", "points per $", "overpay $", "early busts", "lineup %"]


WINS = {}


def build():
    for yr, lid in (("2025","1257482235834028032"),("2024","1124841011114168320"),
                    ("2023","998364322315190272"),("2022","859910378069577728")):
        d = SK[yr]
        for r in json.load(urllib.request.urlopen(
                f"https://api.sleeper.app/v1/league/{lid}/rosters")):
            who = d["rid2who"].get(str(r["roster_id"])) or d["rid2who"].get(r["roster_id"])
            if who: WINS[(yr, who)] = r["settings"]["wins"]
    players = json.load(urllib.request.urlopen("https://api.sleeper.app/v1/players/nfl"))
    pos = lambda p: (players.get(p) or {}).get("position")

    def best(slots, pts):
        used, tot = set(), 0.0
        for s in [x for x in slots if x not in FLEX]:
            c = max(((v, p) for p, v in pts.items() if p not in used and pos(p) == s), default=None)
            if c: used.add(c[1]); tot += c[0]
        for s in [x for x in slots if x in FLEX]:
            ok = FLEX[s]
            c = max(((v, p) for p, v in pts.items() if p not in used and pos(p) in ok), default=None)
            if c: used.add(c[1]); tot += c[0]
        return tot

    after = lambda pid, yr, wk: sum(BW.get(yr, {}).get(str(w), {}).get(pid, 0.0) or 0.0
                                    for w in range(int(wk), 15))
    rows = []
    for yr, d in SK.items():
        slots = [s for s in d["roster_positions"] if s != "BN"]
        act = collections.defaultdict(float); opt = collections.defaultdict(float)
        started = collections.defaultdict(set)
        for wk, ms in d["weeks"].items():
            for m in ms:
                who = d["rid2who"].get(str(m["roster_id"])) or d["rid2who"].get(m["roster_id"])
                if not who: continue
                pp = m.get("players_points") or {}
                act[who] += sum(pp.get(p, 0) for p in (m.get("starters") or []))
                opt[who] += best(slots, pp)
                for p in (m.get("starters") or []): started[who].add((int(wk), p))
        auc = collections.defaultdict(list)
        for t in d["tx"]:
            if t.get("type") != "waiver": continue
            bid = (t.get("settings") or {}).get("waiver_bid"); adds = t.get("adds") or {}
            if bid is None or not adds: continue
            who = d["rid2who"].get(str(t["roster_ids"][0])) or d["rid2who"].get(t["roster_ids"][0])
            for pid in adds:
                auc[(t.get("leg"), pid)].append((bid, who, t.get("status") == "complete"))
        att = collections.Counter(); spent = collections.Counter()
        wire = collections.defaultdict(float); over = collections.defaultdict(list)
        for (wk, pid), bids in auc.items():
            if not wk: continue
            for b, who, wonit in bids:
                if who: att[who] += 1
            w = next((b for b in bids if b[2]), None)
            if not w: continue
            wbid, who, _ = w
            if not who: continue
            spent[who] += wbid
            wire[who] += sum(BW.get(yr, {}).get(str(x), {}).get(pid, 0.0) or 0.0
                             for x in range(int(wk), 15) if (x, pid) in started[who])
            losers = [b[0] for b in bids if not b[2]]
            if losers: over[who].append(wbid - max(losers))
        for who in act:
            e = [p for p in GR["picks"] if p["who"] == who and p["yr"] == yr and p["rd"] <= 4]
            if not e or not opt[who] or att[who] < 3: continue
            rows.append({"yr": yr, "who": who, "points": act[who],
                         "wins": WINS.get((yr, who)),
                         "waiver claims": att[who],
                         "points per $": wire[who] / max(spent[who], 1),
                         "overpay $": statistics.mean(over[who]) if over[who] else 0.0,
                         "early busts": sum(1 for p in e if p["val"] < -50),
                         "lineup %": act[who] / opt[who] * 100})
    return rows


def ridge(X, y, lam):
    n, p = len(X), len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) + (lam if a == b else 0) for b in range(p)]
         for a in range(p)]
    bvec = [sum(X[i][a] * y[i] for i in range(n)) for a in range(p)]
    M = [A[i][:] + [bvec[i]] for i in range(p)]
    for c in range(p):
        pr = max(range(c, p), key=lambda r: abs(M[r][c])); M[c], M[pr] = M[pr], M[c]
        for r in range(p):
            if r != c and M[c][c]:
                f = M[r][c] / M[c][c]
                for cc in range(c, p + 1): M[r][cc] -= f * M[c][cc]
    return [M[i][p] / M[i][i] if M[i][i] else 0.0 for i in range(p)]


def main():
    rows = [r for r in build() if r["wins"] is not None]
    y = [float(r["wins"]) for r in rows]
    mu = {f: statistics.mean(r[f] for r in rows) for f in FEATURES}
    sd = {f: statistics.pstdev(r[f] for r in rows) or 1 for f in FEATURES}
    X = [[1.0] + [(r[f] - mu[f]) / sd[f] for f in FEATURES] for r in rows]

    print("=" * 78)
    print(f"  PREDICTING A SEASON'S WIN TOTAL FROM BEHAVIOUR  (n = {len(rows)})")
    print("=" * 78)
    ybar = statistics.mean(y); sst = sum((v - ybar) ** 2 for v in y)
    print(f"  {'lambda':>8}{'in-sample R2':>15}{'LOO R2':>12}")
    best_lam, best_r2 = None, -9
    for lam in (0, 1, 3, 10, 30, 100, 300):
        beta = ridge(X, y, lam)
        pred = [sum(b * xi for b, xi in zip(beta, X[i])) for i in range(len(X))]
        r2 = 1 - sum((y[i] - pred[i]) ** 2 for i in range(len(y))) / sst
        err = 0.0
        for i in range(len(X)):
            Xi = X[:i] + X[i + 1:]; yi = y[:i] + y[i + 1:]
            b2 = ridge(Xi, yi, lam)
            err += (y[i] - sum(b * xi for b, xi in zip(b2, X[i]))) ** 2
        loo = 1 - err / sst
        print(f"  {lam:>8}{r2:>15.3f}{loo:>12.3f}")
        if loo > best_r2: best_r2, best_lam = loo, lam
    print(f"\n  best lambda = {best_lam}, out-of-sample R2 = {best_r2:.3f}")

    beta = ridge(X, y, best_lam)
    print(f"\n  {'feature':22}{'wins per SD':>15}{'direction':>12}")
    for f, b in sorted(zip(FEATURES, beta[1:]), key=lambda t: -abs(t[1])):
        print(f"  {f:22}{b:>+15.2f}{'helps' if b > 0 else 'hurts':>12}")

    print("\n" + "=" * 78)
    print("  WHERE EACH MANAGER RANKS  (career averages, 3+ seasons only)")
    print("=" * 78)
    # Ranking needs a stable per-manager average, so require three seasons.
    # The model above still uses every manager-season, including short stints.
    MIN_SEASONS = 3
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    seasons = collections.defaultdict(set)
    for r in rows:
        seasons[r["who"]].add(r["yr"])
        for f in FEATURES: agg[r["who"]][f].append(r[f])
    dropped = sorted(w for w in agg if len(seasons[w]) < MIN_SEASONS)
    for w in dropped: del agg[w]
    who_list = list(agg)
    if dropped:
        print(f"  (excluded, fewer than {MIN_SEASONS} seasons: "
              + ", ".join(f"{w} [{len(seasons[w])}]" for w in dropped) + ")")
    print(f"  {'manager':22}" + "".join(f"{f[:12]:>14}" for f in FEATURES))
    ranks = {}
    for f in FEATURES:
        hi_good = f in ("waiver claims", "points per $", "lineup %")
        order = sorted(who_list, key=lambda w: -statistics.mean(agg[w][f]) if hi_good
                       else statistics.mean(agg[w][f]))
        for i, w in enumerate(order, 1): ranks.setdefault(w, {})[f] = i
    for w in sorted(who_list, key=lambda w: statistics.mean(ranks[w].values())):
        mark = " <<<" if w in ("mikeion", "Gordonulus") else ""
        print(f"  {w:22}" + "".join(f"{ranks[w][f]:>14}" for f in FEATURES) + mark)
    json.dump({"rows": rows, "ranks": ranks, "n_ranked": len(who_list), "beta": dict(zip(FEATURES, beta[1:])),
               "loo_r2": best_r2, "lam": best_lam},
              open(OUT / "predict_quality.json", "w"), indent=1)


if __name__ == "__main__":
    main()
