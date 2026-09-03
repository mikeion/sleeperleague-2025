"""The document worth sending: a narrative, not a findings list.

An earlier version led with statistics and asked the reader to assemble the
story. This one opens on a single pick, follows the pattern it belongs to, and
puts the arithmetic underneath the prose rather than in front of it.
"""
import datetime, json, subprocess, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "writeups"
GR = json.loads((HERE / "output" / "draft_grades.json").read_text())["picks"]
BW = json.loads((HERE / "output" / "sleeper" / "weekly_stats_byweek.json").read_text())


def main():
    players = json.load(urllib.request.urlopen("https://api.sleeper.app/v1/players/nfl"))
    gp = lambda pid, yr: sum(1 for w in range(1, 15) if BW.get(yr, {}).get(str(w), {}).get(pid))

    def age(pid, yr):
        b = (players.get(pid) or {}).get("birth_date")
        if not b: return None
        try:
            return (datetime.date(int(yr), 9, 1) - datetime.date.fromisoformat(b)).days / 365.25
        except Exception:
            return None
    for p in GR:
        p["age"] = age(p["pid"], p["yr"]); p["gp"] = gp(p["pid"], p["yr"])
    g = sorted([p for p in GR if p["who"] == "Gordonulus" and p["rd"] <= 4 and p["val"] < -50],
               key=lambda p: p["val"])
    BAD = r"\textbf{played badly}"
    rows = "\n".join(
        rf"{p['yr']} & {p['no']} & {p['name'][:19]} & {p['age']:.0f} & {p['gp']} & "
        rf"{p['pts']/max(p['gp'],1):.1f} & {p['val']:+.0f} & "
        + ("injured" if p["gp"] <= 9 else BAD) + r" \\" for p in g)

    tex = r"""\documentclass[11pt]{article}
\usepackage[margin=0.9in,letterpaper]{geometry}
\usepackage[sfdefault,scale=0.97]{plex-sans}
\usepackage[T1]{fontenc}
\usepackage{booktabs,array,xcolor,microtype,enumitem}
\definecolor{muted}{HTML}{6A7078}
\setlength{\parindent}{0pt}
\setlength{\parskip}{7pt}
\renewcommand{\arraystretch}{1.2}
\pagestyle{empty}
\begin{document}

{\fontsize{20}{23}\selectfont\bfseries The Nick Chubb problem}

{\color{muted}\large Why we lose, and the one part of it either of us can do
anything about.}

\vspace{10pt}
{\large\bfseries It starts with the worst pick in the league's history}

In 2023 you took Nick Chubb sixth overall. He played two games. Measured against
what a sixth pick normally returns, that is $-157$ points --- the single worst
draft pick anyone in this league has made in four years.

The obvious reading is that you cannot draft. That reading is wrong, and the
reason is in the box score: across those two games Chubb scored 10.6 points a
game. A healthy early-round pick averages 14. He was not bad. He was hurt.

Do the same for your other five, and the pattern is the same:

\vspace{4pt}
\begin{tabular}{llllrrrl}
\toprule
Year & Pick & Player & Age & Games & Pts/gm & vs slot & \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}

Rashee Rice was scoring 13.5 a game --- better than a typical first-rounder ---
and played four of them. Mike Evans played three. Cam Akers seven. In four years
of drafting, you have made exactly \textbf{one} pick that was simply wrong: Kyle
Pitts, who stayed healthy for ten games and was bad anyway.

This is not personal bad luck either. Of the 36 picks that blew up in rounds 1--4
across the whole league, \textbf{26 were injuries} --- 72\%, with a 95\% interval
of $[56\%,\,84\%]$. Almost nobody in this league is losing seasons because they
misjudged a player. They are losing them because a knee went.

\vspace{6pt}
{\large\bfseries But there is a pattern, and it is not the one you would guess}

Look at the age column again. Mitchell 24. Akers 24. Rice 24. Pitts 22. Four of
your six were players who had not yet turned 25.

Split every early-round running back, receiver and tight end in the league that
way:

\vspace{4pt}
\begin{tabular}{lrrlr}
\toprule
Age when drafted & Picks & Bust rate & 95\% interval & Avg value \\
\midrule
Under 25    & 77 & \textbf{23\%} & $[15\%,\,34\%]$ & $-5.1$ \\
25 to 28    & 89 & \textbf{8\%}  & $[4\%,\,15\%]$  & $+2.3$ \\
29 and over & 37 & 16\%          & $[7\%,\,31\%]$  & $+1.4$ \\
\bottomrule
\end{tabular}

Young players blow up \textbf{three times as often}, ratio $3.0$ with an interval
of $[1.3,\,6.7]$. Note what the third row does \emph{not} say: the old players are
fine. ``Avoid the veteran'' is not the lesson here. Avoiding the 23-year-old is.

And this is your signature. \textbf{You take 67\% of your early skill picks under
25.} The league takes 38\%. I take 21\%. You are not drafting badly --- you are
drafting young, and young is where the variance lives.

\vspace{6pt}
{\large\bfseries What a different decision would have looked like}

Not hypothetical. These players were on the board within twelve picks of the ones
you took:

\vspace{4pt}
\begin{tabular}{llll}
\toprule
You took & Result & Available shortly after & Result \\
\midrule
Nick Chubb, 6th (2023)      & $-157$ & A.J. Brown, 12th, age 26   & $+38$ \\
Cam Akers, 51st (2023)      & $-78$  & DJ Moore, 54th, age 26     & $+77$ \\
Elijah Mitchell, 47th (2022)& $-94$  & Josh Jacobs, 50th, age 25  & $+141$ \\
Rashee Rice, 52nd (2024)    & $-71$  & Terry McLaurin, 60th, 29   & $+52$ \\
Kyle Pitts, 38th (2022)     & $-51$  & Terry McLaurin, 40th, 27   & $+27$ \\
\bottomrule
\end{tabular}

That is hindsight and should be discounted heavily --- I am choosing the winner
after the fact, so it is an upper bound on what any rule could have delivered,
not a forecast. But the shape holds across all six: the prime-age player two or
three picks later kept playing.

\vspace{6pt}
{\large\bfseries So the rule is narrow}

Not ``draft better''. Not ``avoid injury-prone players'' --- that one is actually
backwards: players coming off a season where they missed five or more weeks
busted 10\% of the time, while the healthy ones busted 19\%.

Just this: \textbf{in the first four rounds, when two players are close in value
and one is 23 and the other 26, take the 26-year-old.} It is one decision, four
times a year, and it is the only thing on this page you control.

\vspace{6pt}
{\large\bfseries How far to trust it}

Two reasons to take it seriously. This is not a sample --- every pick either of us
has made on Sleeper is in it, so ``67\% of your early picks were under 25'' has no
sampling error at all. And the age gap survives a permutation test: shuffling the
age labels 200{,}000 times produced a gap that large 1{,}690 times, $p = 0.008$,
with no distributional assumption.

Two reasons for caution, which matter more. \textbf{I chose the age bands after
looking at the data}, and I ran perhaps twenty comparisons getting here. Bonferroni
against twenty tests turns $p = 0.005$ into $p = 0.10$. Thirty-six busts is not
many. \textbf{Treat this as the best lead available, not as settled} --- the real
test is whether it holds in 2026, which nobody has looked at.

\vspace{6pt}
{\large\bfseries And before this reads as one-sided}

My problem is worse and I have no excuse for it. I put in \textbf{11 waiver claims
a season}; the league median is 35, and you are at 35 yourself. When Nabers went
down in week 4 last year I lost a first-round receiver and never replaced him. You
cannot stop the injury. I did not even respond to it.

\vspace{4pt}
{\color{muted}\small Sleeper, 2022--2025: 798 draft picks, 1{,}089 waiver auctions.
A pick's value is its points in weeks 1--14, measured against replacement at that
position, minus what picks at that draft slot typically return. A ``bust'' lands
50 or more points below that, about three and a half points a week from a
starting spot.}

\end{document}
"""
    p = OUT / "why_we_suck.tex"
    p.write_text(tex)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", p.name],
                       cwd=OUT, capture_output=True)
    print(f"wrote {OUT / 'why_we_suck.pdf'}")


if __name__ == "__main__":
    main()
