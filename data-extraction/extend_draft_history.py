"""Extend draft grading back through the MyFantasyLeague era (2016-2018).

The MFL years are a DIFFERENT game. The 20 franchises drafted as two divisions of
ten, and the divisions drafted INDEPENDENTLY from a shared player pool — 139 of
150 players went in both drafts — so it is really two parallel 10-team leagues,
not one 20-team one. Replacement level is therefore computed for 10 teams, and
the expected-value-by-pick curve is fit within era, so a pick is only ever
compared to picks made under the same rules.

2018 is excluded: MFL returns 300 draft picks for that season with an empty
player field on every one of them.

MFL player ids don't match Sleeper's, so players are joined on normalised name +
position. Points come from Sleeper's historical stats, which reach back to 2016.

Not covered: 2019 (MFL kept no draft results) and 2020-21 (the Yahoo export in
this repo is team-level only — no draft, no player detail).
"""
import collections, json, re, statistics, unicodedata, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
MFL = OUT / "mfl" / "mfl_all_years.json"
BYWEEK = OUT / "sleeper" / "weekly_stats_byweek_all.json"
YEARS = ["2016", "2017"]
# MFL era: 9 starters, no flex, 20 teams
MFL_BASE = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
MFL_TEAMS = 10          # each DIVISION drafted independently from a shared pool
MFL_FLEX = 1          # the 2-3 RB / 2-3 WR range is effectively one flex slot


def norm(n):
    n = unicodedata.normalize("NFKD", str(n)).encode("ascii", "ignore").decode()
    n = re.sub(r"\b(Jr|Sr|II|III|IV|V)\b\.?", "", n)
    return re.sub(r"[^a-z]", "", n.lower())


def J(u):
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.load(r)


def weekly(years):
    if BYWEEK.exists():
        d = json.loads(BYWEEK.read_text())
        if all(y in d for y in years):
            return d
    else:
        d = {}
    for yr in years:
        if yr in d:
            continue
        d[yr] = {}
        for wk in range(1, 15):
            try:
                s = J(f"https://api.sleeper.app/v1/stats/nfl/regular/{yr}/{wk}")
            except Exception:
                continue
            d[yr][str(wk)] = {p: v["pts_half_ppr"] for p, v in s.items()
                              if v and v.get("pts_half_ppr")}
    BYWEEK.write_text(json.dumps(d))
    return d


