"""Grade every manager's draft, every year.

Two corrections make this a fair measure of drafting rather than of luck at the
top of the board:

  1. Raw points are position-blind, and a QB outscores an RB by ~130 points a year
     for doing nothing special. So every player is first converted to points above
     replacement at his own position (14 teams, QB/RB/RB/WR/WR/TE/FLEX/WRRB_FLEX
     /K/DEF), computed separately for each season.
  2. Picking 1st should beat picking 14th, so each pick is then scored against what
     a typical pick at that slot returned — the mean value of every pick within a
     +/-12 window of that pick number, pooled across 2022-25.

A manager's draft score is the sum of those surpluses: value above what his draft
slot owed him. Without correction 1, every "best pick ever" comes back a QB.

Scoring window is weeks 1-14, the fantasy regular season. Weeks 15-18 are
excluded: they decide nothing for a team that already missed the playoffs.
"""
import collections, json, statistics, sys, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
CACHE = OUT / "sleeper" / "weekly_stats_cache.json"
DRAFTS = {"2025": "1257482235834028033", "2024": "1124841011114168322",
          "2023": "998364322319384576", "2022": "859910379126509568"}
LEAGUES = {"2025": "1257482235834028032", "2024": "1124841011114168320",
           "2023": "998364322315190272", "2022": "859910378069577728"}
WINDOW = 12
BASE = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
FLEX = [{"RB", "WR", "TE"}, {"RB", "WR"}]
TEAMS = 14


def J(u):
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.load(r)


def season_points():
    """player_id -> {year: points} over weeks 1-14."""
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    pts = collections.defaultdict(dict)
    for yr in DRAFTS:
        for wk in range(1, 15):
            try:
                wkstats = J(f"https://api.sleeper.app/v1/stats/nfl/regular/{yr}/{wk}")
            except Exception:
                continue
            for pid, s in wkstats.items():
                v = (s or {}).get("pts_half_ppr")
                if v:
                    pts[pid][yr] = pts[pid].get(yr, 0) + v
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(pts))
    return pts


def replacement(points_by_pos):
    """Greedy fill of every starting slot in the league -> replacement value per position."""
    pools = {p: sorted(v, reverse=True) for p, v in points_by_pos.items()}
    used = {p: min(BASE.get(p, 0) * TEAMS, len(pools[p])) for p in pools}
    for eligible in FLEX:
        for _ in range(TEAMS):
            best, bp = None, None
            for p in eligible:
                if p in pools and used[p] < len(pools[p]):
                    c = pools[p][used[p]]
                    if best is None or c > best:
                        best, bp = c, p
            if bp:
                used[bp] += 1
    return {p: (pools[p][min(used[p], len(pools[p]) - 1)] if pools[p] else 0.0) for p in pools}


def main():
    pts = season_points()
    players = J("https://api.sleeper.app/v1/players/nfl")

    # replacement level per position, per season
    repl = {}
    for yr in DRAFTS:
        bypos = collections.defaultdict(list)
        for pid, ys in pts.items():
            if yr not in ys:
                continue
            pos = (players.get(pid) or {}).get("position")
            if pos in BASE:
                bypos[pos].append(ys[yr])
        repl[yr] = replacement(bypos)
    picks = []
    for yr, did in DRAFTS.items():
        users = {u["user_id"]: u["display_name"] for u in J(f"https://api.sleeper.app/v1/league/{LEAGUES[yr]}/users")}
        for p in J(f"https://api.sleeper.app/v1/draft/{did}/picks"):
            who = users.get(p.get("picked_by"))
            if not who:
                continue
            picks.append({"yr": yr, "who": who, "no": p["pick_no"], "rd": p["round"],
                          "pid": p["player_id"],
                          "name": (players.get(p["player_id"]) or {}).get("full_name") or p["player_id"],
                          "pos": (players.get(p["player_id"]) or {}).get("position"),
                          "pts": pts.get(p["player_id"], {}).get(yr, 0.0)})
            pos = picks[-1]["pos"]
            picks[-1]["par"] = picks[-1]["pts"] - repl[yr].get(pos, 0.0)

    # expected return at each pick number, pooled across years
    by_no = collections.defaultdict(list)
    for p in picks:
        by_no[p["no"]].append(p["par"])
    nos = sorted(by_no)
    expected = {}
    for n in nos:
        pool = [v for m in nos if abs(m - n) <= WINDOW for v in by_no[m]]
        expected[n] = statistics.mean(pool) if pool else 0.0
    for p in picks:
        p["exp"] = expected[p["no"]]
        p["val"] = p["par"] - p["exp"]

    grid = collections.defaultdict(dict)
    for p in picks:
        grid[p["who"]][p["yr"]] = grid[p["who"]].get(p["yr"], 0.0) + p["val"]

    years = sorted(DRAFTS)
    print("=" * 78)
    print("  DRAFT SCORE — value above replacement, above what your slot owed you")
    print("=" * 78)
    print(f"  {'Manager':20}" + "".join(f"{y:>9}" for y in years) + f"{'TOTAL':>10}{'yrs':>5}")
    rows = []
    for who, ys in grid.items():
        tot = sum(ys.values())
        rows.append((tot / max(len(ys), 1), tot, who, ys))
    rows.sort(reverse=True)
    for _avg, tot, who, ys in rows:
        line = f"  {who:20}"
        for y in years:
            line += f"{ys[y]:>+9.0f}" if y in ys else f"{'—':>9}"
        print(line + f"{tot:>+10.0f}{len(ys):>5}")

    print()
    print("=" * 78)
    print("  BEST PICKS EVER (value above slot)")
    print("=" * 78)
    for p in sorted(picks, key=lambda x: -x["val"])[:12]:
        print(f"  {p['yr']}  R{p['rd']:<2} pk{p['no']:>3}  {p['name'][:22]:23}{p['pos'] or '':4}"
              f"{p['pts']:>6.0f}pts {p['par']:>+6.0f}par {p['val']:>+7.0f}   {p['who']}")
    print()
    print("=" * 78)
    print("  WORST PICKS EVER")
    print("=" * 78)
    for p in sorted(picks, key=lambda x: x["val"])[:12]:
        print(f"  {p['yr']}  R{p['rd']:<2} pk{p['no']:>3}  {p['name'][:22]:23}{p['pos'] or '':4}"
              f"{p['pts']:>6.0f}pts {p['par']:>+6.0f}par {p['val']:>+7.0f}   {p['who']}")

    print()
    print("  replacement level by season:", {y: {k: round(v) for k, v in r.items()} for y, r in repl.items()}["2025"], "(2025)")

    (OUT / "draft_grades.json").write_text(json.dumps(
        {"grid": grid, "picks": picks, "expected": expected}, indent=1))
    print(f"\nwrote {OUT / 'draft_grades.json'}")


if __name__ == "__main__":
    main()
