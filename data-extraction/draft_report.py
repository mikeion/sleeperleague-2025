#!/usr/bin/env python3
"""Build the post-draft report for the current season.

Everything Sleeper's draft recap shows (reach vs ADP, projected Week 1 lineup,
position rankings, bye-week pileups, rookies) plus what it does not:

  * an interval on every projected lineup, from the empirical distribution of
    RotoWire's misses in the archived seasons (see archive_projections.py),
  * a win probability for each Week 1 matchup from those intervals,
  * whether each manager's reaches have historically paid off, using four
    seasons of drafts, ADP, and realized points.

The intervals treat starters as independent. That understates team variance
when a manager stacks a QB with his own receiver; the copula comes later.

Writes html5up-landed/assets/data/draft_report.json.
"""
import collections
import datetime
import json
import random
import statistics
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ARCHIVE = HERE / "output" / "sleeper" / "projections"
POINTS_CACHE = HERE / "output" / "sleeper" / "weekly_stats_cache.json"
OUT = HERE.parent / "html5up-landed" / "assets" / "data" / "draft_report.json"

LEAGUE_ID = "1389689478104231936"
HISTORY = {"2025": ("1257482235834028032", "1257482235834028033"),
           "2024": ("1124841011114168320", "1124841011114168322"),
           "2023": ("998364322315190272", "998364322319384576"),
           "2022": ("859910378069577728", "859910379126509568")}
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
BASE = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
SKILL = {"QB", "RB", "WR", "TE"}
FLEX = [{"RB", "WR", "TE"}, {"RB", "WR"}]
TEAMS = 14
REACH = 12          # picks early enough to count as a reach
WINDOW = 12         # ADP window for "what a pick here usually returns"
SIMS = 10000
MIN_GROUP = 30      # residuals needed before a position/band group stands on its own
CALIBRATION_SEASONS = ["2024", "2025"]
BANDS = [0, 4, 8, 12, 16, 22, 999]

NAMES = {"rpthorp": "Ryan", "robertwneal2": "Robert", "robbbbbbbb": "Robb", "fishy11": "Vince",
         "dakodiacbear": "Dakota", "spaceman917": "Nick", "sambam805": "Sam", "mikeion": "Mike",
         "caseyforeverunclean": "Casey", "gordonulus": "Gordon", "captainbigcup": "Colin",
         "bigdog11": "Daniel", "otterboi": "Josh", "buddygalletti": "Buddy", "elliottkaser": "Elliott"}


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def projections(season, week=None):
    pos = "&".join(f"position[]={p}" for p in POSITIONS)
    wk = f"/{week}" if week else ""
    rows = fetch(f"https://api.sleeper.app/projections/nfl/{season}{wk}?season_type=regular&{pos}")
    return {r["player_id"]: (r.get("stats") or {}) for r in rows}


def bye_weeks(season):
    byes = {}
    for week in range(1, 19):
        rows = fetch(f"https://api.sleeper.app/projections/nfl/{season}/{week}?season_type=regular&position[]=QB")
        teams = {r["team"] for r in rows if r.get("team")}
        playing = {r["team"] for r in rows if r.get("team") and r.get("game_id")}
        for t in teams - playing:
            byes[t] = week
    return byes


# ---------------------------------------------------------------- lineups

def best_lineup(players, points):
    """Greedy fill of QB/RB/RB/WR/WR/TE/FLEX/WRRB_FLEX/K/DEF. Returns list of (pid, slot)."""
    pool = sorted((p for p in players if points.get(p) is not None), key=lambda p: -points[p])
    lineup, used = [], set()
    for pos, n in BASE.items():
        for p in [p for p in pool if p not in used and players[p] == pos][:n]:
            lineup.append((p, pos)); used.add(p)
    for eligible, slot in zip(FLEX, ["FLEX", "WRRB"]):
        rest = [p for p in pool if p not in used and players[p] in eligible]
        if rest:
            lineup.append((rest[0], slot)); used.add(rest[0])
    return lineup


# ---------------------------------------------------------------- residuals

def band(x):
    for i in range(len(BANDS) - 1):
        if BANDS[i] <= x < BANDS[i + 1]:
            return i
    return len(BANDS) - 2


