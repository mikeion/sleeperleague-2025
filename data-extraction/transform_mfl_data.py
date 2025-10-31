#!/usr/bin/env python3
"""
Transform MFL data to match Sleeper-like format for dashboard integration
"""

import json
from pathlib import Path
from collections import defaultdict

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def transform_mfl_to_common_format():
    """Transform MFL data to common format compatible with dashboard"""

    # Load owner mapping
    owner_mapping = load_json(Path(__file__).parent / 'owner_mapping.json')
    mfl_to_sleeper = owner_mapping['mfl_to_sleeper']

    years = [2016, 2017, 2018, 2019]
    all_seasons = {}

    for year in years:
        print(f"\nTransforming {year} data...")

        # Load MFL data
        mfl_data = load_json(Path(__file__).parent / 'output' / 'mfl' / f'mfl_{year}.json')

        season_data = {
            'year': year,
            'platform': 'MyFantasyLeague',
            'league_id': '59111',
            'teams': [],
            'standings': [],
            'total_weeks': 14,  # Standard NFL regular season
            'playoff_start_week': 15
        }

        # Get franchises
        franchises = mfl_data['league']['league']['franchises']['franchise']

        # Transform team data
        for franchise in franchises:
            fid = franchise.get('id')
            mapping = mfl_to_sleeper.get(fid, {})

            team = {
                'franchise_id': fid,
                'team_name': franchise.get('name'),
                'sleeper_username': mapping.get('sleeper_username', 'unknown'),
                'sleeper_display_name': mapping.get('sleeper_display_name', 'unknown'),
                'real_name': mapping.get('real_name', ''),
                'logo': franchise.get('logo', ''),
                'icon': franchise.get('icon', ''),
                'division': franchise.get('division', '00')
            }

            season_data['teams'].append(team)

        print(f"  ✓ Transformed {len(season_data['teams'])} teams")

        # TODO: Transform standings (need to parse league_standings data)
        # TODO: Transform weekly matchups (need to parse schedule data)
        # TODO: Transform transactions

        all_seasons[year] = season_data

    return all_seasons

def save_transformed_data(data):
    """Save transformed data to JSON"""
    output_dir = Path(__file__).parent / 'output' / 'transformed'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save individual years
    for year, season_data in data.items():
        output_file = output_dir / f'mfl_{year}_transformed.json'
        with open(output_file, 'w') as f:
            json.dump(season_data, f, indent=2)
        print(f"Saved: {output_file}")

    # Save combined file
    combined_file = output_dir / 'mfl_all_transformed.json'
    with open(combined_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved combined: {combined_file}")

def main():
    print("=" * 80)
    print("MFL Data Transformation")
    print("=" * 80)

    transformed_data = transform_mfl_to_common_format()
    save_transformed_data(transformed_data)

    print("\n✓ Transformation complete!")
    print("\nNext steps:")
    print("1. Extract Yahoo data (2020-2021)")
    print("2. Transform Yahoo data to same format")
    print("3. Combine all historical data (MFL + Yahoo + Sleeper)")
    print("4. Update dashboard to display all years")

if __name__ == "__main__":
    main()
