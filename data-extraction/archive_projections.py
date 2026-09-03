#!/usr/bin/env python3
"""Archive Sleeper's weekly projections next to what actually happened.

Sleeper serves a RotoWire projection and a Sportradar stat line for every
player-week back to 2018. Nobody else keeps these for free, and they are the
training data for everything with an interval on it: how wide the miss is by
position, how skewed, how often a projected 12 turns into a 0.

One slim record per player-week goes to output/sleeper/projections/{season}.json:
projection, actual, and the components that drive the miss. Past seasons are
fetched once and left alone. The current season is re-pulled every run, so run
this Thursday morning and again Tuesday to get the pre-game projection and the
final stat line for each week.

Caveat: records for past weeks carry a last-modified stamp after kickoff, so the
historical projections may not be the exact pre-game numbers. The current-season
Thursday snapshots are the only ones we can vouch for.
"""
import datetime
import json
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output" / "sleeper" / "projections"
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
FIRST_SEASON = 2018
COMPONENTS = ["pass_att", "pass_yd", "pass_td", "pass_int", "rush_att", "rush_yd",
              "rush_td", "rec_tgt", "rec", "rec_yd", "rec_td", "fum_lost", "off_snp"]


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def week_rows(kind, season, week):
    pos = "&".join(f"position[]={p}" for p in POSITIONS)
    return fetch(f"https://api.sleeper.app/{kind}/nfl/{season}/{week}?season_type=regular&{pos}")


def slim(row, prefix):
    s = row.get("stats") or {}
    out = {f"{prefix}_pts": s.get("pts_half_ppr")}
    for c in COMPONENTS:
        if c in s:
            out[f"{prefix}_{c}"] = s[c]
    return out


def archive_season(season, current_week):
    rows = {}
    last_week = 18 if season < current_season else current_week
    for week in range(1, last_week + 1):
        proj = week_rows("projections", season, week)
        stat = week_rows("stats", season, week)
        stats_by_id = {r["player_id"]: r for r in stat}
        for r in proj:
            if not (r.get("stats") or {}).get("pts_half_ppr"):
                continue
            pid = r["player_id"]
            rec = {"player_id": pid, "week": week,
                   "position": (r.get("player") or {}).get("position"),
                   "team": r.get("team"), "opponent": r.get("opponent"),
                   "proj_updated": r.get("updated_at")}
            rec.update(slim(r, "proj"))
            actual = stats_by_id.get(pid)
            if actual:
                rec.update(slim(actual, "act"))
                rec["act_gp"] = (actual.get("stats") or {}).get("gp")
            rows[f"{pid}_{week}"] = rec
        print(f"  {season} wk{week}: {len(proj)} proj rows", file=sys.stderr)
    return rows


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    state = fetch("https://api.sleeper.app/v1/state/nfl")
    current_season = int(state["season"])
    current_week = int(state["week"])
    seasons = [int(a) for a in sys.argv[1:]] or list(range(FIRST_SEASON, current_season + 1))
    for season in seasons:
        path = OUT / f"{season}.json"
        if path.exists() and season < current_season:
            print(f"{season}: already archived", file=sys.stderr)
            continue
        existing = json.loads(path.read_text())["rows"] if path.exists() else {}
        fresh = archive_season(season, current_week)
        # Keep the first projection we ever saw for a week: that is the
        # pre-game number. Everything else (actuals, components) updates.
        for key, rec in fresh.items():
            old = existing.get(key)
            if old and old.get("proj_pts") is not None:
                for k in list(rec):
                    if k.startswith("proj"):
                        rec[k] = old[k] if k in old else rec[k]
            existing[key] = rec
        path.write_text(json.dumps({"season": season, "archived": datetime.date.today().isoformat(),
                                    "rows": existing}, separators=(",", ":")))
        print(f"{season}: {len(existing)} player-weeks -> {path}", file=sys.stderr)
