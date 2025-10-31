#!/usr/bin/env python3
from yahoofantasy import Context

ctx = Context()

print("Checking which NFL seasons are available...\n")

for year in range(2015, 2026):
    try:
        leagues = ctx.get_leagues('nfl', [year])
        if leagues:
            print(f"✓ {year}: Found {len(leagues)} league(s)")
            for league in leagues:
                print(f"    - {league.name} (ID: {league.league_id})")
        else:
            print(f"  {year}: No leagues")
    except Exception as e:
        print(f"✗ {year}: Error - {e}")
