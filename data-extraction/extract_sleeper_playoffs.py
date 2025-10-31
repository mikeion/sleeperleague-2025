#!/usr/bin/env python3
"""
Extract playoff results (champion and runner-up) from Sleeper API
"""
import requests
import json
from pathlib import Path

# Sleeper league IDs (walked backward from 2025)
LEAGUE_IDS = {
    2022: "859910378069577728",
    2023: "998364322315190272",
    2024: "1124841011114168320",
    2025: "1257482235834028032"
}

def get_username_from_roster(league_id, roster_id):
    """Get username for a roster ID"""
    # Get rosters
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    roster = next((r for r in rosters if r['roster_id'] == roster_id), None)

    if not roster:
        return None

    # Get user
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    user = next((u for u in users if u['user_id'] == roster['owner_id']), None)

    if not user:
        return None

    # Get username from profile
    profile = requests.get(f"https://api.sleeper.app/v1/user/{user['user_id']}").json()
    return profile.get('username') if profile else None

def parse_playoff_bracket(league_id, year):
    """Parse playoff bracket to find champion and runner-up"""
    # Get winners bracket
    bracket_url = f"https://api.sleeper.app/v1/league/{league_id}/winners_bracket"
    resp = requests.get(bracket_url)

    if resp.status_code != 200:
        print(f"  No playoff bracket for {year}")
        return None

    bracket = resp.json()

    # The championship game is typically the last matchup with round = 2 or the final matchup
    # We need to find the matchup where both teams came from semifinals

    # Build a mapping of matchup flow
    # Look for the final matchup (should have highest matchup id or be marked as championship)

    # Strategy: Find matchup where both participants came from winner's bracket semifinals
    # The championship is the matchup that determines the overall winner

    # Look at the bracket structure - find matchup with no "parent" (no other matchup feeds into it)
    matchup_sources = {}
    for matchup in bracket:
        m_id = matchup.get('m')
        t1_from = matchup.get('t1_from')
        t2_from = matchup.get('t2_from')

        if t1_from:
            matchup_sources[t1_from.get('w')] = True
        if t2_from:
            matchup_sources[t2_from.get('w')] = True

    # Find matchup that isn't a source for another matchup (the final)
    championship_matchup = None
    for matchup in bracket:
        m_id = matchup.get('m')
        if m_id not in matchup_sources:
            # This matchup doesn't feed into another - it's likely the championship
            championship_matchup = matchup
            break

    if not championship_matchup:
        # Fallback: last matchup in bracket
        championship_matchup = bracket[-1]

    # Extract champion and runner-up
    champion_roster = championship_matchup.get('w')
    team1 = championship_matchup.get('t1')
    team2 = championship_matchup.get('t2')

    # Runner-up is the other team in championship game
    runner_up_roster = team2 if champion_roster == team1 else team1

    champion_username = get_username_from_roster(league_id, champion_roster)
    runner_up_username = get_username_from_roster(league_id, runner_up_roster)

    return {
        'year': year,
        'champion': champion_username,
        'runner_up': runner_up_username,
        'champion_roster_id': champion_roster,
        'runner_up_roster_id': runner_up_roster
    }

def main():
    print("Extracting Sleeper playoff results...")

    playoff_results = []

    for year in sorted(LEAGUE_IDS.keys()):
        league_id = LEAGUE_IDS[year]
        print(f"\n{year} (League ID: {league_id})")

        result = parse_playoff_bracket(league_id, year)

        if result:
            playoff_results.append(result)
            print(f"  Champion: {result['champion']}")
            print(f"  Runner-up: {result['runner_up']}")
        else:
            print(f"  Could not determine playoff results")

    # Save to file
    output_file = Path(__file__).parent / 'output' / 'sleeper' / 'sleeper_playoff_results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(playoff_results, f, indent=2)

    print(f"\n✓ Playoff results saved to {output_file}")
    print(f"  Total years: {len(playoff_results)}")

if __name__ == "__main__":
    main()
