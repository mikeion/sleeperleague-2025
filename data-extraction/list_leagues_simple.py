#!/usr/bin/env python3
from yahoofantasy import Context

ctx = Context()

print("Attempting to get NFL leagues...\n")

# Try without specifying years
try:
    print("Trying: ctx.get_leagues('nfl')")
    leagues = ctx.get_leagues('nfl')
    print(f"✓ Found {len(leagues)} league(s)!\n")

    for league in leagues:
        print(f"League: {league.name}")
        print(f"  ID: {league.league_id if hasattr(league, 'league_id') else 'N/A'}")
        print(f"  Key: {league.league_key if hasattr(league, 'league_key') else 'N/A'}")
        print(f"  Season: {league.season if hasattr(league, 'season') else 'N/A'}")
        print(f"  Type: {league.league_type if hasattr(league, 'league_type') else 'N/A'}")
        print()

except Exception as e:
    print(f"✗ Error: {e}\n")

# Try with empty list
try:
    print("Trying: ctx.get_leagues('nfl', [])")
    leagues = ctx.get_leagues('nfl', [])
    print(f"✓ Found {len(leagues)} league(s)!\n")

    for league in leagues:
        print(f"League: {league.name}")
        print(f"  ID: {league.league_id if hasattr(league, 'league_id') else 'N/A'}")
        print(f"  Key: {league.league_key if hasattr(league, 'league_key') else 'N/A'}")
        print()

except Exception as e:
    print(f"✗ Error: {e}\n")
