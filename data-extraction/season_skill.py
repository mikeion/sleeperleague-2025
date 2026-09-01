"""Decompose each manager's season into the three things they actually control.

  DRAFT    value of the players they drafted (see draft_grades.py)
  WAIVERS  starter points from players they did NOT draft — the wire and trades
  LINEUP   actual points / optimal points, i.e. did they start the right guys

Same league, same weeks (1-14). Everything is measured off the real starters and
the real bench each week, so "optimal" means the best legal lineup that manager
could have set from the roster he actually had that Sunday.
"""
import collections, json, statistics, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
CACHE = OUT / "sleeper" / "season_skill_cache.json"
LEAGUES = {"2025": "1257482235834028032", "2024": "1124841011114168320",
           "2023": "998364322315190272", "2022": "859910378069577728"}
DRAFTS = {"2025": "1257482235834028033", "2024": "1124841011114168322",
          "2023": "998364322319384576", "2022": "859910379126509568"}
FLEX_OK = {"FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
           "REC_FLEX": {"WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"}}


def J(u):
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.load(r)


def gather():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    out = {}
    for yr, lid in LEAGUES.items():
        lg = J(f"https://api.sleeper.app/v1/league/{lid}")
        users = {u["user_id"]: u["display_name"] for u in J(f"https://api.sleeper.app/v1/league/{lid}/users")}
        rosters = J(f"https://api.sleeper.app/v1/league/{lid}/rosters")
        rid2who = {r["roster_id"]: users.get(r["owner_id"], str(r["owner_id"])) for r in rosters}
        drafted = collections.defaultdict(list)
        for p in J(f"https://api.sleeper.app/v1/draft/{DRAFTS[yr]}/picks"):
            w = users.get(p.get("picked_by"))
            if w:
                drafted[w].append(p["player_id"])
        weeks = {}
        for wk in range(1, 15):
            try:
                weeks[str(wk)] = J(f"https://api.sleeper.app/v1/league/{lid}/matchups/{wk}")
            except Exception:
                pass
        tx = []
        for wk in range(1, 18):
            try:
                tx += J(f"https://api.sleeper.app/v1/league/{lid}/transactions/{wk}")
            except Exception:
                pass
        out[yr] = {"roster_positions": lg["roster_positions"], "rid2who": rid2who,
                   "drafted": drafted, "weeks": weeks, "tx": tx}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out))
    return out


def optimal(slots, pts, pos_of):
    used, total = set(), 0.0
    fixed = [s for s in slots if s not in FLEX_OK and s != "BN"]
    flex = [s for s in slots if s in FLEX_OK]
    for slot in fixed:
        best = max(((v, p) for p, v in pts.items() if p not in used and pos_of(p) == slot),
                   default=None)
        if best:
            used.add(best[1]); total += best[0]
    for slot in flex:
        ok = FLEX_OK[slot]
        best = max(((v, p) for p, v in pts.items() if p not in used and pos_of(p) in ok),
                   default=None)
        if best:
            used.add(best[1]); total += best[0]
    return total


def main():
    data = gather()
    players = J("https://api.sleeper.app/v1/players/nfl")
    pos_of = lambda pid: (players.get(pid) or {}).get("position")

    agg = collections.defaultdict(lambda: collections.defaultdict(float))
    seasons = collections.defaultdict(set)
    for yr, d in data.items():
        slots = [s for s in d["roster_positions"] if s != "BN"]
        drafted = {w: set(v) for w, v in d["drafted"].items()}
        for wk, ms in d["weeks"].items():
            for m in ms:
                who = d["rid2who"].get(str(m["roster_id"])) or d["rid2who"].get(m["roster_id"])
                if not who:
                    continue
                pp = m.get("players_points") or {}
                starters = m.get("starters") or []
                act = sum(pp.get(p, 0) for p in starters)
                opt = optimal(slots, pp, pos_of)
                mine = drafted.get(who, set())
                agg[who]["actual"] += act
                agg[who]["optimal"] += opt
                agg[who]["from_draft"] += sum(pp.get(p, 0) for p in starters if p in mine)
                agg[who]["from_wire"] += sum(pp.get(p, 0) for p in starters if p not in mine)
                agg[who]["weeks"] += 1
                seasons[who].add(yr)
        for t in d["tx"]:
            if t.get("status") != "complete" or t.get("type") not in ("waiver", "free_agent"):
                continue
            if not t.get("adds"):
                continue
            for rid in t.get("roster_ids", []):
                who = d["rid2who"].get(str(rid)) or d["rid2who"].get(rid)
                if who:
                    agg[who]["adds"] += 1
            bid = (t.get("settings") or {}).get("waiver_bid")
            if bid:
                who = d["rid2who"].get(str(t["roster_ids"][0])) or d["rid2who"].get(t["roster_ids"][0])
                if who:
                    agg[who]["faab"] += bid

    print("=" * 92)
    print("  SEASON SKILL, 2022-25 — where each manager's starting points came from")
    print("=" * 92)
    print(f"  {'Manager':20}{'Lineup%':>9}{'Left/wk':>9}{'%fromWire':>11}{'WirePts/yr':>12}{'Adds/yr':>9}{'Pts/$':>8}")
    rows = []
    for who, a in agg.items():
        n = len(seasons[who])
        if not a["optimal"] or n == 0:
            continue
        rows.append((a["from_wire"] / max(a["actual"], 1), who, a, n))
    rows.sort(reverse=True)
    for share, who, a, n in rows:
        eff = a["actual"] / a["optimal"] * 100
        left = (a["optimal"] - a["actual"]) / max(a["weeks"], 1)
        print(f"  {who:20}{eff:>8.1f}%{left:>9.1f}{share * 100:>10.1f}%"
              f"{a['from_wire'] / n:>12.0f}{a['adds'] / n:>9.0f}"
              f"{(a['from_wire'] / a['faab']) if a['faab'] else 0:>8.1f}")
    (OUT / "season_skill.json").write_text(json.dumps({k: dict(v) for k, v in agg.items()}, indent=1))
    print(f"\nwrote {OUT / 'season_skill.json'}")


if __name__ == "__main__":
    main()
