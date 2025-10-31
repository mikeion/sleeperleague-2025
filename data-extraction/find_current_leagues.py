#!/usr/bin/env python3
from yahoofantasy import Context

ctx = Context()

# Try recent/current seasons
for year in [2024, 2023, 2022]:
    try:
        print(f"\nChecking {year}...")
        leagues = ctx.get_leagues('nfl', year)  # Try without list
        print(f"✓ Found {len(leagues)} league(s) for {year}!\n")

        for league in leagues:
            print(f"  League: {league.name}")
            if hasattr(league, 'league_id'):
                print(f"    ID: {league.league_id}")
            if hasattr(league, 'league_key'):
                print(f"    Key: {league.league_key}")
            if hasattr(league, 'season'):
                print(f"    Season: {league.season}")
            print()

    except Exception as e:
        print(f"  Error: {e}")