def load_residuals():
    """(position, projection band) -> list of actual - projected, from archived seasons.
    A projected player with no stat line did not play: that is a real outcome, scored 0."""
    res = collections.defaultdict(list)
    for season in CALIBRATION_SEASONS:
        path = ARCHIVE / f"{season}.json"
        if not path.exists():
            print(f"missing {path}; run archive_projections.py first", file=sys.stderr)
            sys.exit(1)
        for r in json.loads(path.read_text())["rows"].values():
            if r["position"] not in BASE or not r.get("proj_pts"):
                continue
            actual = r.get("act_pts") or 0.0
            res[(r["position"], band(r["proj_pts"]))].append(actual - r["proj_pts"])
    return res


def simulate(lineup, positions, proj, residuals, rng):
    totals = []
    draws = []
    for pid, _slot in lineup:
        key = (positions[pid], band(proj[pid]))
        pool = residuals.get(key) or []
        if len(pool) < MIN_GROUP:   # thin band: fall back to the whole position
            pool = [r for (pos, _b), rs in residuals.items() if pos == positions[pid] for r in rs] or [0.0]
        draws.append((proj[pid], pool))
    for _ in range(SIMS):
        totals.append(sum(mu + rng.choice(pool) for mu, pool in draws))
    return totals


def quantile(xs, q):
    xs = sorted(xs)
    return xs[min(int(q * len(xs)), len(xs) - 1)]


# ---------------------------------------------------------------- history

def replacement(points_by_pos):
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


def reach_history(players):
    """Per manager: did the picks they reached for beat what their ADP usually returns?"""
    if not POINTS_CACHE.exists():
        print("no weekly_stats_cache.json; run draft_grades.py once", file=sys.stderr)
        return {}, {}
    pts = json.loads(POINTS_CACHE.read_text())
    picks = []
    for yr, (lid, did) in HISTORY.items():
        bypos = collections.defaultdict(list)
        for pid, ys in pts.items():
            pos = (players.get(pid) or {}).get("position")
            if yr in ys and pos in BASE:
                bypos[pos].append(ys[yr])
        repl = replacement(bypos)
        adp = {pid: s.get("adp_half_ppr") for pid, s in projections(yr).items()}
        users = {u["user_id"]: u["display_name"].lower() for u in fetch(f"https://api.sleeper.app/v1/league/{lid}/users")}
        for p in fetch(f"https://api.sleeper.app/v1/draft/{did}/picks"):
            who = users.get(p.get("picked_by"))
            a = adp.get(p["player_id"])
            pos = (players.get(p["player_id"]) or {}).get("position")
            if not who or not a or a >= 999 or pos not in BASE:
                continue
            picks.append({"yr": yr, "who": who, "no": p["pick_no"], "adp": a,
                          "par": pts.get(p["player_id"], {}).get(yr, 0.0) - repl.get(pos, 0.0)})
    # expectation at an ADP: mean value of every pick whose ADP fell within the window
    for p in picks:
        pool = [q["par"] for q in picks if abs(q["adp"] - p["adp"]) <= WINDOW]
        p["surplus"] = p["par"] - statistics.mean(pool)
        p["reach"] = p["no"] - p["adp"] <= -REACH
    per = collections.defaultdict(lambda: {"reaches": [], "others": []})
    for p in picks:
        per[p["who"]]["reaches" if p["reach"] else "others"].append(p["surplus"])
    out = {}
    for who, d in per.items():
        out[who] = {"n_reaches": len(d["reaches"]),
                    "reach_surplus": round(statistics.mean(d["reaches"]), 1) if d["reaches"] else None,
                    "n_others": len(d["others"]),
                    "other_surplus": round(statistics.mean(d["others"]), 1) if d["others"] else None}
    league = {"n_reaches": sum(1 for p in picks if p["reach"]),
              "reach_surplus": round(statistics.mean([p["surplus"] for p in picks if p["reach"]]), 1),
              "other_surplus": round(statistics.mean([p["surplus"] for p in picks if not p["reach"]]), 1),
              "seasons": sorted(HISTORY)}
    return out, league


# ---------------------------------------------------------------- main

