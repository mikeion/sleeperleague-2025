#!/usr/bin/env python3
import json

with open('owner_mapping.json', 'r') as f:
    data = json.load(f)

mfl = data['mfl_to_sleeper']

print('=' * 80)
print('CONFIRMED OWNER MAPPINGS')
print('=' * 80)
print()

confirmed = []
unknown = []

for fid in sorted(mfl.keys()):
    franchise = mfl[fid]
    real_name = franchise.get('real_name', '')
    sleeper_user = franchise.get('sleeper_username', 'unknown')
    notes = franchise.get('notes', '')

    if real_name or (sleeper_user != 'unknown' and sleeper_user != 'not_in_league'):
        confirmed.append((fid, real_name, sleeper_user, notes))
    else:
        unknown.append((fid, notes))

print(f'CONFIRMED ({len(confirmed)} franchises):')
print()
for fid, real_name, sleeper_user, notes in confirmed:
    name_display = real_name if real_name else sleeper_user
    print(f'  Franchise {fid}: {name_display}')
    team_names = notes.split('Team names: ')[1].split(' - ')[0] if 'Team names:' in notes else notes
    print(f'       Teams: {team_names}')
    print()

print()
print('=' * 80)
print(f'UNKNOWN ({len(unknown)} franchises):')
print('=' * 80)
print()
for fid, notes in unknown:
    team_names = notes.split('Team names: ')[1].split(' - ')[0] if 'Team names:' in notes else notes
    print(f'  Franchise {fid}: {team_names}')
    print()
