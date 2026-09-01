"""Variance budget for head-to-head fantasy football.

Produces every number reported in writeups/skill_ceiling.tex.

Model.  For manager m in week t,  Y_mt = mu + alpha_m + eps_mt,
with alpha_m ~ (0, tau^2) independent of eps_mt ~ (0, sigma^2).
A head-to-head margin is D = Y_mt - Y_m't, so the noise enters twice and the
talent gap once:  P(m beats m') = Phi( delta / (sigma * sqrt 2) ) where
delta = alpha_m - alpha_m'.  Define the skill-to-noise ratio
kappa = tau / (sigma * sqrt 2); a manager c SDs above average wins a given week
with probability Phi(c * kappa).

Estimation is unbalanced one-way ANOVA (Searle, Casella & McCulloch 1992),
with a nonparametric bootstrap over managers for interval estimates.
"""
import collections, json, math, random, statistics
from pathlib import Path
from statistics import NormalDist

OUT = Path(__file__).parent / "output"
SK = json.loads((OUT / "sleeper" / "season_skill_cache.json").read_text())
FLEX = {"FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
        "REC_FLEX": {"WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"}}
Phi = NormalDist(0, 1).cdf
random.seed(11)


def anova(groups):
    """Unbalanced one-way random effects -> (tau2, sigma2, n0)."""
    ns = [len(v) for v in groups]
    N, k = sum(ns), len(groups)
    grand = sum(sum(v) for v in groups) / N
    MSW = sum(sum((x - statistics.mean(v)) ** 2 for x in v) for v in groups) / (N - k)
    MSB = sum(len(v) * (statistics.mean(v) - grand) ** 2 for v in groups) / (k - 1)
    n0 = (N - sum(n * n for n in ns) / N) / (k - 1)
    return max((MSB - MSW) / n0, 0.0), MSW, n0


def budget(groups):
    tau2, sig2, n0 = anova(groups)
    tau, sig = math.sqrt(tau2), math.sqrt(sig2)
    kappa = tau / (sig * math.sqrt(2)) if sig else 0.0
    return {"tau2": tau2, "sigma2": sig2, "icc": tau2 / (tau2 + sig2),
            "tau": tau, "sigma": sig, "kappa": kappa,
            "p1sd": Phi(kappa), "n0": n0}


def boot(groups, B=2000):
    """Nonparametric bootstrap resampling MANAGERS (the unit of clustering)."""
    out = collections.defaultdict(list)
    for _ in range(B):
        g = [random.choice(groups) for _ in groups]
        try:
            b = budget(g)
        except Exception:
            continue
        for k, v in b.items():
            out[k].append(v)
    return {k: (sorted(v)[int(.025 * len(v))], sorted(v)[int(.975 * len(v))])
            for k, v in out.items()}


CACHE = OUT / "variance_inputs.json"


def collect():
    """actual = points started; optimal = best legal lineup that week."""
    if CACHE.exists():
        d = json.loads(CACHE.read_text())
        return d["act"], d["opt"], d["byseason"]
    import urllib.request
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

    act, opt, byseason = collections.defaultdict(list), collections.defaultdict(list), {}
    for yr, d in SK.items():
        slots = [s for s in d["roster_positions"] if s != "BN"]
        per = collections.defaultdict(list)
        for wk, ms in d["weeks"].items():
            for m in ms:
                who = d["rid2who"].get(str(m["roster_id"])) or d["rid2who"].get(m["roster_id"])
                if not who or m["points"] <= 0:
                    continue
                act[who].append(m["points"])
                opt[who].append(best(slots, m.get("players_points") or {}))
                per[who].append(m["points"])
        byseason[yr] = [v for v in per.values() if len(v) >= 10]
    CACHE.write_text(json.dumps({"act": act, "opt": opt, "byseason": byseason}))
    return act, opt, byseason