def main():
    rng = random.Random(2026)
    state = fetch("https://api.sleeper.app/v1/state/nfl")
    season, week = state["season"], max(int(state["week"]), 1)
    league = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}")
    users = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/users")
    rosters = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters")
    picks = fetch(f"https://api.sleeper.app/v1/draft/{league['draft_id']}/picks")
    matchups = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{week}")
    players = fetch("https://api.sleeper.app/v1/players/nfl")
    season_proj = projections(season)
    week_proj = projections(season, week)
    byes = bye_weeks(season)
    residuals = load_residuals()

    def pinfo(pid):
        p = players.get(pid) or {}
        pos = p.get("position") or pid
        return {"id": pid, "name": p.get("full_name") or pid, "pos": pos,
                "team": p.get("team"), "age": p.get("age"), "exp": p.get("years_exp"),
                "bye": byes.get(p.get("team") or pid),
                "img": (f"https://sleepercdn.com/images/team_logos/nfl/{pid.lower()}.png" if pos == "DEF"
                        else f"https://sleepercdn.com/content/nfl/players/thumb/{pid}.jpg")}

    # Every player's rank by projected points above replacement at his position.
    # ADP is the market before the news; this is what the market knows now.
    proj_by_pos = collections.defaultdict(list)
    for pid, st in season_proj.items():
        pos = (players.get(pid) or {}).get("position")
        if pos in BASE and st.get("pts_half_ppr"):
            proj_by_pos[pos].append(st["pts_half_ppr"])
    repl_now = replacement(proj_by_pos)
    par_now = {pid: st["pts_half_ppr"] - repl_now[(players.get(pid) or {}).get("position")]
               for pid, st in season_proj.items()
               if (players.get(pid) or {}).get("position") in BASE and st.get("pts_half_ppr")}
    ranked = sorted(par_now, key=lambda x: -par_now[x])
    value_rank = {pid: i for i, pid in enumerate(ranked, 1)}
    # what a pick at slot n usually buys: PAR of the players ranked near n, with the
    # window clipped symmetrically so the top picks are not compared to a thinner tail
    def expected(n):
        w = min(WINDOW, n - 1)
        return statistics.mean(par_now[pid] for pid in ranked[n - 1 - w:n + w])
    expected_par = {n: max(expected(n), 0.0) for n in range(1, TEAMS * 20)}

    managers = {}
    for u in users:
        uname = u["display_name"].lower()
        roster = next(r for r in rosters if r["owner_id"] == u["user_id"])
        managers[u["user_id"]] = {
            "username": uname, "name": NAMES.get(uname, u["display_name"]),
            "handle": u["display_name"], "team": (u.get("metadata") or {}).get("team_name") or u["display_name"],
            "avatar": f"https://sleepercdn.com/avatars/thumbs/{u['avatar']}" if u.get("avatar") else None,
            "roster_id": roster["roster_id"], "players": roster.get("players") or [], "picks": []}

    # --- draft picks vs ADP
    for p in picks:
        m = managers.get(p["picked_by"])
        if not m:
            continue
        adp = (season_proj.get(p["player_id"]) or {}).get("adp_half_ppr")
        info = pinfo(p["player_id"])
        info.update({"pick": p["pick_no"], "round": p["round"], "slot": p["draft_slot"],
                     "adp": adp if adp and adp < 999 else None,
                     "diff": round(p["pick_no"] - adp, 1) if adp and adp < 999 else None,
                     "season_proj": round((season_proj.get(p["player_id"]) or {}).get("pts_half_ppr") or 0, 1),
                     "value_rank": value_rank.get(p["player_id"]),
                     # below replacement is worth zero, not negative: the cost of a bad pick is
                     # bounded by what the slot would have bought
                     "value_pts": round(max(par_now[p["player_id"]], 0.0) - expected_par[p["pick_no"]], 1)
                                  if p["player_id"] in par_now else None})
        m["picks"].append(info)
        m["slot"] = p["draft_slot"]

    for m in managers.values():
        diffs = [p["diff"] for p in m["picks"] if p["diff"] is not None]
        m["reach"] = {"avg_abs": round(statistics.mean(abs(d) for d in diffs), 1),
                      "median_abs": round(statistics.median(abs(d) for d in diffs), 1),
                      "avg": round(statistics.mean(diffs), 1),
                      "biggest_reach": min((p for p in m["picks"] if p["diff"] is not None), key=lambda p: p["diff"]),
                      "biggest_steal": max((p for p in m["picks"] if p["diff"] is not None), key=lambda p: p["diff"])}
        # kickers and defenses are excluded: their projections are noise and everyone takes them last
        valued = [p for p in m["picks"] if p["value_pts"] is not None and p["pos"] in SKILL]
        m["value"] = {"best": max(valued, key=lambda p: p["value_pts"]),
                      "worst": min(valued, key=lambda p: p["value_pts"])}
        by_pos = collections.defaultdict(float)
        for p in m["picks"]:
            by_pos[p["pos"]] += p["season_proj"]
        m["position_pts"] = {pos: round(by_pos[pos], 1) for pos in POSITIONS}
        m["rookies"] = sum(1 for pid in m["players"] if (players.get(pid) or {}).get("years_exp") == 0)

    for pos in POSITIONS:
        order = sorted(managers.values(), key=lambda m: -m["position_pts"][pos])
        for rank, m in enumerate(order, 1):
            m.setdefault("position_rank", {})[pos] = rank
    for m in managers.values():
        m["positions_led"] = sum(1 for r in m["position_rank"].values() if r == 1)

    # --- projected lineups with intervals
    for m in managers.values():
        pos_of = {pid: (players.get(pid) or {}).get("position") for pid in m["players"]}
        wk_pts = {pid: (week_proj.get(pid) or {}).get("pts_half_ppr") for pid in m["players"]}
        lineup = best_lineup({pid: pos for pid, pos in pos_of.items() if pos in BASE}, wk_pts)
        sims = simulate(lineup, pos_of, wk_pts, residuals, rng)
        m["week_lineup"] = [dict(pinfo(pid), slot=slot, proj=round(wk_pts[pid], 2)) for pid, slot in lineup]
        m["week_proj"] = round(sum(wk_pts[pid] for pid, _ in lineup), 2)
        m["week_p10"] = round(quantile(sims, 0.10), 1)
        m["week_p50"] = round(quantile(sims, 0.50), 1)
        m["week_p90"] = round(quantile(sims, 0.90), 1)
        m["_sims"] = sims
        # season starters by projection, for bye pileups and age
        s_pts = {pid: (season_proj.get(pid) or {}).get("pts_half_ppr") for pid in m["players"]}
        starters = best_lineup({pid: pos for pid, pos in pos_of.items() if pos in BASE}, s_pts)
        bye_count = collections.Counter(byes.get((players.get(pid) or {}).get("team") or pid) for pid, _ in starters)
        bye_count.pop(None, None)
        worst = max(bye_count.items(), key=lambda kv: kv[1]) if bye_count else (None, 0)
        m["bye_bomb"] = {"week": worst[0], "starters": worst[1]}
        ages = [players[pid]["age"] for pid, _ in starters if (players.get(pid) or {}).get("age")]
        m["starter_age"] = round(statistics.mean(ages), 1) if ages else None

    # --- matchup win probabilities
    by_roster = {m["roster_id"]: m for m in managers.values()}
    games = collections.defaultdict(list)
    for mu in matchups:
        games[mu["matchup_id"]].append(by_roster[mu["roster_id"]])
    matchup_out = []
    for mid, pair in sorted(games.items()):
        if len(pair) != 2:
            continue
        a, b = pair
        wins = sum(1 for x, y in zip(a["_sims"], b["_sims"]) if x > y)
        p = wins / SIMS
        matchup_out.append({"a": a["username"], "b": b["username"], "p_a": round(p, 3), "p_b": round(1 - p, 3),
                            "margin_p10": round(quantile([x - y for x, y in zip(a["_sims"], b["_sims"])], 0.10), 1),
                            "margin_p90": round(quantile([x - y for x, y in zip(a["_sims"], b["_sims"])], 0.90), 1)})
        a["opponent"], b["opponent"] = b["username"], a["username"]
        a["win_prob"], b["win_prob"] = round(p, 3), round(1 - p, 3)

    history, league_history = reach_history(players)
    for m in managers.values():
        m["history"] = history.get(m["username"])

    # --- report cards
    ms = list(managers.values())
    def card(title, m, value, blurb):
        return {"title": title, "manager": m["username"] if m else None, "value": value, "blurb": blurb}
    best = max(ms, key=lambda m: m["week_p50"])
    spread = lambda m: m["week_p90"] - m["week_p10"]
    boom = max(ms, key=spread)
    steady = min(ms, key=spread)
    steal = max(ms, key=lambda m: m["value"]["best"]["value_pts"])
    reach = min(ms, key=lambda m: m["value"]["worst"]["value_pts"])
    coward = min(ms, key=lambda m: m["reach"]["avg_abs"])
    blazer = max(ms, key=lambda m: m["reach"]["avg_abs"])
    bomb = max(ms, key=lambda m: m["bye_bomb"]["starters"])
    rookies = max(ms, key=lambda m: m["rookies"])
    oldest = max((m for m in ms if m["starter_age"]), key=lambda m: m["starter_age"])
    king = max(ms, key=lambda m: m["positions_led"])
    sp, rp = steal["value"]["best"], reach["value"]["worst"]
    tight = min(matchup_out, key=lambda g: abs(g["p_a"] - 0.5))
    cards = [
        card("Best on paper", best, f"{best['week_p50']:.1f} pts",
             f"Highest projected Week {week} lineup. 80% interval {best['week_p10']:.0f} to {best['week_p90']:.0f}."),
        card("Boom or bust", boom, f"{boom['week_p10']:.0f} to {boom['week_p90']:.0f}",
             f"Widest 80% interval in Week {week}. The lineup you want when you are the underdog."),
        card("Steady Eddie", steady, f"{steady['week_p10']:.0f} to {steady['week_p90']:.0f}",
             f"Narrowest 80% interval in Week {week}. The lineup you want when you are the favorite."),
        card("Steal of the draft", steal, f"{sp['value_pts']:+.0f} pts",
             f"{sp['name']} at {sp['pick']}, now projected the {ordinal(sp['value_rank'])} most valuable player"
             + (f" (ADP {sp['adp']:.0f})." if sp['adp'] else ".")
             + " Points above what that pick usually buys."),
        card("Biggest reach", reach, f"{rp['value_pts']:+.0f} pts",
             f"{rp['name']} at {rp['pick']}, now projected {ordinal(rp['value_rank'])} in value"
             + (f" (ADP {rp['adp']:.0f})." if rp['adp'] else ".")
             + " Projections, not ADP, so suspensions and injuries count."),
        card("Certified coward", coward, f"{coward['reach']['avg_abs']:.1f} picks off",
             "Never strayed from ADP. The board drafted for them."),
        card("Trailblazer", blazer, f"{blazer['reach']['avg_abs']:.1f} picks off",
             "Furthest from ADP on average. Either knows something or doesn't."),
        card("Bye week bomb", bomb, f"{bomb['bye_bomb']['starters']} in W{bomb['bye_bomb']['week']}",
             "Most projected starters sitting out the same week."),
        card("Rookie fever", rookies, f"{rookies['rookies']} rookies", "Most first-year players on one roster."),
        card("Veteran presence", oldest, f"{oldest['starter_age']:.1f} yrs", "Oldest projected starting lineup."),
        card("Position king", king, f"{king['positions_led']} of 6", "Positions they lead the league in, by projected season points."),
        card("Coin flip of the week", None, f"{max(tight['p_a'], tight['p_b']):.0%} vs {min(tight['p_a'], tight['p_b']):.0%}",
             f"{managers_by(ms, tight['a'])['name']} vs {managers_by(ms, tight['b'])['name']}. Nobody should be confident."),
    ]

    for m in ms:
        del m["_sims"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generated": datetime.datetime.now().isoformat(timespec="minutes"),
        "season": season, "week": week, "league": league["name"],
        "method": {"sims": SIMS, "calibration_seasons": CALIBRATION_SEASONS,
                   "residual_counts": {f"{k[0]}:{BANDS[k[1]]}-{BANDS[k[1] + 1]}": len(v) for k, v in sorted(residuals.items())},
                   "note": "Starters simulated independently from empirical projection residuals by position and projection band."},
        "reach_threshold": REACH, "history_league": league_history,
        "managers": sorted(ms, key=lambda m: m["slot"]), "matchups": matchup_out, "cards": cards,
    }, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)", file=sys.stderr)


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def managers_by(ms, username):
    return next(m for m in ms if m["username"] == username)


if __name__ == "__main__":
    main()
