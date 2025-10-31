#!/usr/bin/env python3
"""
Test what Yahoo leagues we can access
"""

from yahoofantasy import Context

print("Checking what Yahoo Fantasy leagues are available...\n")

try:
    ctx = Context()

    # Try different years
    for year in [2020, 2021, 2022, 2023, 2024]:
        print(f"Checking {year}...")
        try:
            leagues = ctx.get_leagues('nfl', [year])
            if leagues:
                print(f"  ✓ Found {len(leagues)} league(s):")
                for league in leagues:
                    print(f"    - {league.name}")
                    print(f"      ID: {league.league_id}")
                    print(f"      Key: {league.league_key if hasattr(league, 'league_key') else 'N/A'}")
            else:
                print(f"  - No leagues found")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

    # Try to get all leagues without specifying year
    print("\nTrying to get all available leagues...")
    try:
        # Some versions might support this
        all_leagues = ctx.get_leagues('nfl')
        print(f"Found {len(all_leagues)} total leagues")
        for league in all_leagues:
            print(f"  - {league.name} ({league.season if hasattr(league, 'season') else 'unknown year'})")
    except Exception as e:
        print(f"Could not fetch all leagues: {e}")

except Exception as e:
    print(f"Authentication error: {e}")
    print("\nMake sure you ran: yahoofantasy login")
