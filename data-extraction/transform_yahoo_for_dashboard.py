#!/usr/bin/env python3
"""
Transform Yahoo Fantasy data into dashboard format
"""
import json
from pathlib import Path

# Load Yahoo data
yahoo_data_file = Path(__file__).parent / 'output' / 'yahoo' / 'yahoo_all_years.json'
with open(yahoo_data_file, 'r') as f:
    yahoo_data = json.load(f)

# Load team name mapping
mapping_file = Path(__file__).parent / 'yahoo_team_mapping.json'
with open(mapping_file, 'r') as f:
    team_mapping = json.load(f)

# Load owner mapping for display names
owner_mapping_file = Path(__file__).parent / 'owner_mapping.json'
with open(owner_mapping_file, 'r') as f:
    owner_mapping_data = json.load(f)

# Create reverse lookup: sleeper_username -> display_name
username_to_display = {}
mfl_to_sleeper = owner_mapping_data.get('mfl_to_sleeper', {})
for franchise_id, owner_info in mfl_to_sleeper.items():
    username = owner_info.get('sleeper_username', '').lower()
    display_name = owner_info.get('real_name', 'Unknown')
    if username and username != 'unknown':
        username_to_display[username] = display_name

def get_display_name(username):
    """Get display name from username"""
    return username_to_display.get(username.lower(), username)

def transform_yahoo_data():
    """Transform Yahoo data to dashboard format"""
    dashboard_data = {
        'platform': 'Yahoo',
        'years': [2020, 2021],
        'champions': [],
        'manager_stats': {}
    }

    # Process each year
    for year_str, year_data in yahoo_data.items():
        year = int(year_str)
        year_mapping = team_mapping.get(str(year), {})

        # Add champion and runner-up (rank 2)
        if 'champion' in year_data:
            champ_team_name = year_data['champion']['team_name']
            champ_username = year_mapping.get(champ_team_name, 'unknown')

            # Find runner-up (rank 2 in standings)
            runner_up_team = next((t for t in year_data['standings'] if t['rank'] == 2), None)
            runner_up_display = 'Unknown'
            if runner_up_team:
                runner_up_username = year_mapping.get(runner_up_team['name'], 'unknown')
                runner_up_display = get_display_name(runner_up_username)

            dashboard_data['champions'].append({
                'year': year,
                'platform': 'Yahoo',
                'champion': {
                    'username': champ_username,
                    'display_name': get_display_name(champ_username),
                    'team_name': champ_team_name
                },
                'runner_up': {
                    'display_name': runner_up_display
                }
            })

        # Process standings
        for team in year_data['standings']:
            team_name = team['name']
            username = year_mapping.get(team_name, 'unknown')

            if username == 'unknown':
                print(f"Warning: No mapping found for team '{team_name}' in {year}")
                continue

            # Normalize username to lowercase
            username = username.lower()

            # Initialize manager if not exists
            if username not in dashboard_data['manager_stats']:
                dashboard_data['manager_stats'][username] = {
                    'username': username,
                    'display_name': get_display_name(username),
                    'years': {},
                    'totals': {
                        'wins': 0,
                        'losses': 0,
                        'ties': 0,
                        'points_for': 0.0,
                        'points_against': 0.0,
                        'championships': 0
                    }
                }

            manager = dashboard_data['manager_stats'][username]

            # Add year data
            manager['years'][str(year)] = {
                'wins': team['wins'],
                'losses': team['losses'],
                'ties': team['ties'],
                'points_for': team['points_for'],
                'points_against': team['points_against'],
                'champion': username == year_mapping.get(
                    year_data.get('champion', {}).get('team_name', ''), ''
                ).lower()
            }

            # Update totals
            manager['totals']['wins'] += team['wins']
            manager['totals']['losses'] += team['losses']
            manager['totals']['ties'] += team['ties']
            manager['totals']['points_for'] += team['points_for']
            manager['totals']['points_against'] += team['points_against']

            # Check if champion
            is_champion = (username == year_mapping.get(
                year_data.get('champion', {}).get('team_name', ''), ''
            ).lower())

            # Check if runner-up
            is_runner_up = (username == year_mapping.get(
                year_data.get('runner_up', {}).get('team_name', ''), ''
            ).lower())

            manager['years'][str(year)]['champion'] = is_champion
            manager['years'][str(year)]['runner_up'] = is_runner_up

            if is_champion:
                manager['totals']['championships'] += 1

    # Calculate placements for each year
    for year in dashboard_data['years']:
        # Get all managers who played that year
        year_standings = []
        for username, stats in dashboard_data['manager_stats'].items():
            if str(year) in stats['years']:
                year_data = stats['years'][str(year)]
                year_standings.append({
                    'username': username,
                    'wins': year_data['wins'],
                    'points_for': year_data['points_for']
                })

        # Sort by wins DESC, then points_for DESC
        year_standings.sort(key=lambda x: (x['wins'], x['points_for']), reverse=True)

        # Assign placements
        total_teams = len(year_standings)
        for placement, standing in enumerate(year_standings, 1):
            dashboard_data['manager_stats'][standing['username']]['years'][str(year)]['finish'] = placement
            dashboard_data['manager_stats'][standing['username']]['years'][str(year)]['total_teams'] = total_teams

    # Convert manager_stats dict to list
    dashboard_data['manager_stats'] = list(dashboard_data['manager_stats'].values())

    return dashboard_data

def main():
    print("Transforming Yahoo data for dashboard...")

    dashboard_data = transform_yahoo_data()

    # Save to output
    output_file = Path(__file__).parent / 'output' / 'yahoo' / 'yahoo_dashboard_data.json'
    with open(output_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"\n✓ Yahoo dashboard data saved to {output_file}")

    # Print summary
    print(f"\nYahoo Data Summary:")
    print(f"  Years: {dashboard_data['years']}")
    print(f"  Managers: {len(dashboard_data['manager_stats'])}")
    print(f"\nChampions:")
    for champ in dashboard_data['champions']:
        print(f"  {champ['year']}: {champ['champion']['display_name']} ({champ['champion']['username']})")

    print(f"\nManager Stats:")
    for manager in sorted(dashboard_data['manager_stats'], key=lambda x: x['display_name']):
        total_games = manager['totals']['wins'] + manager['totals']['losses'] + manager['totals']['ties']
        print(f"  {manager['display_name']:20} - {manager['totals']['wins']}-{manager['totals']['losses']}-{manager['totals']['ties']} ({total_games} games)")

if __name__ == "__main__":
    main()