def main():
    act, opt, byseason = collect()
    A = [v for v in act.values() if len(v) >= 20]
    O = [v for v in opt.values() if len(v) >= 20]

    print("=" * 78)
    print("  TABLE 1 — VARIANCE BUDGET, WEEKLY TEAM SCORE")
    print("=" * 78)
    for lbl, g in (("actual lineup", A), ("optimal lineup", O)):
        b = budget(g); ci = boot(g)
        print(f"\n  {lbl}   (k={len(g)} managers, {sum(len(x) for x in g)} manager-weeks)")
        print(f"    sigma^2 (within, week to week)  {b['sigma2']:>8.1f}"
              f"   [{ci['sigma2'][0]:.0f}, {ci['sigma2'][1]:.0f}]")
        print(f"    tau^2   (between managers)      {b['tau2']:>8.1f}"
              f"   [{ci['tau2'][0]:.1f}, {ci['tau2'][1]:.1f}]")
        print(f"    ICC                             {b['icc']:>8.4f}"
              f"   [{ci['icc'][0]:.4f}, {ci['icc'][1]:.4f}]")
        print(f"    kappa = tau/(sigma*sqrt2)       {b['kappa']:>8.4f}"
              f"   [{ci['kappa'][0]:.4f}, {ci['kappa'][1]:.4f}]")
        print(f"    P(+1 SD manager wins a week)    {b['p1sd']:>8.4f}"
              f"   [{ci['p1sd'][0]:.4f}, {ci['p1sd'][1]:.4f}]")

    b = budget(A)
    print("\n" + "=" * 78)
    print("  TABLE 2 — WIN PROBABILITY AND SEASON RECORD")
    print("=" * 78)
    print(f"  {'talent edge':>12}{'P(win week)':>14}{'E[wins in 14]':>16}{'P(record>.500)':>16}")
    for c in (0.5, 1, 2, 3):
        p = Phi(c * b["kappa"])
        pw = sum(math.comb(14, w) * p ** w * (1 - p) ** (14 - w) for w in range(8, 15))
        print(f"  {'+' + str(c) + ' SD':>12}{p:>14.3f}{14 * p:>16.2f}{pw:>16.3f}")

    print("\n" + "=" * 78)
    print("  TABLE 3 — HOW LONG TO MEASURE A MANAGER")
    print("=" * 78)
    rho = b["icc"]
    print(f"  Spearman-Brown reliability of a k-week mean, rho = {rho:.4f}")
    for k in (14, 28, 56, 104, 208):
        print(f"    k={k:>4} weeks ({k/14:>4.1f} seasons)   reliability = {k*rho/(1+(k-1)*rho):.3f}")
    need = 0.8 * (1 - rho) / (rho * 0.2)
    print(f"  weeks for reliability 0.80: {need:.0f}  ({need/14:.1f} seasons)")

    print("\n" + "=" * 78)
    print("  TABLE 4 — STABILITY ACROSS SEASONS")
    print("=" * 78)
    print(f"  {'season':>8}{'k':>4}{'sigma^2':>10}{'tau^2':>9}{'ICC':>9}{'P(+1SD)':>10}")
    for yr in sorted(byseason):
        g = byseason[yr]
        if len(g) < 8: continue
        s = budget(g)
        print(f"  {yr:>8}{len(g):>4}{s['sigma2']:>10.1f}{s['tau2']:>9.1f}"
              f"{s['icc']:>9.4f}{s['p1sd']:>10.3f}")

    print("\n" + "=" * 78)
    print("  TABLE 5 — VALIDATION: predicted vs observed spread in season records")
    print("=" * 78)
    obs = []
    for yr, d in SK.items():
        per = collections.defaultdict(list)
        for wk, ms in d["weeks"].items():
            bym = collections.defaultdict(list)
            for m in ms:
                if m.get("matchup_id") is not None: bym[m["matchup_id"]].append(m)
            for pair in bym.values():
                if len(pair) != 2: continue
                a, c = pair
                wa = d["rid2who"].get(str(a["roster_id"])) or d["rid2who"].get(a["roster_id"])
                wc = d["rid2who"].get(str(c["roster_id"])) or d["rid2who"].get(c["roster_id"])
                if a["points"] == c["points"]: continue
                per[wa].append(a["points"] > c["points"]); per[wc].append(c["points"] > a["points"])
        for who, r in per.items():
            if len(r) >= 10: obs.append(sum(r) / len(r))
    sd_obs = statistics.pstdev(obs)
    p = 0.5
    sd_binom = math.sqrt(p * (1 - p) / 14)
    sd_pred = math.sqrt(sd_binom ** 2 + (b["kappa"] * NormalDist(0, 1).pdf(0) * 2) ** 2 * 1)
    print(f"  observed SD of season win rate            {sd_obs:.4f}")
    print(f"  SD from a pure coin flip (n=14)           {sd_binom:.4f}")
    print(f"  implied SD from talent, sqrt(obs^2-coin^2) "
          f"{math.sqrt(max(sd_obs**2 - sd_binom**2, 0)):.4f}")
    print(f"  model-predicted talent SD  2*phi(0)*kappa {2*NormalDist(0,1).pdf(0)*b['kappa']:.4f}")
    print("\n  (the last two lines are the test: an independent estimate of talent")
    print("   spread from season RECORDS, against the one derived from weekly SCORES)")


if __name__ == "__main__":
    main()
