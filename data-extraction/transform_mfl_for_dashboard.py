#!/usr/bin/env python3
"""
Transform MFL data into a format compatible with the dashboard
Creates a JSON file that can be loaded alongside Sleeper data
"""
import json
from pathlib import Path

# Load owner mapping
with open('owner_mapping.json', 'r') as f:
    owner_map = json.load(f)
    mfl_to_sleeper = owner_map['mfl_to_sleeper']

# Load MFL champions
with open('output/mfl/mfl_champions.json', 'r') as f:
    champions_data = json.load(f)

# Load MFL data for all years
mfl_years = {}
for year in [2016, 2017, 2018, 2019]:
    with open(f'output/mfl/mfl_{year}.json', 'r') as f:
        mfl_years[year] = json.load(f)

def get_sleeper_username(franchise_id):
    """Map MFL franchise ID to Sleeper username"""
    franchise_id = str(franchise_id).zfill(4)
    if franchise_id in mfl_to_sleeper:
        username = mfl_to_sleeper[franchise_id].get('sleeper_username', 'unknown')
        # Normalize to lowercase for consistent matching
        return username.lower() if username != 'unknown' else username
    return 'unknown'

def get_display_name(franchise_id):
    """Get display name for a franchise"""
    franchise_id = str(franchise_id).zfill(4)
    if franchise_id in mfl_to_sleeper:
        return mfl_to_sleeper[franchise_id].get('real_name', 'Unknown')
    return 'Unknown'

# Transform champions data
transformed_champions = []
for champ in champions_data:
    transformed_champions.append({
        'year': champ['year'],
        'platform': 'MFL',
        'champion': {
            'username': get_sleeper_username(champ['champion_id']),
            'display_name': champ['champion'],
            'franchise_id': champ['champion_id']
        },
        'runner_up': {
            'display_name': champ['runner_up']
        },
        'championship_score': {
            'champion': float(champ['champion_score']),
            'runner_up': float(champ['runner_up_score'])
        }
    })

# Transform manager stats (wins, losses, points for, championships, etc.)
manager_stats = {}

for year, data in mfl_years.items():
    if 'league_standings' in data and 'leagueStandings' in data['league_standings']:
        standings = data['league_standings']['leagueStandings']
        if 'franchise' in standings:
            franchises = standings['franchise']
            if not isinstance(franchises, list):
                franchises = [franchises]

            for franchise in franchises:
                fid = franchise.get('id', '')
                username = get_sleeper_username(fid)
                display_name = get_display_name(fid)

                if username not in manager_stats:
                    manager_stats[username] = {
                        'username': username,
                        'display_name': display_name,
                        'years': {},
                        'totals': {
                            'wins': 0,
                            'losses': 0,
                            'ties': 0,
                            'points_for': 0.0,
                            'points_against': 0.0,
                            'championships': 0,
                            'seasons_played': 0
                        }
                    }

                # Parse season stats
                wins = int(franchise.get('h2hw', 0))
                losses = int(franchise.get('h2hl', 0))
                ties = int(franchise.get('h2ht', 0))
                points_for = float(franchise.get('pf', 0))
                points_against = float(franchise.get('pa', 0))

                # Check if they won championship this year
                is_champion = any(c['year'] == year and c['champion_id'] == fid for c in champions_data)

                manager_stats[username]['years'][year] = {
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'points_for': points_for,
                    'points_against': points_against,
                    'champion': is_champion
                }

                # Update totals
                manager_stats[username]['totals']['wins'] += wins
                manager_stats[username]['totals']['losses'] += losses
                manager_stats[username]['totals']['ties'] += ties
                manager_stats[username]['totals']['points_for'] += points_for
                manager_stats[username]['totals']['points_against'] += points_against
                manager_stats[username]['totals']['seasons_played'] += 1
                if is_champion:
                    manager_stats[username]['totals']['championships'] += 1

# Calculate win percentages
for username, stats in manager_stats.items():
    total_games = stats['totals']['wins'] + stats['totals']['losses'] + stats['totals']['ties']
    if total_games > 0:
        stats['totals']['win_percentage'] = round(stats['totals']['wins'] / total_games, 3)
    else:
        stats['totals']['win_percentage'] = 0.0

# Create final output
output = {
    'platform': 'MFL',
    'years': [2016, 2017, 2018, 2019],
    'champions': transformed_champions,
    'manager_stats': list(manager_stats.values())
}

# Save to output directory
output_file = Path(__file__).parent / 'output' / 'mfl' / 'mfl_dashboard_data.json'
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f'✓ MFL dashboard data saved to {output_file}')
print(f'\nSummary:')
print(f'  Years: {", ".join(map(str, output["years"]))}')
print(f'  Champions: {len(output["champions"])}')
print(f'  Managers: {len(output["manager_stats"])}')
print(f'\nChampions:')
for champ in output['champions']:
    print(f'  {champ["year"]}: {champ["champion"]["display_name"]}')

print(f'\nTop 5 Managers by Total Points:')
sorted_managers = sorted(output['manager_stats'], key=lambda x: x['totals']['points_for'], reverse=True)
for i, mgr in enumerate(sorted_managers[:5], 1):
    print(f'  {i}. {mgr["display_name"]}: {mgr["totals"]["points_for"]:.2f} pts ({mgr["totals"]["wins"]}-{mgr["totals"]["losses"]})')
