#!/usr/bin/env python3
"""
Extract historical fantasy football data from Yahoo Fantasy (2020-2021)
League IDs: 2021: 1061934, 2020: 114631

This script requires the yahoofantasy library and OAuth authentication.
Install: pip install yahoofantasy
Setup: yahoofantasy login (requires Yahoo Developer App)
"""

import json
from pathlib import Path

try:
    from yahoofantasy import Context, League
except ImportError:
    print("ERROR: yahoofantasy library not installed")
    print("Install with: pip install yahoofantasy")
    print("\nThen authenticate with: yahoofantasy login")
    print("(This requires a Yahoo Developer App - see README)")
    exit(1)

# Yahoo Configuration
LEAGUES = {
    2020: "114631",
    2021: "1061934"
}

def extract_league_data(year, league_id):
    """Extract all relevant data for a given year"""
    print(f"\nExtracting Yahoo data for {year} (League ID: {league_id})...")

    try:
        # Initialize context
        ctx = Context()

        # Get all NFL leagues for this year
        leagues = ctx.get_leagues('nfl', [year])

        # Find our specific league by ID
        league = None
        for l in leagues:
            if str(l.league_id) == str(league_id):
                league = l
                break

        if not league:
            print(f"  Could not find league {league_id} in {year}")
            print(f"  Available leagues: {[l.league_id + ' - ' + l.name for l in leagues]}")
            return None

        data = {
            'year': year,
            'league_id': league_id,
            'league_info': {},
            'teams': [],
            'standings': [],
            'matchups': {},
            'transactions': [],
            'draft_results': []
        }

        # Get league info
        print(f"  Fetching league info...")
        data['league_info'] = {
            'name': league.name,
            'num_teams': league.num_teams,
            'season': year,
            'league_key': league.league_key,
            'scoring_type': league.scoring_type,
            'start_week': league.start_week,
            'end_week': league.end_week,
            'current_week': league.current_week
        }

        # Get teams
        print(f"  Fetching teams...")
        teams = league.teams()
        for team in teams:
            data['teams'].append({
                'team_id': team.team_id,
                'team_key': team.team_key,
                'name': team.name,
                'manager_name': team.manager.nickname if hasattr(team, 'manager') else None,
                'wins': team.wins if hasattr(team, 'wins') else None,
                'losses': team.losses if hasattr(team, 'losses') else None,
                'ties': team.ties if hasattr(team, 'ties') else None,
                'points_for': team.points_for if hasattr(team, 'points_for') else None,
                'points_against': team.points_against if hasattr(team, 'points_against') else None
            })

        # Get standings
        print(f"  Fetching standings...")
        standings = league.standings()
        for idx, team in enumerate(standings, 1):
            data['standings'].append({
                'rank': idx,
                'team_id': team.team_id,
                'team_name': team.name,
                'wins': team.wins,
                'losses': team.losses,
                'ties': team.ties,
                'points_for': team.points_for,
                'points_against': team.points_against
            })

        # Get matchups for each week
        print(f"  Fetching matchups...")
        start_week = league.start_week if hasattr(league, 'start_week') else 1
        end_week = league.end_week if hasattr(league, 'end_week') else 14

        for week in range(start_week, end_week + 1):
            try:
                matchups = league.matchups(week)
                data['matchups'][f'week_{week}'] = []
                for matchup in matchups:
                    data['matchups'][f'week_{week}'].append({
                        'week': week,
                        'team1': matchup.team1.name if hasattr(matchup, 'team1') else None,
                        'team1_score': matchup.team1_score if hasattr(matchup, 'team1_score') else None,
                        'team2': matchup.team2.name if hasattr(matchup, 'team2') else None,
                        'team2_score': matchup.team2_score if hasattr(matchup, 'team2_score') else None
                    })
            except Exception as e:
                print(f"    Warning: Could not fetch week {week} matchups: {e}")

        # Get transactions
        print(f"  Fetching transactions...")
        try:
            transactions = league.transactions()
            for txn in transactions:
                data['transactions'].append({
                    'type': txn.type if hasattr(txn, 'type') else None,
                    'timestamp': txn.timestamp if hasattr(txn, 'timestamp') else None,
                    'status': txn.status if hasattr(txn, 'status') else None
                })
        except Exception as e:
            print(f"    Warning: Could not fetch transactions: {e}")

        # Get draft results
        print(f"  Fetching draft results...")
        try:
            draft = league.draft_results()
            for pick in draft:
                data['draft_results'].append({
                    'pick': pick.pick if hasattr(pick, 'pick') else None,
                    'round': pick.round if hasattr(pick, 'round') else None,
                    'team': pick.team.name if hasattr(pick, 'team') else None,
                    'player': pick.player.name if hasattr(pick, 'player') else None
                })
        except Exception as e:
            print(f"    Warning: Could not fetch draft results: {e}")

        return data

    except Exception as e:
        print(f"  ERROR: Failed to extract data for {year}: {e}")
        print(f"  This might be because:")
        print(f"    1. You haven't authenticated (run: yahoofantasy login)")
        print(f"    2. The league is private and you don't have access")
        print(f"    3. The league ID is incorrect")
        return None

def save_data(data, year):
    """Save extracted data to JSON file"""
    if data is None:
        return

    output_dir = Path(__file__).parent / 'output' / 'yahoo'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f'yahoo_{year}.json'

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  ✓ Saved to {output_file}")

def main():
    print("=" * 60)
    print("Yahoo Fantasy Data Extraction")
    print("=" * 60)
    print("\nNOTE: This requires Yahoo OAuth authentication.")
    print("If you haven't already, run: yahoofantasy login")
    print("=" * 60)

    all_data = {}

    for year, league_id in LEAGUES.items():
        data = extract_league_data(year, league_id)
        if data:
            all_data[year] = data
            save_data(data, year)

    if all_data:
        # Save combined data
        output_dir = Path(__file__).parent / 'output' / 'yahoo'
        combined_file = output_dir / 'yahoo_all_years.json'

        with open(combined_file, 'w') as f:
            json.dump(all_data, f, indent=2)

        print(f"\n✓ All data saved to {output_dir}")
        print(f"✓ Combined file: {combined_file}")
    else:
        print("\n✗ No data was extracted. Check errors above.")

if __name__ == "__main__":
    main()
