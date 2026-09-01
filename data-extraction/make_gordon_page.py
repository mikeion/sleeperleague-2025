"""The one page to actually send.

Three findings survived a day of analysis. Everything else — variance
components, cross-league comparisons, out-of-sample R^2 — was scaffolding used
to establish that those three are the only ones worth reporting, and none of it
belongs on this page.
"""
import datetime, json, statistics, subprocess, urllib.request
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
        if p["rd"] <= 4:
            p["gp"] = gp(p["pid"], p["yr"]); p["age"] = age(p["pid"], p["yr"])
    busts = [p for p in GR if p["rd"] <= 4 and p["val"] < -50]
    g = sorted([p for p in busts if p["who"] == "Gordonulus"], key=lambda p: p["val"])
    BAD = r"\textbf{played badly}"
    rows = "\n".join(
        rf"{p['yr']} & R{p['rd']} & {p['name'][:20]} & {p['gp']} & "
        rf"{p['pts']/max(p['gp'],1):.1f} & {p['val']:+.0f} & "
        + ("injured" if p["gp"] <= 9 else BAD) + r" \\" for p in g)

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[margin=0.85in,letterpaper]{{geometry}}
\usepackage[sfdefault,scale=0.97]{{plex-sans}}
\usepackage[T1]{{fontenc}}
\usepackage{{booktabs,array,xcolor,microtype,enumitem}}
\definecolor{{muted}}{{HTML}}{{6A7078}}
\setlength{{\parindent}}{{0pt}}
\renewcommand{{\arraystretch}}{{1.2}}
\pagestyle{{empty}}
\begin{{document}}

{{\fontsize{{19}}{{22}}\selectfont\bfseries Why we suck}}

\vspace{{4pt}}
{{\color{{muted}}\large Four years of our drafts and waiver claims, pulled apart.
Two things came out.}}

\vspace{{18pt}}
{{\large\bfseries 1.\quad Almost none of it is bad drafting}}

\vspace{{7pt}}
Across the league, \textbf{{72\% of the picks that blew up in rounds 1--4 were
injuries}}, not misjudgements. A healthy early pick averages 14 points a game.
Here are your six:

\vspace{{9pt}}
\begin{{tabular}}{{lllrrrl}}
\toprule
Year & Rd & Player & Games & Pts/gm & vs slot & \\
\midrule
{rows}
\bottomrule
\end{{tabular}}

\vspace{{9pt}}
Rashee Rice was scoring 13.5 a game and played four of them. Chubb was at 10.6
and played two. \textbf{{You have one genuine miss in four years}} --- Kyle Pitts,
who played ten games and was bad. Everything else was a knee.

\vspace{{6pt}}
Out of 36 such busts league-wide, 26 were injuries: \textbf{{72\%}}, with a 95\%
interval of $[56\%,\,84\%]$.

\vspace{{18pt}}
{{\large\bfseries 2.\quad But you draft young, and young is where things break}}

\vspace{{7pt}}
Splitting every early-round running back, receiver and tight end in the league by
age at the time he was drafted:

\vspace{{9pt}}
\begin{{tabular}}{{lrrlr}}
\toprule
Age when drafted & Picks & Bust rate & 95\% interval & Avg value \\
\midrule
Under 25    & 77 & \textbf{{23\%}} & $[15\%,\,34\%]$ & $-5.1$ \\
25 to 28    & 89 & \textbf{{8\%}}  & $[4\%,\,15\%]$  & $+2.3$ \\
29 and over & 37 & 16\%            & $[7\%,\,31\%]$  & $+1.4$ \\
\bottomrule
\end{{tabular}}

\vspace{{10pt}}
The gap between the first two rows is \textbf{{16 percentage points}}, interval
$[5,\,26]$; as a ratio, under-25 picks bust \textbf{{3.0 times}} as often,
interval $[1.3,\,6.7]$. A two-proportion test gives $z = 2.79$, $p = 0.005$. That
test assumes a normal approximation, so I also shuffled the age labels 200{{,}}000
times and counted how often a gap this large appeared by chance: 1{{,}}690 times,
$p = 0.008$. Same answer without the assumption.

