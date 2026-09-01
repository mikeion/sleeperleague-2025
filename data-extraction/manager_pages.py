"""Per-manager detail pages: the picks and claims behind the summary numbers.

A league table tells a manager where he stands. It does not tell him which
decisions put him there, which is the only part he can act on. These pages name
them.
"""
import collections, json, statistics, subprocess, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "writeups"
GR = json.loads((HERE / "output" / "draft_grades.json").read_text())
SK = json.loads((HERE / "output" / "sleeper" / "season_skill_cache.json").read_text())
BW = json.loads((HERE / "output" / "sleeper" / "weekly_stats_byweek.json").read_text())
PQ = json.loads((HERE / "output" / "predict_quality.json").read_text())
WHO = ["mikeion", "Gordonulus"]


def esc(s):
    return str(s).replace("&", r"\&").replace("%", r"\%").replace("$", r"\$").replace("#", r"\#")


def main():
    players = json.load(urllib.request.urlopen("https://api.sleeper.app/v1/players/nfl"))
    nm = lambda p: (players.get(p) or {}).get("full_name") or p
    started = collections.defaultdict(set)
    for yr, d in SK.items():
        r2w = d["rid2who"]
        for wk, ms in d["weeks"].items():
            for m in ms:
                w = r2w.get(str(m["roster_id"])) or r2w.get(m["roster_id"])
                if w:
                    for p in (m.get("starters") or []): started[(yr, w)].add((int(wk), p))

    claims = collections.defaultdict(list)
    for yr, d in SK.items():
        r2w = d["rid2who"]
        auc = collections.defaultdict(list)
        for t in d["tx"]:
            if t.get("type") != "waiver": continue
            bid = (t.get("settings") or {}).get("waiver_bid"); adds = t.get("adds") or {}
            if bid is None or not adds: continue
            w = r2w.get(str(t["roster_ids"][0])) or r2w.get(t["roster_ids"][0])
            for pid in adds: auc[(t.get("leg"), pid)].append((bid, w, t.get("status") == "complete"))
        for (wk, pid), bids in auc.items():
            win = next((b for b in bids if b[2]), None)
            if not win or not wk: continue
            wbid, w, _ = win
            if not w: continue
            got = sum(BW.get(yr, {}).get(str(x), {}).get(pid, 0.0) or 0.0
                      for x in range(int(wk), 15) if (x, pid) in started[(yr, w)])
            second = max((b[0] for b in bids if not b[2]), default=None)
            claims[w].append({"yr": yr, "wk": int(wk), "name": nm(pid), "bid": wbid,
                              "got": got, "second": second})

    secs = []
    for who in WHO:
        early = sorted([p for p in GR["picks"] if p["who"] == who and p["rd"] <= 4],
                       key=lambda p: p["val"])
        late = sorted([p for p in GR["picks"] if p["who"] == who and p["rd"] >= 8],
                      key=lambda p: -p["val"])
        cl = claims[who]
        bestcl = sorted(cl, key=lambda c: -c["got"])[:5]
        waste = sorted([c for c in cl if c["bid"] >= 5], key=lambda c: c["got"])[:5]
        overpays = [c for c in cl if c["second"] is not None]
        overpays.sort(key=lambda c: -(c["bid"] - c["second"]))

        def rowsD(ps, n=5):
            return "\n".join(
                rf"{p['yr']} & R{p['rd']} & {esc(p['name'][:22])} & {p['pos']} & "
                rf"{p['pts']:.0f} & {p['val']:+.0f} \\" for p in ps[:n])

        def rowsC(cs, n=5):
            return "\n".join(
                rf"{c['yr']} & wk {c['wk']} & {esc(c['name'][:22])} & \${c['bid']} & "
                rf"{c['got']:.0f} \\" for c in cs[:n])

        nseason = len({p["yr"] for p in GR["picks"] if p["who"] == who})
        secs.append(rf"""
\newpage
{{\fontsize{{17}}{{20}}\selectfont\bfseries {esc(who)}}}

\vspace{{4pt}}
{{\color{{muted}}\large The picks and claims behind the summary table.}}

\vspace{{14pt}}
{{\large\bfseries The early picks that cost the most}}

\vspace{{4pt}}
{{\color{{muted}}\small ``Cost'' is points below what that draft slot normally returns.
Anything under $-50$ counts as a bust.}}

\vspace{{6pt}}
\begin{{tabular}}{{llllrr}}
\toprule
\thead{{Year}} & \thead{{Rd}} & \thead{{Player}} & \thead{{Pos}} & \thead{{Points}} & \thead{{vs slot}} \\
\midrule
{rowsD(early)}
\bottomrule
\end{{tabular}}

\vspace{{16pt}}
{{\large\bfseries The late picks that paid off}}

\vspace{{6pt}}
\begin{{tabular}}{{llllrr}}
\toprule
\thead{{Year}} & \thead{{Rd}} & \thead{{Player}} & \thead{{Pos}} & \thead{{Points}} & \thead{{vs slot}} \\
\midrule
{rowsD(late)}
\bottomrule
\end{{tabular}}

\vspace{{16pt}}
{{\large\bfseries Best claims off the wire}}

\vspace{{4pt}}
{{\color{{muted}}\small Points counted only from the week you claimed him, and only in
weeks you actually started him.}}

\vspace{{6pt}}
\begin{{tabular}}{{lllrr}}
\toprule
\thead{{Year}} & \thead{{Week}} & \thead{{Player}} & \thead{{Paid}} & \thead{{Points}} \\
\midrule
{rowsC(bestcl)}
\bottomrule
\end{{tabular}}

\vspace{{16pt}}
{{\large\bfseries Money that bought nothing}}

\vspace{{4pt}}
{{\color{{muted}}\small Claims of \$5 or more that returned least.}}

\vspace{{6pt}}
\begin{{tabular}}{{lllrr}}
\toprule
\thead{{Year}} & \thead{{Week}} & \thead{{Player}} & \thead{{Paid}} & \thead{{Points}} \\
\midrule
{rowsC(waste)}
\bottomrule
\end{{tabular}}

\vspace{{14pt}}
{{\color{{muted}}\small Across {nseason} seasons: {len(cl)} winning claims,
\${sum(c['bid'] for c in cl)} spent,
{sum(c['got'] for c in cl):.0f} points returned from the lineup.
Biggest unnecessary overpay: \${overpays[0]['bid'] - overpays[0]['second']} more than the
next bid on {esc(overpays[0]['name'])} in {overpays[0]['yr']}.}}
""")

    tex = r"""\documentclass[10pt]{article}
\usepackage[margin=0.8in,letterpaper]{geometry}
\usepackage[sfdefault,scale=0.96]{plex-sans}
\usepackage[T1]{fontenc}
\usepackage{booktabs,makecell,array,xcolor,microtype}
\definecolor{muted}{HTML}{6A7078}
\renewcommand{\theadfont}{\normalsize\color{muted}}
\renewcommand{\theadalign}{bl}
\renewcommand{\arraystretch}{1.25}
\setlength{\tabcolsep}{9pt}
\setlength{\parindent}{0pt}
\pagestyle{empty}
\begin{document}
""" + "\n".join(secs).replace("\\newpage", "", 1) + r"""
\end{document}
"""
    p = OUT / "manager_detail.tex"
    p.write_text(tex)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", p.name],
                       cwd=OUT, capture_output=True)
    print(f"wrote {OUT / 'manager_detail.pdf'}")


if __name__ == "__main__":
    main()
