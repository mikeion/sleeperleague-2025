# Fantasy Football Dashboard - Deployment Guide

This guide will walk you through deploying your dashboard to Netlify with automatic weekly H2H data refresh.

## What's Been Set Up

Your dashboard now has:
- **Scheduled function** that runs every Tuesday at midnight UTC to refresh H2H data
- **API endpoint** (`/api/h2h`) that serves pre-calculated H2H data
- **Fallback mechanism** - if server data isn't available, calculates locally with 7-day cache

## Files Created

```
html5up-landed/
├── netlify/
│   └── functions/
│       ├── refresh-h2h.mjs       # Scheduled function (runs Tuesdays at midnight)
│       └── get-h2h.mjs           # API endpoint to fetch H2H data
├── netlify.toml                  # Netlify configuration
├── package.json                  # Dependencies for Netlify Functions
└── DEPLOYMENT.md                 # This file
```

## Deployment Steps

### 1. Install Dependencies

First, install the required npm packages:

```bash
cd /Users/mikeion/Documents/dev/utilities/fantasy-league/html5up-landed
npm install
```

### 2. Test Locally (Optional)

You can test the functions locally using Netlify Dev:

```bash
npm run dev
```

This will start a local server at `http://localhost:8888` where you can test the dashboard.

### 3. Deploy to Netlify

Login to Netlify (using npx to run the local CLI):

```bash
npx netlify login
```

This will open a browser window to authorize the CLI.

Initialize your site (first time only):

```bash
npx netlify init
```

Follow the prompts:
- Choose "Create & configure a new site"
- Select your team
- Give your site a name (e.g., "my-fantasy-dashboard")
- For build command: leave empty or use `echo "Static site"`
- For publish directory: use `.` (current directory)

Deploy to production:

```bash
npx netlify deploy --prod
```

### 4. Enable Netlify Blobs

Netlify Blobs is automatically available on all sites. The scheduled function will use it to store the H2H data.

### 5. Verify Scheduled Function

After deployment:

1. Go to your Netlify dashboard: https://app.netlify.com
2. Click on your site
3. Navigate to **Functions** in the sidebar
4. You should see `refresh-h2h` listed as a scheduled function
5. Check the logs to see when it last ran

### 6. Manual Trigger (First Time)

The scheduled function runs every Tuesday at midnight UTC, but you can manually trigger it the first time:

1. Go to your Netlify site dashboard
2. Click **Functions** → `refresh-h2h`
3. Click **Trigger function** or use the Netlify CLI:

```bash
npx netlify functions:invoke refresh-h2h
```

This will pre-populate the H2H data so it's available immediately.

## How It Works

### Data Flow

1. **Tuesday Midnight UTC**: Scheduled function runs automatically
2. Function calculates H2H data from all seasons via Sleeper API
3. Data is stored in Netlify Blobs (key-value storage)
4. When users visit the All-Time Stats page:
   - Frontend tries to fetch from `/api/h2h`
   - If available, uses server data (instant load)
   - If not available, falls back to local calculation with 7-day cache

### Updating Season Data

When a new season starts, update the `SEASONS` array in both:
- `netlify/functions/refresh-h2h.mjs` (line 8)
- `assets/js/league-data.js` (already has your current seasons)

Add the new season like this:

```javascript
const SEASONS = [
    { season: '2022', leagueId: '784850758166863872' },
    { season: '2023', leagueId: '918746033135255552' },
    { season: '2024', leagueId: '1257482235834028032' },
    { season: '2025', leagueId: 'YOUR_NEW_LEAGUE_ID' }  // Add new season here
];
```

Then redeploy:

```bash
npx netlify deploy --prod
```

## Monitoring

### Check Function Logs

```bash
npx netlify functions:log refresh-h2h
```

### Check if Data is Cached

Visit your site and open browser console. You should see:
```
Fetching H2H data from server...
Using server-calculated H2H data from: 2024-01-15T00:00:00.000Z
```

If you see "falling back to local calculation", the server data isn't available yet.

## Troubleshooting

### Scheduled Function Not Running

- Check the cron expression in `refresh-h2h.mjs` (line 95): `'0 0 * * 2'`
  - Format: `minute hour day month weekday`
  - `0 0 * * 2` = Every Tuesday at midnight UTC
- Verify the function deployed successfully in Netlify dashboard

### API Endpoint Returns 404

- Make sure `get-h2h.mjs` deployed correctly
- Check that the path is `/api/h2h` (configured in `get-h2h.mjs` line 23)
- Try accessing directly: `https://your-site.netlify.app/api/h2h`

### Local Testing Issues

If `netlify dev` has issues:
- Make sure all dependencies are installed: `npm install`
- Check Node.js version (should be 18+): `node --version`

## Cost

- **Netlify Free Tier includes**:
  - 125k function invocations/month (scheduled function runs ~4 times/month)
  - 100 GB bandwidth
  - Netlify Blobs: 1 GB storage

Your usage should be well within the free tier limits!

## Next Steps

Once deployed, your dashboard will:
- Automatically refresh H2H data every Tuesday at midnight
- Serve instant-loading All-Time Stats to all users
- Fall back to local calculation if needed (with 7-day cache)

Enjoy your fully automated fantasy football dashboard!