def main():
    mfl = json.loads(MFL.read_text())
    owner = json.loads((Path(__file__).parent / "owner_mapping.json").read_text())["mfl_to_sleeper"]
    sleeper = J("https://api.sleeper.app/v1/players/nfl")
    wk = weekly(YEARS)

    # sleeper lookup on normalised name (+ position where it disambiguates)
    byname = collections.defaultdict(list)
    for pid, p in sleeper.items():
        nm = p.get("full_name")
        if nm and p.get("position"):
            byname[norm(nm)].append((pid, p["position"]))

    rows, unmatched = [], []
    for yr in YEARS:
        y = mfl[yr]
        # MFL id -> (name, position)
        mplayers = {}
        for p in y["players"]["players"]["player"]:
            nm = p.get("name", "")
            if "," in nm:
                last, first = [x.strip() for x in nm.split(",", 1)]
                nm = f"{first} {last}"
            mplayers[p["id"]] = (nm, p.get("position"))

        units = y["draft_results"]["draftResults"]["draftUnit"]
        if isinstance(units, dict):
            units = [units]
        for unit in units:
            for pk in unit.get("draftPick", []):
                pid_mfl = pk.get("player")
                if not pid_mfl or pid_mfl not in mplayers:
                    continue
                nm, mpos = mplayers[pid_mfl]
                pos = {"PK": "K", "Def": "DEF", "TMWR": None}.get(mpos, mpos)
                cands = byname.get(norm(nm), [])
                sid = None
                if pos:
                    for c, cp in cands:
                        if cp == pos:
                            sid = c
                            break
                if sid is None and len(cands) == 1:
                    sid, pos = cands[0][0], cands[0][1]
                if sid is None:
                    unmatched.append(f"{yr} {nm} ({mpos})")
                    continue
                pts = sum(wk.get(yr, {}).get(str(w), {}).get(sid, 0.0) for w in range(1, 15))
                who = owner.get(pk["franchise"], {}).get("sleeper_username")
                rows.append({"yr": yr, "era": "MFL", "who": who, "rd": int(pk["round"]),
                             "no": (int(pk["round"]) - 1) * 10 + int(pk["pick"]),
                             "unit": unit.get("unit"), "name": nm, "pos": pos, "pts": pts})

    print(f"MFL picks parsed: {len(rows)}   unmatched: {len(unmatched)}")
    print("  sample unmatched:", "; ".join(unmatched[:8]) or "none")
    matched_rate = len(rows) / (len(rows) + len(unmatched)) * 100
    print(f"  match rate: {matched_rate:.1f}%")

    # replacement level per MFL season (20 teams, 9 starters, 1 flex)
    for yr in YEARS:
        pool = collections.defaultdict(list)
        for pid, ys in [(p, wk.get(yr, {})) for p in set()]:
            pass
        allp = collections.defaultdict(list)
        for w in wk.get(yr, {}).values():
            for pid, v in w.items():
                allp[pid].append(v)
        tot = {pid: sum(v) for pid, v in allp.items()}
        bypos = collections.defaultdict(list)
        for pid, v in tot.items():
            p = (sleeper.get(pid) or {}).get("position")
            if p in MFL_BASE:
                bypos[p].append(v)
        for p in bypos:
            bypos[p].sort(reverse=True)
        used = {p: min(MFL_BASE[p] * MFL_TEAMS, len(bypos[p])) for p in bypos}
        for _ in range(MFL_FLEX * MFL_TEAMS):
            best, bp = None, None
            for p in ("RB", "WR"):
                if used[p] < len(bypos[p]) and (best is None or bypos[p][used[p]] > best):
                    best, bp = bypos[p][used[p]], p
            if bp:
                used[bp] += 1
        repl = {p: bypos[p][min(used[p], len(bypos[p]) - 1)] for p in bypos}
        for r in rows:
            if r["yr"] == yr:
                r["par"] = r["pts"] - repl.get(r["pos"], 0.0)
        print(f"  {yr} replacement: " + "  ".join(f"{k}{v:.0f}" for k, v in sorted(repl.items())))

    # expected value by pick number, WITHIN the MFL era only
    byno = collections.defaultdict(list)
    for r in rows:
        byno[r["no"]].append(r["par"])
    nos = sorted(byno)
    for r in rows:
        pool = [v for m in nos if abs(m - r["no"]) <= 10 for v in byno[m]]
        r["val"] = r["par"] - (statistics.mean(pool) if pool else 0)

    grid = collections.defaultdict(dict)
    for r in rows:
        if r["who"]:
            grid[r["who"]][r["yr"]] = grid[r["who"]].get(r["yr"], 0.0) + r["val"]
    print()
    print("=" * 64)
    print("  MFL-ERA DRAFT SCORES (2016-2018, 20 teams, within-era baseline)")
    print("=" * 64)
    print(f"  {'Manager':22}{'2016':>9}{'2017':>9}{'2018':>9}")
    for who in sorted(grid, key=lambda w: -statistics.mean(grid[w].values())):
        line = f"  {who:22}"
        for yr in YEARS:
            line += f"{grid[who][yr]:>+9.0f}" if yr in grid[who] else f"{'—':>9}"
        print(line)
    (OUT / "mfl_draft_grades.json").write_text(json.dumps({"grid": grid, "picks": rows}, indent=1))
    print(f"\nwrote {OUT / 'mfl_draft_grades.json'}")


if __name__ == "__main__":
    main()
