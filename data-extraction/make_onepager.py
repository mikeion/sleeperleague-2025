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
COLS = [("waiver claims", r"Waiver claims\\made",        "{:.0f}",  True),
        ("points per $",  r"Points per\\FAAB dollar",    "{:.1f}",  True),
        ("overpay $",     r"Overpaid on\\won bids",      r"\${:.2f}", False),
        ("early busts",   r"Busts per season\\rounds 1--4", "{:.2f}", False),
        ("lineup %",      r"Started the\\right players", r"{:.1f}\%", True)]


def main():
    ranks, rows = D["ranks"], D["rows"]
    n = len(ranks)
    vals = {w: {k: statistics.mean(r[k] for r in rows if r["who"] == w)
                for k, *_ in COLS} for w in ranks}
    order = sorted(ranks, key=lambda w: statistics.mean(ranks[w].values()))

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
\usepackage[margin=0.8in,letterpaper]{{geometry}}
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

{{\fontsize{{18}}{{21}}\selectfont\bfseries Five things you can measure about a fantasy manager}}

\vspace{{5pt}}
{{\color{{muted}}\large Fat Man's Fantasy, 2022--2025. Career averages, with each
manager's rank of {n} in small type.}}

\vspace{{15pt}}
\renewcommand{{\arraystretch}}{{1.28}}
\setlength{{\tabcolsep}}{{11pt}}
\begin{{tabular}}{{l*{{5}}{{r}}}}
\toprule
& {header} \\
\midrule
{body}
\midrule
{medrow}
\bottomrule
\end{{tabular}}

\vspace{{18pt}}
{{\large\bfseries What the columns mean}}

\vspace{{6pt}}
\begin{{itemize}}[leftmargin=1.4em,itemsep=4pt,topsep=0pt]
\item \textbf{{Waiver claims made}} --- how many you put in across a season, the ones
      you lost included.
\item \textbf{{Points per FAAB dollar}} --- points a claimed player scored
      \emph{{while in your starting lineup}}, divided by what you paid. Points he
      scored on your bench do not count.
\item \textbf{{Overpaid on won bids}} --- how far above the \emph{{next-highest}} bid you
      landed on a contested claim. Money you did not have to spend.
\item \textbf{{Busts in rounds 1--4}} --- picks returning at least 50 points less than
      that draft slot normally does.
\item \textbf{{Started the right players}} --- the share of your best possible lineup
      you actually started, judged after the fact.
\end{{itemize}}

\vspace{{16pt}}
{{\large\bfseries What any of it is worth}}

\vspace{{6pt}}
Fitted against season win totals across {len(rows)} manager-seasons, then checked by
leaving each season out and predicting it.

\vspace{{6pt}}
\begin{{itemize}}[leftmargin=1.4em,itemsep=4pt,topsep=0pt]
\item Busting a pick in the first four rounds costs about \textbf{{one win}} --- by some
      distance the most expensive thing here. Ten extra waiver claims are worth
      roughly a tenth of a win.
\item But all five together sharpen a guess at a manager's record only from
      \textbf{{$\pm$2.1 wins to $\pm$2.0}}. They account for 8\% of a season; the other
      92\% is schedule, injuries and luck.
\end{{itemize}}

\vspace{{16pt}}
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
