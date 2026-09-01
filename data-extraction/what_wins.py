"""What actually predicts wins in THIS league?

Builds one row per manager-season (n~55) with the things a manager controls —
draft value, lineup efficiency, waiver volume, waiver production, FAAB spent —
and correlates each against that season's win total. The point is to test the
common advice ("win the waiver wire") against this league's own record rather
than assume it.
"""
import collections, json, math, statistics, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
LEAGUES = {"2025": "1257482235834028032", "2024": "1124841011114168320",
           "2023": "998364322315190272", "2022": "859910378069577728"}
DRAFTS = {"2025": "1257482235834028033", "2024": "1124841011114168322",
          "2023": "998364322319384576", "2022": "859910379126509568"}
FLEX_OK = {"FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
           "REC_FLEX": {"WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"}}
CACHE = OUT / "sleeper" / "season_skill_cache.json"


def J(u):
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.load(r)


def pearson(xs, ys):
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return num / den if den else 0.0


def spearman(xs, ys):
    rank = lambda v: [sorted(v).index(x) + 1 for x in v]
    return pearson(rank(xs), rank(ys))


def main():
    data = json.loads(CACHE.read_text())
    players = J("https://api.sleeper.app/v1/players/nfl")
    pos_of = lambda pid: (players.get(pid) or {}).get("position")
    grades = json.loads((OUT / "draft_grades.json").read_text())["grid"]

    def optimal(slots, pts):
        used, tot = set(), 0.0
        for slot in [s for s in slots if s not in FLEX_OK]:
            b = max(((v, p) for p, v in pts.items() if p not in used and pos_of(p) == slot), default=None)
            if b: used.add(b[1]); tot += b[0]
        for slot in [s for s in slots if s in FLEX_OK]:
            ok = FLEX_OK[slot]
            b = max(((v, p) for p, v in pts.items() if p not in used and pos_of(p) in ok), default=None)
            if b: used.add(b[1]); tot += b[0]
        return tot

    rows = []
    for yr, d in data.items():
        slots = [s for s in d["roster_positions"] if s != "BN"]
        drafted = {w: set(v) for w, v in d["drafted"].items()}
        acc = collections.defaultdict(lambda: collections.defaultdict(float))
        for wk, ms in d["weeks"].items():
            for m in ms:
                who = d["rid2who"].get(str(m["roster_id"])) or d["rid2who"].get(m["roster_id"])
                if not who: continue
                pp = m.get("players_points") or {}
                st = m.get("starters") or []
                acc[who]["act"] += sum(pp.get(p, 0) for p in st)
                acc[who]["opt"] += optimal(slots, pp)
                acc[who]["wire"] += sum(pp.get(p, 0) for p in st if p not in drafted.get(who, set()))
        for t in d["tx"]:
            if t.get("status") != "complete" or t.get("type") not in ("waiver", "free_agent") or not t.get("adds"):
                continue
            for rid in t.get("roster_ids", []):
                who = d["rid2who"].get(str(rid)) or d["rid2who"].get(rid)
                if who: acc[who]["adds"] += 1
            bid = (t.get("settings") or {}).get("waiver_bid")
            if bid:
                who = d["rid2who"].get(str(t["roster_ids"][0])) or d["rid2who"].get(t["roster_ids"][0])
                if who: acc[who]["faab"] += bid
        for r in J(f"https://api.sleeper.app/v1/league/{LEAGUES[yr]}/rosters"):
            who = d["rid2who"].get(str(r["roster_id"])) or d["rid2who"].get(r["roster_id"])
            a = acc.get(who)
            if not a or not a["opt"]: continue
            rows.append({"yr": yr, "who": who, "wins": r["settings"]["wins"],
                         "draft": grades.get(who, {}).get(yr, 0.0),
                         "lineup": a["act"] / a["opt"] * 100,
                         "wire": a["wire"], "adds": a["adds"], "faab": a["faab"],
                         "ppd": a["wire"] / a["faab"] if a["faab"] else 0})

    print("=" * 80)
    print(f"  WHAT CORRELATES WITH WINS IN THIS LEAGUE   (n = {len(rows)} manager-seasons)")
    print("=" * 80)
    wins = [r["wins"] for r in rows]
    metrics = [("Waiver points in lineup", "wire"), ("Draft score", "draft"),
               ("Lineup efficiency %", "lineup"), ("Waiver adds", "adds"),
               ("FAAB spent", "faab"), ("Waiver pts per $", "ppd")]
    print(f"  {'Metric':28}{'Pearson r':>11}{'Spearman':>10}   {'strength'}")
    out = []
    for label, k in metrics:
        xs = [r[k] for r in rows]
        out.append((abs(pearson(xs, wins)), label, pearson(xs, wins), spearman(xs, wins)))
    for _a, label, r, rho in sorted(out, reverse=True):
        bar = "#" * int(abs(r) * 40)
        print(f"  {label:28}{r:>+11.3f}{rho:>+10.3f}   {bar}")

    print()
    print("  Top-3 seasons by waiver points, and how they finished:")
    for r in sorted(rows, key=lambda x: -x["wire"])[:6]:
        print(f"    {r['yr']}  {r['who']:20} wire {r['wire']:>6.0f}  adds {r['adds']:>3}  -> {r['wins']:>2} wins")
    print("  Bottom-3 seasons by waiver points:")
    for r in sorted(rows, key=lambda x: x["wire"])[:6]:
        print(f"    {r['yr']}  {r['who']:20} wire {r['wire']:>6.0f}  adds {r['adds']:>3}  -> {r['wins']:>2} wins")
    (OUT / "what_wins.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
