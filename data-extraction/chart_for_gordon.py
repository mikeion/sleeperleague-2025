"""The one image to send: why two managers underperform, and why the league
makes it hard to tell. Built to read as a phone screenshot in a group chat.
"""
import json, statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "output" / "charts"
PROFILE = json.loads((Path(__file__).parent / "output" / "manager_profile.json").read_text())
ICC = json.loads(Path("/tmp/icc_vals.json").read_text())

BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#9aa4b5"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
A, B = "mikeion", "Gordonulus"
FOCAL_ICC = 0.078          # 2025 only, like-for-like with the sample


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.set_axisbelow(True)


def main():
    dims, raw = PROFILE["dims"], PROFILE["raw"]
    z = PROFILE["z"]
    fig = plt.figure(figsize=(14, 6.9), facecolor=SURFACE)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.30,
                          left=.125, right=.975, top=.76, bottom=.26)

    # ---- left: the two profiles ----
    ax = fig.add_subplot(gs[0])
    ys = list(range(len(dims)))[::-1]
    for y, i in zip(ys, range(len(dims))):
        for who, off, col in ((A, 0.19, BLUE), (B, -0.19, ORANGE)):
            v = z[who][i]
            x0, w = (0, v) if v > 0 else (v, -v)
            ax.add_patch(FancyBboxPatch((x0, y + off - 0.17), w, 0.34,
                         boxstyle=f"round,pad=0,rounding_size={min(.05, w/2) if w else 0}",
                         linewidth=0, facecolor=col, mutation_aspect=.35, clip_on=False))
            pad = 0.07 if v >= 0 else -0.07
            ax.text(v + pad, y + off, f"{v:+.2f}", va="center",
                    ha="left" if v >= 0 else "right", fontsize=8.5,
                    color=col, fontweight="bold")
    ax.axvline(0, color=INK, linewidth=1.3)
    ax.set_yticks(ys); ax.set_yticklabels(dims, fontsize=10.5, color=INK)
    ax.set_xlim(-2.65, 2.65); ax.set_ylim(-0.7, len(dims) - 0.3)
    style(ax)
    ax.set_xlabel("standard deviations from league average   ←  worse      better  →",
                  fontsize=9.5, color=MUTED, labelpad=8)
    ax.set_title("1.  We are bad at different things", fontsize=13, color=INK,
                 fontweight="bold", loc="left", pad=12)

    # ---- right: where this league sits among 252 ----
    ax2 = fig.add_subplot(gs[1])
    ax2.hist(ICC, bins=30, color=GREY, edgecolor=SURFACE, linewidth=0.8)
    ax2.axvline(FOCAL_ICC, color=BLUE, linewidth=2.4)
    ax2.axvline(statistics.median(ICC), color=INK, linewidth=1.2, linestyle=(0, (4, 3)))
    ymax = ax2.get_ylim()[1]
    ax2.text(FOCAL_ICC + .012, ymax * .93, "our league\n0.078", fontsize=9.5,
             color=BLUE, fontweight="bold", va="top")
    ax2.text(statistics.median(ICC) + .012, ymax * .56, "typical league\n0.294",
             fontsize=9.5, color=INK, va="top")
    style(ax2)
    ax2.set_xlabel("share of weekly scoring explained by who the manager is",
                   fontsize=9.5, color=MUTED, labelpad=8)
    ax2.set_ylabel("leagues", fontsize=9.5, color=MUTED)
    ax2.set_title("2.  And our league barely rewards it", fontsize=13, color=INK,
                  fontweight="bold", loc="left", pad=12)

    fig.text(.035, .945, "Why we suck, and why it is hard to tell",
             fontsize=18, color=INK, fontweight="bold", ha="left")
    fig.text(.035, .900,
             "Fat Man's Fantasy 2022–25 vs 252 public Sleeper leagues  ·  "
             "left panel: every manager z-scored, higher is better",
             fontsize=10, color=MUTED, ha="left")
    fig.text(.035, .855, "mikeion", fontsize=12, color=BLUE, fontweight="bold", ha="left")
    fig.text(.096, .855, "Gordonulus", fontsize=12, color=ORANGE, fontweight="bold", ha="left")

    fig.text(.5, .025,
             "You lose in the draft: 38% of your rounds 1–4 bust, against 16% league-wide. "
             "I lose on the wire: 10 claims a season, median is 32.\n"
             "But our league is in the bottom 15% for how much any of that matters — and not "
             "because we are good. Our top half is exactly as spread out as\neveryone else's "
             "(50th percentile). What we do not have is a team that quit: 65% of leagues have one, "
             "and their worst team scores 80% of average. Ours scores 93%.",
             fontsize=10, color=INK, ha="center", va="bottom", linespacing=1.7)

    p = OUT / "why_we_suck.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
