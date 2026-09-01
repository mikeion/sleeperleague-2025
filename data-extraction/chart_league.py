"""Generate league charts as PNGs — one per manager, plus league-wide views.

    python3 data-extraction/chart_league.py             # everyone
    python3 data-extraction/chart_league.py Gordonulus  # just one

Head-to-head is a polarity question ("who owns whom"), so it's drawn as a
diverging bar centred on zero rather than wins-beside-losses, which makes the
reader do the subtraction. Palette is the validated blue/red diverging pair.
"""
import collections, json, sys, urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "output" / "charts"
CACHE = Path(__file__).parent / "output" / "sleeper" / "h2h_cache.json"
LEAGUES = {"2025": "1257482235834028032", "2024": "1124841011114168320",
           "2023": "998364322315190272", "2022": "859910378069577728"}

BLUE, RED = "#2a78d6", "#e34948"          # validated diverging pair
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"


def fetch():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    J = lambda u: json.load(urllib.request.urlopen(u))
    games, seasons = [], []
    for yr, lid in LEAGUES.items():
        rosters, users = J(f"https://api.sleeper.app/v1/league/{lid}/rosters"), J(f"https://api.sleeper.app/v1/league/{lid}/users")
        nm = {u["user_id"]: u["display_name"] for u in users}
        rid = {r["roster_id"]: nm.get(r["owner_id"], r["owner_id"]) for r in rosters}
        for r in rosters:
            s = r["settings"]
            seasons.append({"yr": yr, "who": rid[r["roster_id"]], "w": s["wins"], "l": s["losses"],
                            "pf": s["fpts"] + s.get("fpts_decimal", 0) / 100})
        for wk in range(1, 15):
            try:
                ms = J(f"https://api.sleeper.app/v1/league/{lid}/matchups/{wk}")
            except Exception:
                continue
            pods = collections.defaultdict(list)
            for m in ms:
                if m.get("matchup_id") is not None:
                    pods[m["matchup_id"]].append(m)
            for pod in pods.values():
                if len(pod) == 2:
                    a, b = pod
                    games.append({"yr": yr, "wk": wk, "a": rid[a["roster_id"]], "b": rid[b["roster_id"]],
                                  "pa": a["points"], "pb": b["points"]})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"games": games, "seasons": seasons}))
    return {"games": games, "seasons": seasons}


def head_to_head(games):
    h = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for g in games:
        if g["pa"] == g["pb"]:
            continue
        w, l = (g["a"], g["b"]) if g["pa"] > g["pb"] else (g["b"], g["a"])
        h[w][l][0] += 1
        h[l][w][1] += 1
    return h


def rounded_bars(ax, ys, widths, colors, height=0.62, r=0.16):
    """Flat bars read as blocks; rounded data-ends read as marks."""
    for y, w, c in zip(ys, widths, colors):
        if w == 0:
            continue
        x0, ww = (0, w) if w > 0 else (w, -w)
        ax.add_patch(FancyBboxPatch(
            (x0, y - height / 2), ww, height,
            boxstyle=f"round,pad=0,rounding_size={min(r, ww / 2) if ww else 0}",
            linewidth=0, facecolor=c, mutation_aspect=0.6, clip_on=False))


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def chart_h2h(who, h2h, path):
    opps = h2h[who]
    if not opps:
        return False
    rows = sorted(((w - l, w, l, o) for o, (w, l) in opps.items()), reverse=True)
    labels = [f"{o}" for _, _, _, o in rows]
    diffs = [d for d, _, _, _ in rows]
    ys = list(range(len(rows)))[::-1]

    fig, ax = plt.subplots(figsize=(9, 0.44 * len(rows) + 2.0), facecolor=SURFACE)
    rounded_bars(ax, ys, diffs, [BLUE if d > 0 else RED for d in diffs])
    for y, (d, w, l, _o) in zip(ys, rows):
        pad = 0.13 if d >= 0 else -0.13
        ax.text(d + pad, y, f"{w}–{l}", va="center", ha="left" if d >= 0 else "right",
                fontsize=9, color=MUTED)
    ax.axvline(0, color=MUTED, linewidth=1.1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=10, color=INK)
    lim = max(3, max(abs(d) for d in diffs) + 1.4)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    style(ax)
    ax.set_xlabel("game differential   ← they own you      you own them →",
                  fontsize=9, color=MUTED, labelpad=8)
    tw = sum(w for _, w, _, _ in rows)
    tl = sum(l for _, _, l, _ in rows)
    ax.set_title(f"{who} — head to head, 2022–2025",
                 fontsize=14, color=INK, fontweight="bold", loc="left", pad=30)
    # subtitle sits in axes coords just under the title, so it can't collide
    ax.text(0, 1.0, f"overall {tw}–{tl} ({tw / max(tw + tl, 1):.3f})",
            transform=ax.transAxes, fontsize=10, color=MUTED, ha="left", va="bottom")
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
    return True


def chart_standings(seasons, games, path):
    rec = collections.defaultdict(lambda: [0, 0])
    for g in games:
        if g["pa"] == g["pb"]:
            continue
        w, l = (g["a"], g["b"]) if g["pa"] > g["pb"] else (g["b"], g["a"])
        rec[w][0] += 1
        rec[l][1] += 1
    rows = sorted(((w / (w + l), w, l, k) for k, (w, l) in rec.items() if w + l >= 14), reverse=True)
    ys = list(range(len(rows)))[::-1]
    vals = [p - 0.5 for p, _, _, _ in rows]

    fig, ax = plt.subplots(figsize=(9, 0.44 * len(rows) + 1.8), facecolor=SURFACE)
    rounded_bars(ax, ys, vals, [BLUE if v > 0 else RED for v in vals], r=0.012)
    for y, v, (p, w, l, k) in zip(ys, vals, rows):
        pad = 0.008 if v >= 0 else -0.008
        ax.text(v + pad, y, f"{w}–{l}   {p:.3f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=9, color=MUTED)
    ax.axvline(0, color=MUTED, linewidth=1.1)
    ax.set_yticks(ys)
    ax.set_yticklabels([k for _, _, _, k in rows], fontsize=10, color=INK)
    ax.set_xlim(-0.20, 0.20)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xticks([-0.15, -0.075, 0, 0.075, 0.15])
    ax.set_xticklabels([".350", ".425", ".500", ".575", ".650"])
    style(ax)
    ax.set_xlabel("career win rate, relative to .500", fontsize=9, color=MUTED, labelpad=8)
    ax.set_title("Fat Man's Fantasy — career record, 2022–2025",
                 fontsize=14, color=INK, fontweight="bold", loc="left", pad=14)
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def main():
    data = fetch()
    games, seasons = data["games"], data["seasons"]
    h2h = head_to_head(games)
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    made = []
    for who in sorted(h2h):
        if only and who.lower() != only.lower():
            continue
        p = OUT / f"h2h_{who}.png"
        if chart_h2h(who, h2h, p):
            made.append(p.name)
    if not only:
        chart_standings(seasons, games, OUT / "career_record.png")
        made.append("career_record.png")
    print(f"wrote {len(made)} chart(s) to {OUT}")
    for m in made:
        print("  ", m)


if __name__ == "__main__":
    main()
