#!/usr/bin/env python3
"""
Extract playoff results (champion, runner-up, 3rd, 4th, and Sacko) from Sleeper API
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
    """Parse playoff bracket to find champion, runner-up, 3rd, 4th, and Sacko"""
    # Get winners and losers brackets
    winners_url = f"https://api.sleeper.app/v1/league/{league_id}/winners_bracket"
    losers_url = f"https://api.sleeper.app/v1/league/{league_id}/losers_bracket"

    winners_resp = requests.get(winners_url)
    losers_resp = requests.get(losers_url)

    if winners_resp.status_code != 200:
        print(f"  No playoff bracket for {year}")
        return None

    winners_bracket = winners_resp.json()
    losers_bracket = losers_resp.json() if losers_resp.status_code == 200 else []

    results = {
        'year': year,
        'champion': None,
        'runner_up': None,
        'third_place': None,
        'fourth_place': None,
        'fifth_place': None,
        'sixth_place': None,
        'seventh_place': None,
        'eighth_place': None,
        'sacko': None
    }

    # Parse winners bracket - look for placement markers
    for matchup in winners_bracket:
        p = matchup.get('p')  # placement indicator

        if p == 1:  # Championship game
            champion_roster = matchup.get('w')
            team1 = matchup.get('t1')
            team2 = matchup.get('t2')
            loser_roster = team2 if champion_roster == team1 else team1

            results['champion'] = get_username_from_roster(league_id, champion_roster)
            results['runner_up'] = get_username_from_roster(league_id, loser_roster)

        elif p == 3:  # 3rd place game
            winner_roster = matchup.get('w')
            team1 = matchup.get('t1')
            team2 = matchup.get('t2')
            loser_roster = team2 if winner_roster == team1 else team1

            results['third_place'] = get_username_from_roster(league_id, winner_roster)
            results['fourth_place'] = get_username_from_roster(league_id, loser_roster)

        elif p == 5:  # 5th place game
            winner_roster = matchup.get('w')
            team1 = matchup.get('t1')
            team2 = matchup.get('t2')
            loser_roster = team2 if winner_roster == team1 else team1

            results['fifth_place'] = get_username_from_roster(league_id, winner_roster)
            results['sixth_place'] = get_username_from_roster(league_id, loser_roster)

        elif p == 7:  # 7th place game
            winner_roster = matchup.get('w')
            team1 = matchup.get('t1')
            team2 = matchup.get('t2')
            loser_roster = team2 if winner_roster == team1 else team1

            results['seventh_place'] = get_username_from_roster(league_id, winner_roster)
            results['eighth_place'] = get_username_from_roster(league_id, loser_roster)

    # Parse losers bracket for Sacko
    # The Toilet Bowl championship (p=1 in losers bracket): winner gets the Sacko trophy
    # The "winner" of the losers bracket final "wins" last place
    for matchup in losers_bracket:
        p = matchup.get('p')

        if p == 1:  # Toilet Bowl final - winner gets the Sacko (last place trophy)
            winner_roster = matchup.get('w')
            results['sacko'] = get_username_from_roster(league_id, winner_roster)

    # Validate we got at least champion and runner-up
    if not results['champion'] or not results['runner_up']:
        print(f"  Could not identify champion and runner-up")
        return None

    return results

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
            if result['third_place']:
                print(f"  3rd Place: {result['third_place']}")
            if result['fourth_place']:
                print(f"  4th Place: {result['fourth_place']}")
            if result['fifth_place']:
                print(f"  5th Place: {result['fifth_place']}")
            if result['sixth_place']:
                print(f"  6th Place: {result['sixth_place']}")
            if result['seventh_place']:
                print(f"  7th Place: {result['seventh_place']}")
            if result['eighth_place']:
                print(f"  8th Place: {result['eighth_place']}")
            if result['sacko']:
                print(f"  Sacko: {result['sacko']}")
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
