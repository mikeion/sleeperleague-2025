#!/usr/bin/env python3
"""
Extract Yahoo Fantasy data for 2020-2021 seasons
"""
from yahoofantasy import Context
import json
from pathlib import Path

# Yahoo league IDs for "Fat Man's League of 14"
LEAGUES = {
    2020: "399.l.114631",
    2021: "406.l.1061934"
}

ctx = Context()

def extract_yahoo_data(year, league_key):
    """Extract data for a Yahoo league"""
    print(f"\n{'='*60}")
    print(f"Extracting {year} data...")
    print(f"{'='*60}")

    try:
        # Get all leagues for the year
        leagues = ctx.get_leagues('nfl', year)

        # Find the correct league by key
        league = None
        for lg in leagues:
            if lg.league_key == league_key:
                league = lg
                break

        if not league:
            print(f"  Could not find league with key {league_key}")
            return None

        print(f"League: {league.name}")
        print(f"League Key: {league.league_key}")

        data = {
            'year': year,
            'league_key': league_key,
            'league_name': league.name,
            'standings': [],
            'teams': [],
            'matchups': {},
            'settings': {}
        }

        # Get standings
        print("  Fetching standings...")
        standings = league.standings()
        if standings:
            for team in standings:
                team_data = {
                    'team_key': str(team.team_key) if hasattr(team, 'team_key') else None,
                    'team_id': str(team.team_id) if hasattr(team, 'team_id') else None,
                    'name': str(team.name) if hasattr(team, 'name') else None,
                    'manager_name': str(team.manager.nickname) if hasattr(team, 'manager') and hasattr(team.manager, 'nickname') else None,
                    'wins': int(team.team_standings.outcome_totals.wins) if hasattr(team, 'team_standings') else 0,
                    'losses': int(team.team_standings.outcome_totals.losses) if hasattr(team, 'team_standings') else 0,
                    'ties': int(team.team_standings.outcome_totals.ties) if hasattr(team, 'team_standings') else 0,
                    'points_for': float(team.team_standings.points_for) if hasattr(team, 'team_standings') else 0.0,
                    'points_against': float(team.team_standings.points_against) if hasattr(team, 'team_standings') else 0.0,
                    'rank': int(team.team_standings.rank) if hasattr(team, 'team_standings') else None
                }
                data['standings'].append(team_data)
                data['teams'].append(team_data)
                print(f"    {team_data['name']}: {team_data['wins']}-{team_data['losses']} ({team_data['points_for']} pts)")

        # Try to get playoff bracket/championship
        print("  Checking for playoff data...")
        try:
            # The champion is typically the #1 ranked team after playoffs
            if data['standings']:
                champion = data['standings'][0]  # First place
                data['champion'] = {
                    'team_name': champion['name'],
                    'manager_name': champion['manager_name'],
                    'team_key': champion['team_key']
                }
                print(f"  Champion: {champion['name']} ({champion['manager_name']})")
        except Exception as e:
            print(f"  Could not determine champion: {e}")

        return data

    except Exception as e:
        print(f"Error extracting {year} data: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    all_data = {}

    for year, league_key in LEAGUES.items():
        data = extract_yahoo_data(year, league_key)
        if data:
            all_data[year] = data

            # Save individual year
            output_dir = Path(__file__).parent / 'output' / 'yahoo'
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f'yahoo_{year}.json'
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  Saved to {output_file}")

    # Save combined
    if all_data:
        combined_file = Path(__file__).parent / 'output' / 'yahoo' / 'yahoo_all_years.json'
        with open(combined_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        print(f"\n✓ All data saved to {combined_file}")

if __name__ == "__main__":
    main()
