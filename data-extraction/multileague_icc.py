"""Does the variance budget generalise beyond one league?

Estimates the same one-way random-effects decomposition in every league returned
by crawl_leagues.py, then reports the distribution of the ICC and the implied
win probability across leagues, and tests whether either depends on league size
or scoring format.

Third-party leagues are anonymous here: only size, scoring type, and the matrix
of weekly scores are used.
"""
import json, math, statistics
from pathlib import Path
from statistics import NormalDist

OUT = Path(__file__).parent / "output" / "multileague"
Phi = NormalDist(0, 1).cdf


def budget(groups):
    ns = [len(v) for v in groups]
    N, k = sum(ns), len(groups)
    if k < 6 or N < 60:
        return None
    grand = sum(sum(v) for v in groups) / N
    MSW = sum(sum((x - statistics.mean(v)) ** 2 for x in v) for v in groups) / (N - k)
    MSB = sum(len(v) * (statistics.mean(v) - grand) ** 2 for v in groups) / (k - 1)
    n0 = (N - sum(n * n for n in ns) / N) / (k - 1)
    tau2 = max((MSB - MSW) / n0, 0.0)
    if MSW <= 0:
        return None
    rho = tau2 / (tau2 + MSW)
    return {"tau2": tau2, "sigma2": MSW, "rho": rho,
            "kappa": math.sqrt(rho / (2 * (1 - rho))) if rho < 1 else float("inf"),
            "k": k, "N": N}


def pear(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    n = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    d = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return n / d if d else 0.0


def main():
    data = json.loads((OUT / "scores.json").read_text())
    res = []
    for lg in data:
        b = budget(lg["scores"])
        if b:
            b["teams"] = lg["teams"]; b["scoring"] = lg["scoring"]
            b["ppr"] = ("PPR" if (lg["scoring"] or 0) >= 0.9 else
                        "half" if (lg["scoring"] or 0) >= 0.4 else "std")
            res.append(b)
    if not res:
        print("no usable leagues"); return

    rhos = sorted(r["rho"] for r in res)
    ps = sorted(Phi(r["kappa"]) for r in res)
    def q(v, p):                       # linear-interpolated quantile
        i = p * (len(v) - 1)
        lo = int(i)
        return v[lo] * (1 - (i - lo)) + v[min(lo + 1, len(v) - 1)] * (i - lo)
    print("=" * 80)
    print(f"  VARIANCE BUDGET ACROSS {len(res)} PUBLIC SLEEPER LEAGUES (2025)")
    print("=" * 80)
    print(f"  {'':22}{'median':>10}{'IQR':>22}{'10-90 pct':>22}")
    for lbl, v in (("ICC (rho)", rhos), ("P(+1 SD wins a week)", ps)):
        print(f"  {lbl:22}{q(v,.5):>10.4f}"
              f"{'[' + format(q(v,.25),'.4f') + ', ' + format(q(v,.75),'.4f') + ']':>22}"
              f"{'[' + format(q(v,.10),'.4f') + ', ' + format(q(v,.90),'.4f') + ']':>22}")
    print(f"\n  mean sigma (within-manager, pts/wk)  {statistics.mean(math.sqrt(r['sigma2']) for r in res):>7.1f}")
    print(f"  mean tau   (between managers, pts/wk) {statistics.mean(math.sqrt(r['tau2']) for r in res):>7.1f}")
    print(f"  share of leagues with rho < 0.10:     {sum(1 for r in rhos if r < .10)/len(rhos)*100:>6.0f}%")
    print(f"  share of leagues with rho < 0.20:     {sum(1 for r in rhos if r < .20)/len(rhos)*100:>6.0f}%")

    print()
    print("  by league size:")
    print(f"    {'teams':>7}{'n':>5}{'median rho':>13}{'median P(win)':>15}")
    for lo, hi, lbl in ((0, 9, "<=9"), (10, 10, "10"), (11, 12, "11-12"), (13, 99, "13+")):
        s = [r for r in res if lo <= (r["teams"] or 0) <= hi]
        if len(s) >= 5:
            print(f"    {lbl:>7}{len(s):>5}{statistics.median(r['rho'] for r in s):>13.4f}"
                  f"{statistics.median(Phi(r['kappa']) for r in s):>15.4f}")
    print("\n  by scoring:")
    print(f"    {'format':>7}{'n':>5}{'median rho':>13}")
    for f in ("std", "half", "PPR"):
        s = [r for r in res if r["ppr"] == f]
        if len(s) >= 5:
            print(f"    {f:>7}{len(s):>5}{statistics.median(r['rho'] for r in s):>13.4f}")

    sizes = [r["teams"] for r in res if r["teams"]]
    rr = [r["rho"] for r in res if r["teams"]]
    print(f"\n  corr(league size, ICC) = {pear(sizes, rr):+.3f}   (n={len(rr)})")
    print("\n  Fat Man's Fantasy, for comparison:  rho = 0.0390, P(+1 SD) = 0.557")
    pct = sum(1 for r in rhos if r < 0.0390) / len(rhos) * 100
    print(f"  -> that league sits at the {pct:.0f}th percentile of this sample")


if __name__ == "__main__":
    main()
