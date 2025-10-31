#!/usr/bin/env python3
"""
Extract historical fantasy football data from MyFantasyLeague (2016-2019)
League ID: 59111
"""

import requests
import json
from pathlib import Path

# MFL Configuration
LEAGUE_ID = "59111"
YEARS = [2016, 2017, 2018, 2019]
BASE_URL = "https://api.myfantasyleague.com/{year}/export"

def fetch_mfl_data(year, export_type, params=None):
    """Fetch data from MFL API"""
    url = BASE_URL.format(year=year)

    # Default params
    all_params = {
        'TYPE': export_type,
        'L': LEAGUE_ID,
        'JSON': '1'  # Request JSON format
    }

    # Add any additional params
    if params:
        all_params.update(params)

    try:
        response = requests.get(url, params=all_params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {export_type} for {year}: {e}")
        return None

def extract_league_data(year):
    """Extract all relevant data for a given year"""
    print(f"\nExtracting data for {year}...")

    data = {
        'year': year,
        'league': None,
        'league_standings': None,
        'rosters': None,
        'players': None,
        'schedule': None,
        'transactions': None,
        'draft_results': None
    }

    # Fetch league info
    print(f"  Fetching league info...")
    data['league'] = fetch_mfl_data(year, 'league')

    # Fetch standings
    print(f"  Fetching standings...")
    data['league_standings'] = fetch_mfl_data(year, 'leagueStandings')

    # Fetch rosters
    print(f"  Fetching rosters...")
    data['rosters'] = fetch_mfl_data(year, 'rosters')

    # Fetch players
    print(f"  Fetching players...")
    data['players'] = fetch_mfl_data(year, 'players')

    # Fetch schedule/matchups
    print(f"  Fetching schedule...")
    data['schedule'] = fetch_mfl_data(year, 'leagueSchedules')

    # Fetch transactions
    print(f"  Fetching transactions...")
    data['transactions'] = fetch_mfl_data(year, 'transactions')

    # Fetch draft results
    print(f"  Fetching draft results...")
    data['draft_results'] = fetch_mfl_data(year, 'draftResults')

    return data

def save_data(data, year):
    """Save extracted data to JSON file"""
    output_dir = Path(__file__).parent / 'output' / 'mfl'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f'mfl_{year}.json'

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  Saved to {output_file}")

def main():
    print("=" * 60)
    print("MyFantasyLeague Data Extraction")
    print("League ID: 59111")
    print("Years: 2016-2019")
    print("=" * 60)

    all_data = {}

    for year in YEARS:
        data = extract_league_data(year)
        all_data[year] = data
        save_data(data, year)

    # Save combined data
    output_dir = Path(__file__).parent / 'output' / 'mfl'
    combined_file = output_dir / 'mfl_all_years.json'

    with open(combined_file, 'w') as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✓ All data saved to {output_dir}")
    print(f"✓ Combined file: {combined_file}")

if __name__ == "__main__":
    main()
