"""A league table of manager behaviour, in ranks.

Ranks, not z-scores: everyone in a fantasy league already reads standings.
Plain column names, no invented metric vocabulary, and the honest caveat about
how little any of it predicts printed on the figure itself.
"""
import json, statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

OUT = Path(__file__).parent / "output" / "charts"
D = json.loads((OUT.parent / "predict_quality.json").read_text())

SURFACE, INK, MUTED, RULE = "#fcfcfb", "#0b0b0b", "#5c6470", "#e3e3dd"
HILITE = "#fff3d6"
# sequential blue, dark = rank 1. Starts at step 250 so the palest cell still reads.
RAMP = LinearSegmentedColormap.from_list("b", ["#0d366b", "#256abf", "#5598e7", "#9ec5f4", "#e8f1fd"])

COLS = [("waiver claims", "Waiver claims\nmade"),
        ("points per $",  "Points per\nFAAB dollar"),
        ("overpay $",     "Overpaying on\nwon bids"),
        ("early busts",   "Busts in\nrounds 1–4"),
        ("lineup %",      "Started the\nright players")]
FOCUS = {"mikeion": "Mike", "Gordonulus": "Gordon"}


def main():
    ranks = D["ranks"]
    n = len(ranks)
    order = sorted(ranks, key=lambda w: statistics.mean(ranks[w].values()))

    fig, ax = plt.subplots(figsize=(11.6, 8.4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(-1.9, n + 1.5)

    x0, cw = 0.30, 0.132
    for j, (_key, lbl) in enumerate(COLS):
        ax.text(x0 + j * cw + cw / 2, n + 0.30, lbl, fontsize=10.2, color=MUTED,
                ha="center", va="bottom", linespacing=1.5)
    ax.plot([0.02, x0 + len(COLS) * cw], [n + 0.12, n + 0.12], color=INK, lw=1.4)

    for i, who in enumerate(order):
        y = n - 1 - i
        name = FOCUS.get(who, who)
        focus = who in FOCUS
        if focus:
            ax.add_patch(plt.Rectangle((0.02, y - 0.42), x0 + len(COLS) * cw - 0.02, 0.84,
                                       facecolor=HILITE, edgecolor="none", zorder=0))
        ax.text(0.045, y, name, fontsize=11.5 if focus else 10.8, color=INK,
                va="center", fontweight="bold" if focus else "normal")
        for j, (key, _l) in enumerate(COLS):
            r = ranks[who][key]
            cx = x0 + j * cw + cw / 2
            ax.add_patch(plt.Rectangle((cx - 0.052, y - 0.30), 0.104, 0.60,
                                       facecolor=RAMP((r - 1) / (n - 1)),
                                       edgecolor=SURFACE, lw=1.6, zorder=2))
            ax.text(cx, y, str(r), fontsize=11, ha="center", va="center", zorder=3,
                    color="#ffffff" if r <= n * 0.45 else INK,
                    fontweight="bold" if focus else "normal")

    ax.plot([0.02, x0 + len(COLS) * cw], [-0.55, -0.55], color=RULE, lw=1.2)
    ax.text(0.02, -1.02, "Rank out of 15 managers, Fat Man's Fantasy 2022–25.  "
                         "1 is best.  Darker is better.",
            fontsize=10, color=MUTED, va="top")
    ax.text(0.02, -1.48,
            "All five together explain 8% of season wins out of sample. "
            "Busting an early pick is the costliest at three-quarters of a win.",
            fontsize=10, color=MUTED, va="top")

    fig.text(0.035, 0.955, "Mike and Gordon, ranked", fontsize=20, color=INK,
             fontweight="bold", ha="left", va="top")
    fig.text(0.035, 0.912,
             "Gordon is last or nearly last at drafting. Mike is last at working the wire.",
             fontsize=11.5, color=MUTED, ha="left", va="top")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.03)
    p = OUT / "ranked.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
