"""Snowball-sample public Sleeper leagues to test whether the variance budget
estimated for one league generalises.

Starting from the seed league's members, we alternate between (a) collecting the
leagues a known user belongs to and (b) collecting the members of a newly seen
league, expanding breadth-first until a target number of leagues is reached.

Only aggregate quantities are retained: league id, size, scoring type, and the
weekly score matrix with rosters anonymised to integers. No usernames or team
names from third-party leagues are stored or reported.
"""
import collections, json, random, sys, time, urllib.request, urllib.error
from pathlib import Path

OUT = Path(__file__).parent / "output" / "multileague"
OUT.mkdir(parents=True, exist_ok=True)
SEED = "1389689478104231936"
SEASON = "2025"
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 250
PAUSE = 0.05


def J(url, tries=3):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                time.sleep(PAUSE)
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + a * 3)
                continue
            return None
        except Exception:
            time.sleep(0.5)
    return None


def crawl():
    seen_l, seen_u = set(), set()
    ql, qu = collections.deque(), collections.deque()
    users = J(f"https://api.sleeper.app/v1/league/{SEED}/users") or []
    for u in users:
        qu.append(u["user_id"]); seen_u.add(u["user_id"])
    keep = []
    while (ql or qu) and len(keep) < TARGET:
        # expand a user -> their leagues
        if qu:
            uid = qu.popleft()
            for lg in (J(f"https://api.sleeper.app/v1/user/{uid}/leagues/nfl/{SEASON}") or []):
                lid = lg["league_id"]
                if lid in seen_l:
                    continue
                seen_l.add(lid)
                if lg.get("status") != "complete":
                    continue
                st = lg.get("settings") or {}
                keep.append({"id": lid, "teams": lg.get("total_rosters"),
                             "scoring": (lg.get("scoring_settings") or {}).get("rec"),
                             "playoff_week": st.get("playoff_week_start"),
                             "positions": lg.get("roster_positions")})
                ql.append(lid)
                if len(keep) >= TARGET:
                    break
        # expand a league -> its users
        if ql and len(keep) < TARGET:
            lid = ql.popleft()
            for u in (J(f"https://api.sleeper.app/v1/league/{lid}/users") or []):
                if u["user_id"] not in seen_u:
                    seen_u.add(u["user_id"]); qu.append(u["user_id"])
        if len(keep) % 25 == 0 and keep:
            print(f"  {len(keep)} leagues, {len(seen_u)} users seen", flush=True)
    return keep


def fetch_scores(leagues):
    out = []
    for i, lg in enumerate(leagues, 1):
        pw = lg.get("playoff_week") or 15
        last = min(max(int(pw) - 1, 1), 17)
        rows = collections.defaultdict(list)
        ok = 0
        for wk in range(1, last + 1):
            ms = J(f"https://api.sleeper.app/v1/league/{lg['id']}/matchups/{wk}")
            if not ms:
                continue
            got = False
            for m in ms:
                p = m.get("points")
                if p and p > 0:
                    rows[m["roster_id"]].append(round(p, 2)); got = True
            ok += got
        # anonymise roster ids, require a usable panel
        panel = [v for v in rows.values() if len(v) >= 10]
        if len(panel) >= 8 and ok >= 10:
            out.append({"teams": lg["teams"], "scoring": lg["scoring"],
                        "weeks": ok, "n_managers": len(panel), "scores": panel,
                        "positions": lg.get("positions")})
        if i % 20 == 0:
            print(f"  scored {i}/{len(leagues)} leagues, {len(out)} usable", flush=True)
    return out


if __name__ == "__main__":
    print("crawling league graph...", flush=True)
    lg = crawl()
    (OUT / "leagues.json").write_text(json.dumps(lg))
    print(f"found {len(lg)} completed {SEASON} leagues; fetching weekly scores...", flush=True)
    sc = fetch_scores(lg)
    (OUT / "scores.json").write_text(json.dumps(sc))
    print(f"\nwrote {len(sc)} usable leagues to {OUT/'scores.json'}")
