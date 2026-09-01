"""One shareable image: two managers against the league, on what they control.

Built to be readable as a phone screenshot in a group chat, so: big type, direct
labels on every bar, no legend hunting, and the punchline written on the chart.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "output" / "charts"
PROFILE = Path(__file__).parent / "output" / "manager_profile.json"

BLUE, ORANGE = "#2a78d6", "#eb6834"          # validated categorical slots 1 & 2
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
A, B = "mikeion", "Gordonulus"


def bar(ax, y, w, color, h=0.34):
    if abs(w) < 1e-9:
        return
    x0, ww = (0, w) if w > 0 else (w, -w)
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), ww, h,
                                boxstyle=f"round,pad=0,rounding_size={min(.05, ww/2)}",
                                linewidth=0, facecolor=color, mutation_aspect=.35, clip_on=False))


def main():
    d = json.loads(PROFILE.read_text())
    dims, z = d["dims"], d["z"]
    n = len(dims)
    ys = list(range(n))[::-1]

    fig, ax = plt.subplots(figsize=(10.5, 6.4), facecolor=SURFACE)
    for y, dim, i in zip(ys, dims, range(n)):
        bar(ax, y + 0.19, z[A][i], BLUE)
        bar(ax, y - 0.19, z[B][i], ORANGE)
        for val, off, col in ((z[A][i], 0.19, BLUE), (z[B][i], -0.19, ORANGE)):
            pad = 0.07 if val >= 0 else -0.07
            ax.text(val + pad, y + off, f"{val:+.2f}", va="center",
                    ha="left" if val >= 0 else "right", fontsize=9, color=col, fontweight="bold")

    ax.axvline(0, color=INK, linewidth=1.3)
    ax.set_yticks(ys)
    ax.set_yticklabels(dims, fontsize=11.5, color=INK)
    ax.set_xlim(-2.65, 2.65)
    ax.set_ylim(-0.75, n - 0.25)
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("standard deviations from the league average   ←  worse        better  →",
                  fontsize=10, color=MUTED, labelpad=10)

    ax.set_title("Six things you control. We are bad at different ones.",
                 fontsize=16.5, color=INK, fontweight="bold", loc="left", pad=42)
    ax.text(0, 1.055, "Fat Man's Fantasy, 2022–2025 · every manager z-scored · higher is better",
            transform=ax.transAxes, fontsize=9.5, color=MUTED, ha="left", va="bottom")
    ax.text(0.0, 1.012, "mikeion", transform=ax.transAxes, fontsize=11,
            color=BLUE, fontweight="bold", ha="left", va="bottom")
    ax.text(0.088, 1.012, "Gordonulus", transform=ax.transAxes, fontsize=11,
            color=ORANGE, fontweight="bold", ha="left", va="bottom")

    fig.text(0.5, 0.028,
             "mikeion: last in the league on both waiver columns — 10 claims a season, league median is 31."
             "\nGordonulus: above average on waivers. Worst bust rate in the league in rounds 1–4.",
             fontsize=10, color=INK, ha="center", va="bottom", linespacing=1.6)
    fig.tight_layout(rect=[0, 0.10, 1, 1])
    p = OUT / "us_vs_league.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
