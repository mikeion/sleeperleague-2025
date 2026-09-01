"""A one-page draft scouting report for any manager in the league.

    python3 data-extraction/scouting_report.py Gordonulus

Shows what that manager actually does in the first four rounds, where it has gone
wrong, and their pick numbers for tonight. Everything is measured against the
same baselines as the rest of the repo: points above replacement, minus what the
draft slot typically returns.
"""
import collections, datetime, json, statistics, sys, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "output"
GRADES = OUT / "draft_grades.json"
DRAFT_2026 = "1389689478104231937"
TEAMS, ROUNDS = 14, 14


def J(u):
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.load(r)


def picks_for(slot):
    return [(r, (r - 1) * TEAMS + slot if r % 2 else r * TEAMS - slot + 1)
            for r in range(1, ROUNDS + 1)]


def main():
    who = sys.argv[1] if len(sys.argv) > 1 else "Gordonulus"
    data = json.loads(GRADES.read_text())
    picks = [p for p in data["picks"] if p["who"] == who]
    if not picks:
        sys.exit(f"no picks found for {who}. Names: "
                 + ", ".join(sorted({p['who'] for p in data['picks']})))
    allp = data["picks"]
    players = J("https://api.sleeper.app/v1/players/nfl")

    def age(pid, yr):
        b = (players.get(pid) or {}).get("birth_date")
        if not b:
            return None
        try:
            return (datetime.date(int(yr), 9, 1) - datetime.date.fromisoformat(b)).days / 365.25
        except Exception:
            return None

    W = 74
    print("=" * W)
    print(f"  SCOUTING REPORT — {who}".ljust(W))
    print(f"  Fat Man's Fantasy · drafts 2022–2025 · {len(picks)} picks".ljust(W))
    print("=" * W)

    early = [p for p in picks if p["rd"] <= 4]
    lg_early = [p for p in allp if p["rd"] <= 4]
    bust = [p for p in early if p["val"] < -50]
    print(f"\n  ROUNDS 1–4 — where this league is won and lost")
    print(f"    value per pick     {statistics.mean(p['val'] for p in early):>+8.1f}"
          f"   (league {statistics.mean(p['val'] for p in lg_early):+.1f})")
    print(f"    bust rate          {len(bust) / len(early) * 100:>7.0f}%"
          f"   (league {sum(1 for p in lg_early if p['val'] < -50) / len(lg_early) * 100:.0f}%)")
    late = [p for p in picks if p["rd"] >= 8]
    print(f"    rounds 8+ per pick {statistics.mean(p['val'] for p in late):>+8.1f}"
          f"   (league {statistics.mean(p['val'] for p in allp if p['rd'] >= 8):+.1f})")

    print(f"\n  THE PICKS THAT COST YOU")
    for p in sorted(bust, key=lambda x: x["val"])[:6]:
        a = age(p["pid"], p["yr"])
        print(f"    {p['yr']}  R{p['rd']} pk{p['no']:>3}  {p['name'][:21]:22}"
              f"{p['pos']:4}{('age ' + f'{a:.0f}') if a else '':7}{p['val']:>+8.1f}")

    print(f"\n  WHAT YOU TAKE, AND WHEN")
    print(f"    {'':8}" + "".join(f"{x:>7}" for x in ("QB", "RB", "WR", "TE")))
    for lbl, lo, hi in (("R1-2", 1, 2), ("R3-4", 3, 4), ("R5-7", 5, 7), ("R8-14", 8, 14)):
        sub = [p for p in picks if lo <= p["rd"] <= hi]
        c = collections.Counter(p["pos"] for p in sub)
        n = len(sub) or 1
        print(f"    {lbl:8}" + "".join(f"{c[k] / n * 100:>6.0f}%" for k in ("QB", "RB", "WR", "TE")))
    firsts = {}
    for pos in ("QB", "TE"):
        by = {}
        for p in picks:
            if p["pos"] == pos:
                by[p["yr"]] = min(by.get(p["yr"], 99), p["rd"])
        firsts[pos] = statistics.mean(by.values()) if by else None
    for pos, v in firsts.items():
        lg = []
        for w in {x["who"] for x in allp}:
            by = {}
            for p in allp:
                if p["who"] == w and p["pos"] == pos:
                    by[p["yr"]] = min(by.get(p["yr"], 99), p["rd"])
            if by:
                lg.append(statistics.mean(by.values()))
        if v:
            print(f"    first {pos} on average: round {v:.1f}   (league {statistics.mean(lg):.1f})")

    ages = [age(p["pid"], p["yr"]) for p in early if p["pos"] in ("RB", "WR", "TE")]
    ages = [a for a in ages if a]
    lgages = [age(p["pid"], p["yr"]) for p in lg_early if p["pos"] in ("RB", "WR", "TE")]
    lgages = [a for a in lgages if a]
    if ages:
        print(f"    average age of a round 1–4 skill pick: {statistics.mean(ages):.1f}"
              f"   (league {statistics.mean(lgages):.1f})")

    # tonight
    order = J(f"https://api.sleeper.app/v1/draft/{DRAFT_2026}")["draft_order"]
    users = {u["user_id"]: u["display_name"]
             for u in J("https://api.sleeper.app/v1/league/1389689478104231936/users")}
    slot = next((s for uid, s in order.items() if users.get(uid) == who), None)
    if slot:
        print(f"\n  TONIGHT — you pick from slot {slot} of {TEAMS}")
        pk = picks_for(slot)
        print("    " + "  ".join(f"R{r}:{n}" for r, n in pk[:7]))
        print("    " + "  ".join(f"R{r}:{n}" for r, n in pk[7:]))
        gaps = [pk[i + 1][1] - pk[i][1] - 1 for i in range(len(pk) - 1)]
        print(f"    longest wait between picks: {max(gaps)} picks")
    print("\n" + "=" * W)
    print("  Value = points above replacement at the position, minus what that draft")
    print("  slot typically returns. Half-PPR, weeks 1-14. 16 early picks per manager,")
    print("  so read the bust count as a tendency, not a verdict.")
    print("=" * W)


if __name__ == "__main__":
    main()
