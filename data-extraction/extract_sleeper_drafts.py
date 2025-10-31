#!/usr/bin/env python3
"""
Extract draft positions from Sleeper API
"""
import requests
import json
from pathlib import Path

# Sleeper league IDs
LEAGUE_IDS = {
    2022: "859910378069577728",
    2023: "998364322315190272",
    2024: "1124841011114168320",
    2025: "1257482235834028032"
}

def get_username_from_roster(league_id, roster_id):
    """Get username for a roster ID"""
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    roster = next((r for r in rosters if r['roster_id'] == roster_id), None)

    if not roster:
        return None

    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    user = next((u for u in users if u['user_id'] == roster['owner_id']), None)

    if not user:
        return None

    profile = requests.get(f"https://api.sleeper.app/v1/user/{user['user_id']}").json()
    return profile.get('username') if profile else None

def extract_draft_order(league_id, year):
    """Extract draft order for a given year"""
    # Get drafts for this league
    drafts_url = f"https://api.sleeper.app/v1/league/{league_id}/drafts"
    drafts = requests.get(drafts_url).json()

    if not drafts or len(drafts) == 0:
        print(f"  No draft data found")
        return None

    # Get the first draft (there's usually only one per season)
    draft_id = drafts[0]['draft_id']

    # Get all picks
    picks_url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
    picks = requests.get(picks_url).json()

    if not picks:
        print(f"  No picks found for draft {draft_id}")
        return None

    # Get round 1 picks only
    round1_picks = [p for p in picks if p['round'] == 1]
    round1_picks.sort(key=lambda x: x['pick_no'])

    # Build draft order mapping
    draft_order = {}
    for pick in round1_picks:
        username = get_username_from_roster(league_id, pick['roster_id'])
        if username:
            draft_order[username] = {
                'pick': pick['pick_no'],
                'roster_id': pick['roster_id'],
                'player_id': pick.get('player_id'),
                'round': pick['round']
            }

    return draft_order

def main():
    print("Extracting Sleeper draft positions...")

    all_draft_data = {}

    for year in sorted(LEAGUE_IDS.keys()):
        league_id = LEAGUE_IDS[year]
        print(f"\n{year} (League ID: {league_id})")

        draft_order = extract_draft_order(league_id, year)

        if draft_order:
            all_draft_data[str(year)] = draft_order
            print(f"  Draft Order:")
            for username, data in sorted(draft_order.items(), key=lambda x: x[1]['pick']):
                print(f"    Pick {data['pick']:2d}: {username}")
        else:
            all_draft_data[str(year)] = {}
            print(f"  No draft data available")

    # Save to file
    output_file = Path(__file__).parent / 'output' / 'sleeper' / 'sleeper_draft_positions.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(all_draft_data, f, indent=2)

    print(f"\n✓ Draft positions saved to {output_file}")
    print(f"  Total years: {len([y for y in all_draft_data.values() if y])}")

if __name__ == "__main__":
    main()
