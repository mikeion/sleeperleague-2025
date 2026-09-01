"""Reconstruct every FAAB auction and ask what wins them.

Sleeper keeps FAILED waiver claims, bid amount included, so each contested player
in a given week can be rebuilt as a sealed-bid auction: who bid, how much, who won,
and what the clearing price actually was. That makes it possible to separate
"won the player" from "paid more than he had to".
"""
import collections, json, statistics
from pathlib import Path

OUT = Path(__file__).parent / "output"
CACHE = OUT / "sleeper" / "season_skill_cache.json"
STATS = OUT / "sleeper" / "weekly_stats_cache.json"


def main():
    d = json.loads(CACHE.read_text())
    pts = json.loads(STATS.read_text()) if STATS.exists() else {}

    auctions = collections.defaultdict(list)   # (yr, week, player) -> [(bid, who, won)]
    for yr, x in d.items():
        rid2who = x["rid2who"]
        for t in x["tx"]:
            if t.get("type") != "waiver":
                continue
            bid = (t.get("settings") or {}).get("waiver_bid")
            adds = t.get("adds") or {}
            if bid is None or not adds:
                continue
            rid = t["roster_ids"][0]
            who = rid2who.get(str(rid)) or rid2who.get(rid)
            for pid in adds:
                auctions[(yr, t.get("leg"), pid)].append((bid, who, t.get("status") == "complete"))

    contested = {k: v for k, v in auctions.items() if len(v) > 1}
    print("=" * 78)
    print(f"  {len(auctions)} FAAB auctions, {len(contested)} contested (2+ bidders)")
    print("=" * 78)

    per = collections.defaultdict(lambda: collections.defaultdict(float))
    for (yr, wk, pid), bids in auctions.items():
        bids.sort(reverse=True)
        winner = next((b for b in bids if b[2]), None)
        if not winner:
            continue
        wbid, wwho, _ = winner
        losers = [b for b in bids if not b[2]]
        second = max((b[0] for b in losers), default=0)
        got = pts.get(pid, {}).get(yr, 0.0)
        per[wwho]["won"] += 1
        per[wwho]["spent"] += wbid
        per[wwho]["overpay"] += wbid - second
        per[wwho]["pts"] += got
        if losers:
            per[wwho]["contested_wins"] += 1
            per[wwho]["contested_overpay"] += wbid - second
        else:
            per[wwho]["uncontested"] += 1
        for b, who, _w in losers:
            per[who]["lost"] += 1
            per[who]["lost_bid"] += b

    print(f"  {'Manager':20}{'won':>5}{'lost':>6}{'win%':>7}{'$/win':>7}{'overpay$':>10}{'%uncont':>9}{'pts/$':>7}")
    rows = []
    for who, a in per.items():
        tries = a["won"] + a["lost"]
        if tries < 20:
            continue
        rows.append((a["contested_overpay"] / max(a["contested_wins"], 1), who, a, tries))
    for ov, who, a, tries in sorted(rows):
        print(f"  {who:20}{a['won']:>5.0f}{a['lost']:>6.0f}{a['won'] / tries * 100:>6.0f}%"
              f"{a['spent'] / max(a['won'], 1):>7.1f}{ov:>10.1f}"
              f"{a['uncontested'] / max(a['won'], 1) * 100:>8.0f}%"
              f"{a['pts'] / max(a['spent'], 1):>7.1f}")
    print("\n  overpay$ = average dollars above the next-highest bid, on CONTESTED wins only")

    print()
    print("=" * 78)
    print("  WHAT DOES A WINNING BID COST, BY WEEK?")
    print("=" * 78)
    byweek = collections.defaultdict(list)
    for (yr, wk, pid), bids in auctions.items():
        w = next((b for b in bids if b[2]), None)
        if w and wk:
            byweek[int(wk)].append(w[0])
    print(f"  {'wk':>4}{'n':>5}{'median':>8}{'mean':>7}{'max':>6}")
    for wk in sorted(byweek):
        v = byweek[wk]
        print(f"  {wk:>4}{len(v):>5}{statistics.median(v):>8.0f}{statistics.mean(v):>7.1f}{max(v):>6.0f}")

    print()
    print("=" * 78)
    print("  IS THE MARKET EFFICIENT? points returned vs price paid")
    print("=" * 78)
    buckets = [(0, 0, "$0 (free)"), (1, 4, "$1-4"), (5, 14, "$5-14"),
               (15, 34, "$15-34"), (35, 200, "$35+")]
    for lo, hi, lbl in buckets:
        v = []
        for (yr, wk, pid), bids in auctions.items():
            w = next((b for b in bids if b[2]), None)
            if w and lo <= w[0] <= hi:
                v.append(pts.get(pid, {}).get(yr, 0.0))
        if v:
            print(f"  {lbl:12} n={len(v):>4}   mean rest-of-year pts {statistics.mean(v):>6.1f}"
                  f"   median {statistics.median(v):>6.1f}   %busts(<20pts) {sum(1 for x in v if x < 20) / len(v) * 100:>5.0f}%")


if __name__ == "__main__":
    main()
