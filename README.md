# Fat Man's Fantasy Dashboard

A dashboard for tracking our fantasy league stats. Built using the Sleeper API to pull in real-time data from our league history.

## What's in here

- Current season standings and weekly matchups
- Historical stats going back to when we started using Sleeper (2022)
- Waiver wire activity and FAAB spending
- Weekly scoring trends and power rankings
- Trade history
- **2025 Season Wrapped** - Spotify Wrapped-style season highlights
- **Draft Report** - post-draft cards, projected lineups with 80% intervals, Week 1 win probabilities, reach history

## Draft Report

`draft-report.html` is built from a static JSON file, so it loads instantly and makes no API calls. Rebuild it with:

```bash
cd data-extraction
python3 archive_projections.py   # Sleeper weekly projections + actuals, 2018 to now
python3 draft_report.py          # writes html5up-landed/assets/data/draft_report.json
python3 week_report.py           # locks this week's projections, intervals, and win probabilities
```

The homepage reads the weekly snapshots in `assets/data/weeks/` to show win probabilities next to live scores and to grade past weeks on the model scorecard. Snapshots are never rewritten once a week is played.

Run the archive Thursday morning each week so the pre-game projections are captured, and again Tuesday for the final stat lines. The intervals on the report come from the empirical distribution of RotoWire's misses in the archived seasons, by position and projection band, with starters simulated independently.

## 2025 Wrapped

A scrollytelling experience with personalized stats for each manager:

- **Personal stats**: Record, peak/valley weeks, consistency score, luck index
- **Rivalries**: Your nemesis (most losses against) and favorite opponent (most wins)
- **League highlights**: Top 5 scores, biggest blowout, heartbreaker of the season
- **Share card**: Copy a link to share your Wrapped with the league

Access via the "2025 Wrapped" button in the nav, or directly: `wrapped.html?manager=yourname`

## Running it

Just open `index.html` in a browser. No setup needed.

For local development with Netlify Functions:
```bash
cd html5up-landed
npx netlify dev
```

To use with your own league, update the league ID in `assets/js/league-data.js`.

## Built with

- Sleeper API for the data
- Chart.js for graphs
- GSAP ScrollTrigger for Wrapped animations
- HTML5 UP template for the design
