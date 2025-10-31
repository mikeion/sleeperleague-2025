#!/usr/bin/env python3
"""
Find MFL champions for each year based on standings/playoff data
"""

import json
from pathlib import Path

# Load owner mapping
with open('owner_mapping.json', 'r') as f:
    mapping = json.load(f)['mfl_to_sleeper']

for year in [2016, 2017, 2018, 2019]:
    print(f"\n{'='*80}")
    print(f"{year} SEASON")
    print('='*80)

    # Load MFL data
    with open(f'output/mfl/mfl_{year}.json', 'r') as f:
        data = json.load(f)

    # Get standings
    standings_data = data.get('league_standings', {})
    if 'error' in standings_data:
        print(f"ERROR: Could not fetch standings for {year}")
        continue

    standings = standings_data.get('leagueStandings', {}).get('franchise', [])
    franchises = {f['id']: f['name'] for f in data['league']['league']['franchises']['franchise']}

    # Sort by wins (regular season)
    sorted_standings = sorted(standings, key=lambda x: (int(x.get('h2hw', 0)), float(x.get('pf', 0))), reverse=True)

    print(f"\nTop 5 Regular Season Finishers:")
    for i, team in enumerate(sorted_standings[:5], 1):
        fid = team['id']
        owner = mapping.get(fid, {}).get('real_name', 'Unknown')
        print(f"  {i}. {owner:20} ({franchises.get(fid, 'Unknown')[:40]})")
        print(f"     Record: {team.get('h2hwlt', 'N/A'):10} | PF: {team.get('pf', 'N/A')}")

    print(f"\nCHAMPION: (Please verify from your league records)")
    print(f"  Most likely: {mapping.get(sorted_standings[0]['id'], {}).get('real_name', 'Unknown')}")
