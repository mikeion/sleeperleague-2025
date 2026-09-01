"""One-page PDF of the manager table.

Design notes. An earlier version filled all 70 cells with a blue ramp keyed to
rank; with the value printed in the same cell the colour was redundant and the
page read as noise. Here each cell carries the number and a small superscript
rank, so both are legible without any fill. The only ink beyond black is a light
rule and grey for secondary text.
"""
import json, statistics, subprocess
from pathlib import Path

HERE = Path(__file__).parent
D = json.loads((HERE / "output" / "predict_quality.json").read_text())
OUT = HERE.parent / "writeups"
OUT.mkdir(exist_ok=True)

# key, header, format, higher-is-better
COLS = [("waiver claims", r"Waiver\\claims",            "{:.0f}",  True),
        ("points per $",  r"Points per\\FAAB \$",        "{:.1f}",  True),
        ("overpay $",     r"Overpaid\\per bid",          r"\${:.2f}", False),
        ("early busts",   r"Busts in\\rounds 1--4",      "{:.2f}", False),
        ("late steals",   r"Steals in\\rounds 8--14",  "{:.2f}", True),
        ("lineup %",      r"Started the\\right players", r"{:.1f}\%", True)]


def main():
    ranks, rows = D["ranks"], D["rows"]
    n = len(ranks)
    vals = {w: {k: statistics.mean(r[k] for r in rows if r["who"] == w)
                for k, *_ in COLS} for w in ranks}
    order = sorted(ranks, key=lambda w: -D["pred_wins"][w])

    def cell(w, k, fmt):
        v, r = vals[w][k], ranks[w][k]
        rank = rf"\rk{{{r}}}"
        return rf"{fmt.format(v)}\,{rank}"

    body = "\n".join(
        rf"{w} & " + " & ".join(cell(w, k, f) for k, _l, f, _g in COLS) + r" \\"
        for w in order)
    med = {k: statistics.median(vals[w][k] for w in vals) for k, *_ in COLS}
    medrow = r"\textbf{league median} & " + " & ".join(
        rf"\textbf{{{f.format(med[k])}}}" for k, _l, f, _g in COLS) + r" \\"
    header = " & ".join(rf"\thead{{{lbl}}}" for _, lbl, _f, _g in COLS)

    tex = rf"""\documentclass[10pt]{{article}}
\usepackage[margin=0.65in,top=0.55in,bottom=0.5in,letterpaper]{{geometry}}
\usepackage[sfdefault,scale=0.96]{{plex-sans}}
\usepackage[T1]{{fontenc}}
\usepackage{{booktabs,makecell,array,xcolor,microtype,enumitem}}
\definecolor{{muted}}{{HTML}}{{6A7078}}
\definecolor{{rule}}{{HTML}}{{C9CDD2}}
\newcommand{{\rk}}[1]{{\textsuperscript{{\textcolor{{muted}}{{\scriptsize #1}}}}}}
\renewcommand{{\theadfont}}{{\normalsize\color{{muted}}}}
\renewcommand{{\theadalign}}{{bc}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\arrayrulewidth}}{{0.5pt}}
\pagestyle{{empty}}
\begin{{document}}

{{\fontsize{{16}}{{19}}\selectfont\bfseries Six things you can measure about a fantasy manager}}

\vspace{{5pt}}
{{\color{{muted}}\large Fat Man's Fantasy, 2022--2025. Each figure is a
\emph{{per-season}} average, with the manager's rank of {n} in small type. Ordered by
what the model at the foot of the page predicts from these six numbers alone.}}

\vspace{{10pt}}
\renewcommand{{\arraystretch}}{{1.16}}
\setlength{{\tabcolsep}}{{8pt}}
\begin{{tabular}}{{l*{{6}}{{r}}}}
\toprule
& {header} \\
\midrule
{body}
\midrule
{medrow}
\bottomrule
\end{{tabular}}

\vspace{{11pt}}
{{\large\bfseries What the columns mean}}

\vspace{{6pt}}
\begin{{itemize}}[leftmargin=1.4em,itemsep=2.5pt,topsep=0pt]
\item \textbf{{Waiver claims}} --- how many you put in per season, the ones you lost
      included.
\item \textbf{{Points per FAAB dollar}} --- points a claimed player scored \emph{{while
      you started him}}, divided by what you paid. Bench points do not count.
\item \textbf{{Overpaid per bid}} --- how far above the \emph{{next-highest}} bid you
      landed on a contested claim: money you did not have to spend.
\item \textbf{{Busts in rounds 1--4}} --- early picks finishing 50+ points below what
      that slot usually returns. Malik Nabers, taken 14th in 2025, played four
      games and came in 119 points light: one bust.
\item \textbf{{Steals in rounds 8--14}} --- the mirror of a bust, same threshold. Rico
      Dowdle, taken 154th in 2025, finished RB17: one steal.
\item \textbf{{Started the right players}} --- the share of your best possible lineup
      you actually started, judged with hindsight.
\end{{itemize}}

\vspace{{11pt}}
{{\large\bfseries Why none of this explains very much}}

\vspace{{6pt}}
Not because managers are alike. The spread of season win rates has an SD of
\textbf{{0.152}}; fourteen tosses of a fair coin give \textbf{{0.134}} of that
alone, leaving \textbf{{0.072}} for real differences --- a good manager here sits
near a \textbf{{0.57}} weekly win probability and a poor one near \textbf{{0.43}},
eight wins against six. The gap is real; the noise is simply twice its size.

\vspace{{6pt}}
That caps what any model can reach. Suppose you somehow knew every manager's
\emph{{true}} long-run scoring level --- not his noisy fourteen-week sample, but the
exact figure he would converge to over hundreds of weeks. Predicting a single
season's record from that alone would get you about \textbf{{23\%}} of the way,
because the season is still fourteen weighted coin flips laid on top. It is the
batting-average problem: a true .300 hitter and a true .270 hitter swap places
constantly over fourteen at-bats.

\vspace{{6pt}}
So 23\% is the ceiling for anybody, with any data. These six columns reach 6\% of
the total, about a quarter of what is reachable, and 11\% when judged against
points scored rather than games won. Measured against 252 other Sleeper leagues,
ours sits near the \textbf{{15th percentile}} for how much a manager matters at
all --- the median league has managers differing three times as much as ours do.
Nobody here pulls far ahead, because nobody here has quit.

\vspace{{6pt}}
\begin{{itemize}}[leftmargin=1.4em,itemsep=2.5pt,topsep=0pt]
\item Busting one early pick costs about \textbf{{one win}}, the most expensive single
      thing on this page. Ten extra waiver claims are worth about a tenth of a win.
\item Every figure is out of sample: each of the {len(rows)} manager-seasons was removed
      in turn, the model refitted without it, and used to predict the season it
      had never seen.
\end{{itemize}}

\vspace{{11pt}}
{{\color{{muted}}\small Managers with fewer than three seasons are not ranked --- one
year is far too noisy to place anyone.}}

\end{{document}}
"""
    p = OUT / "manager_ranks.tex"
    p.write_text(tex)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", p.name],
                       cwd=OUT, capture_output=True)
    print(f"wrote {OUT / 'manager_ranks.pdf'}")


if __name__ == "__main__":
    main()
