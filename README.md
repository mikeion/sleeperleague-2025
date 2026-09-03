# Fat Man's Fantasy Dashboard

A dashboard for tracking our fantasy league stats. Built using the Sleeper API to pull in real-time data from our league history.

## What's in here

- Current season standings and weekly matchups
- Historical stats going back to when we started using Sleeper (2022)
- Waiver wire activity and FAAB spending
- Weekly scoring trends and power rankings
- Trade history
- **2025 Season Wrapped** - Spotify Wrapped-style season highlights

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
