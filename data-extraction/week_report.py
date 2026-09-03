#!/usr/bin/env python3
"""Snapshot this week's matchups with projections, intervals, and win probabilities.

Run Thursday morning, before the first game. Writes two files:

  html5up-landed/assets/data/week_report.json              the latest week
  html5up-landed/assets/data/weeks/{season}_w{week}.json   kept forever

The dashboard reads the latest file for the current week and the per-week
files to score past predictions against what happened. The snapshot is the
prediction of record: once the week is played it is not rewritten.

Uses the starters each manager has actually set. A slot left empty or filled
with a player on bye projects to zero, which is the honest number.
"""
import datetime
import json
import random
import sys
from pathlib import Path

from draft_report import (BASE, LEAGUE_ID, NAMES, SIMS, CALIBRATION_SEASONS, best_lineup, fetch,
                          load_residuals, projections, quantile, simulate)

HERE = Path(__file__).parent
DATA = HERE.parent / "html5up-landed" / "assets" / "data"


def main():
    rng = random.Random(2026)
    state = fetch("https://api.sleeper.app/v1/state/nfl")
    season, week = state["season"], max(int(state["week"]), 1)
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        week = int(sys.argv[1])
    league = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}")
    users = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/users")
    rosters = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters")
    matchups = fetch(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{week}")
    players = fetch("https://api.sleeper.app/v1/players/nfl")
    week_proj = projections(season, week)
    residuals = load_residuals()

    def pinfo(pid):
        p = players.get(pid) or {}
        st = week_proj.get(pid) or {}
        pos = p.get("position") or pid
        return {"id": pid, "name": p.get("full_name") or pid, "pos": pos, "team": p.get("team"),
                "proj": round(st.get("pts_half_ppr") or 0.0, 2), "injury": p.get("injury_status")}

    by_roster = {r["roster_id"]: r for r in rosters}
    by_owner = {u["user_id"]: u for u in users}
    managers = {}
    for mu in matchups:
        roster = by_roster[mu["roster_id"]]
        u = by_owner.get(roster["owner_id"]) or {}
        uname = (u.get("display_name") or "unknown").lower()
        pos_of = {pid: (players.get(pid) or {}).get("position") for pid in roster.get("players") or []}
        wk_pts = {pid: (week_proj.get(pid) or {}).get("pts_half_ppr") or 0.0 for pid in pos_of}
        starters = [s for s in (mu.get("starters") or []) if s and s != "0"]
        source = "set"
        if not starters:
            starters = [pid for pid, _ in best_lineup({p: q for p, q in pos_of.items() if q in BASE}, wk_pts)]
            source = "optimal"
        lineup = [(pid, pos_of.get(pid) or "?") for pid in starters]
        sims = simulate(lineup, {**pos_of, **{pid: "WR" for pid in starters if pid not in pos_of}},
                        {**wk_pts, **{pid: 0.0 for pid in starters if pid not in wk_pts}}, residuals, rng)
        s = roster.get("settings") or {}
        managers[mu["roster_id"]] = {
            "username": uname, "name": NAMES.get(uname, u.get("display_name") or "Unknown"),
            "handle": u.get("display_name"), "team": (u.get("metadata") or {}).get("team_name") or u.get("display_name"),
            "avatar": f"https://sleepercdn.com/avatars/thumbs/{u['avatar']}" if u.get("avatar") else None,
            "roster_id": mu["roster_id"], "matchup_id": mu["matchup_id"],
            "wins": s.get("wins", 0), "losses": s.get("losses", 0), "ties": s.get("ties", 0),
            "starters_source": source,
            "starters": [dict(pinfo(pid), slot=slot) for (pid, _), slot in zip(lineup, league["roster_positions"])],
            "bench": [pinfo(pid) for pid in pos_of if pid not in starters],
            "proj_sum": round(sum(wk_pts.get(pid, 0.0) for pid in starters), 2),
            "p10": round(quantile(sims, 0.10), 1), "p50": round(quantile(sims, 0.50), 1),
            "p90": round(quantile(sims, 0.90), 1), "_sims": sims}

    games = {}
    for m in managers.values():
        games.setdefault(m["matchup_id"], []).append(m)
    out_games = []
    for mid, pair in sorted(games.items()):
        if len(pair) != 2:
            continue
        a, b = pair
        diffs = [x - y for x, y in zip(a["_sims"], b["_sims"])]
        p = sum(1 for d in diffs if d > 0) / SIMS
        a["opponent"], b["opponent"] = b["username"], a["username"]
        a["win_prob"], b["win_prob"] = round(p, 3), round(1 - p, 3)
        out_games.append({"matchup_id": mid, "a": a["username"], "b": b["username"],
                          "p_a": round(p, 3), "p_b": round(1 - p, 3),
                          "margin_p10": round(quantile(diffs, 0.10), 1), "margin_p90": round(quantile(diffs, 0.90), 1)})
    for m in managers.values():
        del m["_sims"]

    report = {"generated": datetime.datetime.now().isoformat(timespec="minutes"),
              "season": season, "week": week, "league": league["name"], "sims": SIMS,
              "calibration_seasons": CALIBRATION_SEASONS,
              "managers": sorted(managers.values(), key=lambda m: -m["p50"]), "matchups": out_games}
    (DATA / "weeks").mkdir(parents=True, exist_ok=True)
    locked = DATA / "weeks" / f"{season}_w{week:02d}.json"
    if locked.exists() and "--force" not in sys.argv:
        # The first snapshot is the prediction of record. Rerunning after kickoff
        # would quietly replace it with numbers that already know the scores.
        print(f"week {week} is already locked at {locked}; pass --force to overwrite", file=sys.stderr)
        return
    text = json.dumps(report, separators=(",", ":"))
    (DATA / "week_report.json").write_text(text)
    (DATA / "weeks" / f"{season}_w{week:02d}.json").write_text(text)
    print(f"week {week}: {len(out_games)} matchups, {len(managers)} teams -> {DATA / 'week_report.json'}", file=sys.stderr)


if __name__ == "__main__":
    main()