\vspace{{8pt}}
\textbf{{You take 67\% of your early skill picks under 25}}, interval
$[42\%,\,85\%]$. The league takes 38\%, interval $[32\%,\,45\%]$. I take 21\%.
Mitchell, Akers, Rice and Pitts were all 24 or younger. You are not drafting
badly; you are drafting young, and young is where the variance lives. Bijan and
Chase are why you keep doing it.

\vspace{{18pt}}
{{\large\bfseries 3.\quad Three things that did \emph{{not}} hold up}}

\vspace{{7pt}}
\begin{{itemize}}[leftmargin=1.4em,itemsep=4pt,topsep=0pt]
\item \textbf{{Age as a straight line.}} The correlation between age and games played
      is $-0.013$, interval $[-0.15,\,+0.13]$. Dead zero. The effect is not
      ``older is worse'' --- the 29-and-over group is no worse than average. Only
      the young end is unusual.
\item \textbf{{Avoiding injury-prone players.}} Players drafted after a season in
      which they missed five or more weeks busted 10\% of the time. Players who
      had been healthy busted 19\%. The obvious heuristic is backwards here,
      though on only 20 picks.
\item \textbf{{The idea that some of us are simply better.}} Year-to-year correlation
      in season wins across the league is $-0.10$. Top-four finishes repeat 25\%
      of the time; chance alone gives 29\%. Nobody in this league persists.
\end{{itemize}}

\vspace{{18pt}}
{{\large\bfseries 4.\quad And my problem is the opposite}}

\vspace{{7pt}}
I put in \textbf{{11 waiver claims a season}}. The league median is 35. You are at
35 yourself, which is the one thing you do better than almost anyone here. When
Nabers went down in week 4 last year I lost a first-round receiver and simply
never replaced him.

\vspace{{18pt}}
{{\large\bfseries How the numbers were built, and how far to trust them}}

\vspace{{7pt}}
Every pick is scored the same way. A player's fantasy points in weeks 1--14 are
compared against \emph{{replacement level}} --- what the best freely available
player at his position scored that season, computed by filling all fourteen
starting lineups and taking the next man. That difference is then compared
against what picks at that draft slot typically return, averaged over every pick
within twelve slots of it. A ``bust'' is a pick landing 50 or more points below
that, which is roughly three and a half points a week from a starting spot across
a season.

\vspace{{8pt}}
Two reasons to take it seriously: it is not a sample. Every pick and every claim
either of us has made on Sleeper is in here, so there is no sampling error in the
descriptive figures --- 67\% of your early picks really were under 25. And the
age result survived a permutation test, which makes no distributional assumption
at all.

\vspace{{8pt}}
Two reasons for caution, which matter more. \textbf{{I chose the age bands after
looking at the data}}, and I ran perhaps twenty comparisons over the course of
this: positions, draft slots, schedule effects, injury history, waiver behaviour,
lineup efficiency. Bonferroni against twenty tests turns $p = 0.005$ into
$p = 0.10$. And 36 busts is not many. \textbf{{Treat the age finding as the best
lead we have, not as established}} --- the honest test is whether it holds in
2026, on a season nobody has looked at yet.

\vspace{{14pt}}
{{\color{{muted}}\small Sleeper data, 2022--2025, 798 draft picks and 1{{,}}089 waiver
auctions. A ``bust'' is a pick returning 50+ points less than that draft slot
normally does, measured against the position's replacement level.}}

\end{{document}}
"""
    p = OUT / "why_we_suck.tex"
    p.write_text(tex)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", p.name],
                       cwd=OUT, capture_output=True)
    print(f"wrote {OUT / 'why_we_suck.pdf'}")


if __name__ == "__main__":
    main()
