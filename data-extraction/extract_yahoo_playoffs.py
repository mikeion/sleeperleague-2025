#!/usr/bin/env python3
"""
Extract Yahoo playoff bracket data
Yahoo API docs: https://developer.yahoo.com/fantasysports/guide/
"""

import json
from pathlib import Path

try:
    from yahoofantasy import Context
except ImportError:
    print("ERROR: yahoofantasy library not installed")
    print("Install with: pip install yahoofantasy")
    exit(1)

# Yahoo Configuration
LEAGUES = {
    2020: "114631",
    2021: "1061934"
}

def get_playoff_results(year, league_id):
    """Get playoff results for a given year"""
    print(f'\n{"="*80}')
    print(f'{year} PLAYOFFS')
    print('='*80)

    try:
        # Initialize context
        ctx = Context()

        # Get league
        leagues = ctx.get_leagues('nfl', [year])
        league = None
        for l in leagues:
            if str(l.league_id) == str(league_id):
                league = l
                break

        if not league:
            print(f"Could not find league {league_id}")
            return None

        # Check league attributes for playoff data
        print("\nLeague attributes:")
        for attr in dir(league):
            if not attr.startswith('_') and 'playoff' in attr.lower():
                print(f"  {attr}: {getattr(league, attr, 'N/A')}")

        # Get standings (which includes playoff results)
        standings = league.standings()
        print(f"\nStandings for {year}:")

        results = {
            'year': year,
            'champion': None,
            'runner_up': None,
            'third_place': None,
            'sacko': None
        }

        # Try to extract playoff results from standings
        # Yahoo typically shows final standings after playoffs
        if standings and len(standings) >= 2:
            # Champion is usually 1st in final standings
            champ_team = standings[0]
            runner_up_team = standings[1] if len(standings) > 1 else None

            print(f"\n1st Place: {champ_team.get('name', 'Unknown')}")
            if runner_up_team:
                print(f"2nd Place: {runner_up_team.get('name', 'Unknown')}")

            # Map to actual names from owner_mapping
            results['champion'] = champ_team.get('name', 'Unknown')
            results['runner_up'] = runner_up_team.get('name', 'Unknown') if runner_up_team else None

            # Check if there's a 3rd place team
            if len(standings) > 2:
                third_team = standings[2]
                print(f"3rd Place: {third_team.get('name', 'Unknown')}")
                results['third_place'] = third_team.get('name', 'Unknown')

            # Last place (Sacko) is last in standings
            if len(standings) >= 3:
                last_team = standings[-1]
                print(f"Last Place (Sacko): {last_team.get('name', 'Unknown')}")
                results['sacko'] = last_team.get('name', 'Unknown')

        # Try to get playoff bracket data directly
        print("\n\nAttempting to get playoff bracket data...")
        try:
            # The yahoofantasy library might have a scoreboard or matchups method
            # that includes playoff rounds
            if hasattr(league, 'matchups'):
                print("League has matchups method")
                # Get playoff weeks (typically weeks 15-16 or 15-17)
                playoff_weeks = [15, 16, 17]
                for week in playoff_weeks:
                    try:
                        matchups = league.matchups(week=week)
                        if matchups:
                            print(f"\nWeek {week} matchups:")
                            for m in matchups:
                                print(f"  {m}")
                    except Exception as e:
                        print(f"  Week {week}: {e}")

            if hasattr(league, 'teams'):
                teams = league.teams()
                print(f"\nTeams ({len(teams)} total):")
                for team in teams[:5]:  # Show first 5
                    print(f"  {team.get('name', 'Unknown')}")

        except Exception as e:
            print(f"Error getting playoff data: {e}")

        return results

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    all_results = []

    for year, league_id in LEAGUES.items():
        results = get_playoff_results(year, league_id)
        if results:
            all_results.append(results)

    # Save results
    output_file = Path('output/yahoo/yahoo_playoff_results.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f'\n\n{"="*80}')
    print(f'Playoff results saved to {output_file}')
    print('='*80)
    print('\nSummary:')
    for result in all_results:
        print(f"\n{result['year']}:")
        if result['champion']:
            print(f"  🏆 Champion: {result['champion']}")
        if result['runner_up']:
            print(f"  🥈 Runner-up: {result['runner_up']}")
        if result['third_place']:
            print(f"  🥉 3rd Place: {result['third_place']}")
        if result['sacko']:
            print(f"  💩 Sacko: {result['sacko']}")
