"""Do the same managers stay on top? The direct test of "some people are just good".

Variance components answer this indirectly. This answers it the way a league
member would ask it: does last year's finish predict this year's, do top-four
teams repeat, and is the best four-year record beyond what fourteen coin-flippers
would produce.
"""
import collections, json, math, statistics
from math import comb
from pathlib import Path

OUT = Path(__file__).parent / "output"
SK = json.loads((OUT / "sleeper" / "season_skill_cache.json").read_text())
WW = json.loads((OUT / "what_wins.json").read_text())
YRS = ["2022", "2023", "2024", "2025"]


def pear(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    n = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    d = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return n / d if d else 0.0


def main():
    wins = collections.defaultdict(dict)
    draft = collections.defaultdict(dict)
    for r in WW:
        wins[r["who"]][r["yr"]] = r["wins"]; draft[r["who"]][r["yr"]] = r["draft"]
    pts = collections.defaultdict(dict)
    for yr, d in SK.items():
        r2w = d["rid2who"]; tot = collections.Counter()
        for wk, ms in d["weeks"].items():
            for m in ms:
                w = r2w.get(str(m["roster_id"])) or r2w.get(m["roster_id"])
                if w: tot[w] += m["points"]
        for w, v in tot.items(): pts[w][yr] = v

    print("=" * 74)
    print("  YEAR-TO-YEAR PERSISTENCE")
    print("=" * 74)
    for lbl, D in (("season wins", wins), ("season points", pts), ("draft score", draft)):
        rs = []
        for a, b in zip(YRS, YRS[1:]):
            pair = [(D[w][a], D[w][b]) for w in D if a in D[w] and b in D[w]]
            rs.append(pear([x for x, _ in pair], [y for _, y in pair]))
        print(f"  {lbl:15}" + "  ".join(f"{a[2:]}->{b[2:]} {r:+.3f}"
                                        for (a, b), r in zip(zip(YRS, YRS[1:]), rs))
              + f"   pooled {statistics.mean(rs):+.3f}")

    print("\n" + "=" * 74)
    print("  DO TOP-FOUR FINISHES REPEAT?")
    print("=" * 74)
    rep = tot_ = 0
    for a, b in zip(YRS, YRS[1:]):
        ta = sorted([w for w in wins if a in wins[w]], key=lambda w: -wins[w][a])[:4]
        tb = sorted([w for w in wins if b in wins[w]], key=lambda w: -wins[w][b])[:4]
        r = len(set(ta) & set(tb)); rep += r; tot_ += 4
        print(f"  {a} top-4 -> {b} top-4: {r}/4")
    k = len({w for w in wins})
    print(f"  overall {rep}/{tot_} = {rep/tot_*100:.0f}%; chance alone gives {4/k*100:.0f}%")

    print("\n" + "=" * 74)
    print("  IS THE BEST RECORD BEYOND CHANCE?")
    print("=" * 74)
    best = max(wins, key=lambda w: sum(wins[w].values()))
    W = sum(wins[best].values()); N = sum(len(wins[w]) for w in [best]) * 14
    p1 = sum(comb(N, i) for i in range(W, N + 1)) / 2 ** N
    pk = 1 - (1 - p1) ** k
    print(f"  best record: {best} at {W}-{N-W}")
    print(f"  P(one 50/50 manager does this)          {p1:.4f}")
    print(f"  P(at least one of {k} managers does)      {pk:.4f}")
    print(f"  -> {'beyond chance' if pk < .05 else 'NOT beyond chance at the 5% level'}")
    print("\n  The single-manager probability is the wrong one: nobody picked this")
    print("  manager in advance. We looked at all of them and noticed the best.")


if __name__ == "__main__":
    main()
