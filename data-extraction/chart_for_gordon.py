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
# no highlighting and no renaming: everyone reads their own handle and draws
# their own conclusion. Singling two managers out makes it an accusation.


def main():
    ranks = D["ranks"]
    n = len(ranks)
    order = sorted(ranks, key=lambda w: statistics.mean(ranks[w].values()))

    fig, ax = plt.subplots(figsize=(11.6, 9.8), facecolor=SURFACE)
    ax.set_facecolor(SURFACE); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(-4.3, n + 1.5)

    x0, cw = 0.30, 0.132
    for j, (_key, lbl) in enumerate(COLS):
        ax.text(x0 + j * cw + cw / 2, n + 0.30, lbl, fontsize=10.2, color=MUTED,
                ha="center", va="bottom", linespacing=1.5)
    ax.plot([0.02, x0 + len(COLS) * cw], [n + 0.12, n + 0.12], color=INK, lw=1.4)

    for i, who in enumerate(order):
        y = n - 1 - i
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0.02, y - 0.42), x0 + len(COLS) * cw - 0.02, 0.84,
                                       facecolor="#f4f4ef", edgecolor="none", zorder=0))
        ax.text(0.045, y, who, fontsize=10.8, color=INK, va="center")
        for j, (key, _l) in enumerate(COLS):
            r = ranks[who][key]
            cx = x0 + j * cw + cw / 2
            ax.add_patch(plt.Rectangle((cx - 0.052, y - 0.30), 0.104, 0.60,
                                       facecolor=RAMP((r - 1) / (n - 1)),
                                       edgecolor=SURFACE, lw=1.6, zorder=2))
            ax.text(cx, y, str(r), fontsize=11, ha="center", va="center", zorder=3,
                    color="#ffffff" if r <= n * 0.45 else INK)

    ax.plot([0.02, x0 + len(COLS) * cw], [-0.55, -0.55], color=RULE, lw=1.2)
    ax.text(0.02, -0.95, "How to read it", fontsize=10, color=INK, fontweight="bold", va="top")
    ax.text(0.02, -1.30,
            "1 is best, 14 is worst, darker is better. A bust is a pick in rounds 1\u20134 that "
            "returned 50+ points less than that draft slot normally\ndoes. Overpaying is what you "
            "bid above the next-highest bid on a claim you won \u2014 money you did not need to "
            "spend. Only managers with\nthree or more seasons are ranked, since one year is far too "
            "noisy to place anyone.",
            fontsize=9.6, color=MUTED, va="top", linespacing=1.65)
    ax.text(0.02, -2.75,
            "Fitted against season wins (56 manager-seasons, checked by leaving each one out "
            "and predicting it): each extra bust in rounds 1\u20134\ncosts about one win. Ten extra "
            "waiver claims are worth a tenth of a win. But knowing all five only sharpens a guess "
            "at someone\u2019s\nrecord from \u00b12.1 wins to \u00b12.0 \u2014 they explain 8% of a season, "
            "and the other 92% is schedule, injuries and luck.",
            fontsize=9.6, color=MUTED, va="top", linespacing=1.65)

    fig.text(0.035, 0.955, "Five things you can measure about a manager",
             fontsize=20, color=INK, fontweight="bold", ha="left", va="top")
    fig.text(0.035, 0.912,
             "Fat Man's Fantasy, 2022\u201325. Every manager ranked 1 to 14 on each.",
             fontsize=11.5, color=MUTED, ha="left", va="top")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.03)
    p = OUT / "ranked.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
