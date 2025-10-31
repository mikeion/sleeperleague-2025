#!/usr/bin/env python3
"""
Verify MFL to Sleeper username mappings
Shows which users are mapped and which need manual matching
"""
import json
import requests

# Load owner mapping
with open('owner_mapping.json', 'r') as f:
    owner_map = json.load(f)
    mfl_to_sleeper = owner_map['mfl_to_sleeper']

# Get current Sleeper league users
LEAGUE_ID = '1257482235834028032'
users_response = requests.get(f'https://api.sleeper.app/v1/league/{LEAGUE_ID}/users')
sleeper_users = users_response.json()

# Fetch full profiles to get usernames
sleeper_username_map = {}
for user in sleeper_users:
    user_id = user['user_id']
    profile_response = requests.get(f'https://api.sleeper.app/v1/user/{user_id}')
    profile = profile_response.json()
    if 'username' in profile and profile['username']:
        username = profile['username'].lower()
        display_name = user['display_name']
        sleeper_username_map[username] = display_name

print("="*80)
print("MFL TO SLEEPER MAPPING VERIFICATION")
print("="*80)

print("\n✅ MATCHED USERS (MFL franchise has valid Sleeper username):")
print("-"*80)
matched = []
for fid, data in mfl_to_sleeper.items():
    sleeper_user = data.get('sleeper_username', 'unknown').lower()
    real_name = data.get('real_name', 'Unknown')

    if sleeper_user != 'unknown' and sleeper_user in sleeper_username_map:
        sleeper_display = sleeper_username_map[sleeper_user]
        print(f"  [{fid}] {real_name:20} -> {sleeper_user:20} ({sleeper_display})")
        matched.append(fid)

print(f"\n❌ UNMATCHED USERS (MFL franchise with 'unknown' or invalid Sleeper username):")
print("-"*80)
unmatched = []
for fid, data in mfl_to_sleeper.items():
    sleeper_user = data.get('sleeper_username', 'unknown').lower()
    real_name = data.get('real_name', 'Unknown')
    notes = data.get('notes', '')

    if sleeper_user == 'unknown' or sleeper_user not in sleeper_username_map:
        status = 'NOT IN LEAGUE' if 'NOT IN' in notes or 'LEFT' in notes else 'NEEDS MAPPING'
        print(f"  [{fid}] {real_name:20} - {status}")
        print(f"        Notes: {notes}")
        if sleeper_user != 'unknown':
            print(f"        Current mapping: {sleeper_user} (NOT FOUND IN SLEEPER)")
        unmatched.append(fid)

print(f"\n📊 AVAILABLE SLEEPER USERS (for manual matching):")
print("-"*80)
for username, display_name in sorted(sleeper_username_map.items()):
    # Check if already mapped
    is_mapped = any(
        data.get('sleeper_username', '').lower() == username
        for data in mfl_to_sleeper.values()
    )
    status = "✓ mapped" if is_mapped else "  available"
    print(f"  {status}  {username:20} ({display_name})")

print(f"\n📈 SUMMARY:")
print(f"  Matched: {len(matched)}")
print(f"  Unmatched: {len(unmatched)}")
print(f"  Total MFL users: {len(mfl_to_sleeper)}")
print(f"  Total Sleeper users: {len(sleeper_users)}")
