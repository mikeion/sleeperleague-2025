"""Where each manager sits against the league on everything they control.

Six dimensions, all oriented so higher = better, then z-scored across managers.
The point is to separate "bad season" from "systematically doing one thing wrong".
"""
import collections, json, math, statistics, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
SK = json.loads((OUT / "sleeper" / "season_skill_cache.json").read_text())
BW = json.loads((OUT / "sleeper" / "weekly_stats_byweek.json").read_text())
GR = json.loads((OUT / "draft_grades.json").read_text())
FLEX_OK = {"FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
           "REC_FLEX": {"WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"}}


def J(u):
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.load(r)


players = J("https://api.sleeper.app/v1/players/nfl")
pos_of = lambda p: (players.get(p) or {}).get("position")
after = lambda pid, yr, wk: sum(BW.get(yr, {}).get(str(w), {}).get(pid, 0.0) or 0.0
                                for w in range(int(wk), 15))


def optimal(slots, pts):
    used, tot = set(), 0.0
    for s in [x for x in slots if x not in FLEX_OK]:
        b = max(((v, p) for p, v in pts.items() if p not in used and pos_of(p) == s), default=None)
        if b: used.add(b[1]); tot += b[0]
    for s in [x for x in slots if x in FLEX_OK]:
        ok = FLEX_OK[s]
        b = max(((v, p) for p, v in pts.items() if p not in used and pos_of(p) in ok), default=None)
        if b: used.add(b[1]); tot += b[0]
    return tot


M = collections.defaultdict(lambda: collections.defaultdict(float))
seasons = collections.defaultdict(set)
for yr, d in SK.items():
    slots = [s for s in d["roster_positions"] if s != "BN"]
    for ms in d["weeks"].values():
        for m in ms:
            who = d["rid2who"].get(str(m["roster_id"])) or d["rid2who"].get(m["roster_id"])
            if not who: continue
            pp = m.get("players_points") or {}
            M[who]["act"] += sum(pp.get(p, 0) for p in (m.get("starters") or []))
            M[who]["opt"] += optimal(slots, pp)
            seasons[who].add(yr)

auc = collections.defaultdict(list)
for yr, d in SK.items():
    for t in d["tx"]:
        if t.get("type") != "waiver": continue
        bid = (t.get("settings") or {}).get("waiver_bid"); adds = t.get("adds") or {}
        if bid is None or not adds: continue
        who = d["rid2who"].get(str(t["roster_ids"][0])) or d["rid2who"].get(t["roster_ids"][0])
        for pid in adds:
            auc[(yr, t.get("leg"), pid)].append((bid, who, t.get("status") == "complete"))
for (yr, wk, pid), bids in auc.items():
    w = next((b for b in bids if b[2]), None)
    if not w or not wk: continue
    wbid, wwho, _ = w
    losers = [b for b in bids if not b[2]]
    M[wwho]["won"] += 1; M[wwho]["spent"] += wbid; M[wwho]["wirepts"] += after(pid, yr, wk)
    if losers:
        M[wwho]["cwins"] += 1
        M[wwho]["overpay"] += wbid - max(b[0] for b in losers)
    for who in {b[1] for b in losers}:
        M[who]["lost"] += 1

for p in GR["picks"]:
    if p["rd"] <= 4:
        M[p["who"]]["e_val"] += p["val"]; M[p["who"]]["e_n"] += 1
        if p["val"] < -50: M[p["who"]]["e_bust"] += 1

DIMS = [("Waiver volume", "claims per season"),
        ("Bid discipline", "less overpay per contested win"),
        ("Waiver efficiency", "points per FAAB dollar"),
        ("Lineup setting", "% of optimal lineup started"),
        ("Early-round value", "value per pick, rounds 1-4"),
        ("Bust avoidance", "share of rounds 1-4 that bust")]

raw = {}
for who, a in M.items():
    n = len(seasons.get(who, [])) or 1
    if a["opt"] == 0 or a["e_n"] < 8: continue
    raw[who] = [
        (a["won"] + a["lost"]) / n,
        -(a["overpay"] / max(a["cwins"], 1)),
        a["wirepts"] / max(a["spent"], 1),
        a["act"] / a["opt"] * 100,
        a["e_val"] / a["e_n"],
        -(a["e_bust"] / a["e_n"] * 100),
    ]

names = list(raw)
z = {w: [] for w in names}
for i in range(len(DIMS)):
    col = [raw[w][i] for w in names]
    mu, sd = statistics.mean(col), statistics.pstdev(col) or 1
    for w in names: z[w].append((raw[w][i] - mu) / sd)

print("=" * 96)
print("  MANAGER PROFILE — standard deviations from the league mean (higher is better)")
print("=" * 96)
hdr = f"  {'Manager':21}" + "".join(f"{d[0][:13]:>15}" for d in DIMS)
print(hdr); print("  " + "-" * (len(hdr) - 2))
for w in sorted(names, key=lambda w: -sum(z[w])):
    star = "  <<<" if w in ("mikeion", "Gordonulus") else ""
    print(f"  {w:21}" + "".join(f"{v:>+15.2f}" for v in z[w]) + star)
print()
for d, k in DIMS:
    print(f"  {d:20} = {k}")

json.dump({"dims": [d[0] for d in DIMS], "z": z, "raw": raw},
          open(OUT / "manager_profile.json", "w"), indent=1)
print(f"\nwrote {OUT / 'manager_profile.json'}")
