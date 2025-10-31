# Historical Data Extraction Scripts

Scripts to extract fantasy football data from previous platforms (Yahoo and MyFantasyLeague) to combine with current Sleeper data.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## MyFantasyLeague (2016-2019)

Extract data from MFL league ID: 59111

```bash
python extract_mfl.py
```

This will create JSON files in `output/mfl/` for each year (2016-2019).

**Note:** If the league was private, you may need to provide authentication. The script will first try to access as a public league.

## Yahoo Fantasy (2020-2021)

Extract data from Yahoo leagues:
- 2021: League ID 1061934
- 2020: League ID 114631

### Yahoo Authentication Setup

Yahoo requires OAuth authentication. You'll need to:

1. **Create a Yahoo Developer App**
   - Go to https://developer.yahoo.com/apps/create/
   - Sign in with your Yahoo account
   - Create a new app:
     - Application Name: "Fantasy Dashboard" (or whatever you want)
     - Application Type: "Web Application"
     - Redirect URI: `http://localhost:8000`
     - API Permissions: Check "Fantasy Sports"
   - Save the app and note your **Client ID** and **Client Secret**

2. **Authenticate with the yahoofantasy CLI**
   ```bash
   yahoofantasy login
   ```
   - Enter your Client ID and Client Secret when prompted
   - This will open a browser window to authorize the app
   - The credentials will be saved locally

3. **Run the extraction script**
   ```bash
   python extract_yahoo.py
   ```

This will create JSON files in `output/yahoo/` for each year (2020-2021).

## Output

All extracted data is saved as JSON files in the `output/` directory:

```
output/
├── mfl/
│   ├── mfl_2016.json
│   ├── mfl_2017.json
│   ├── mfl_2018.json
│   ├── mfl_2019.json
│   └── mfl_all_years.json
└── yahoo/
    ├── yahoo_2020.json
    ├── yahoo_2021.json
    └── yahoo_all_years.json
```

## Next Steps

After extracting the data:
1. Transform the data to match the Sleeper format
2. Combine with current Sleeper data
3. Update the dashboard to display all historical years
