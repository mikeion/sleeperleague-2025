#!/usr/bin/env python3
"""
Test Yahoo Fantasy API authentication
"""

from yahoofantasy import Context

print("Testing Yahoo Fantasy API authentication...")
print()
print("This will open a browser window for you to authorize the app.")
print("If you see an error, make sure:")
print("  1. Your Yahoo app has 'Fantasy Sports' permission enabled")
print("  2. Redirect URI is exactly: http://localhost:8000")
print("  3. You're using the correct Client ID and Secret")
print()

try:
    # Try to create a context (this will trigger OAuth flow)
    ctx = Context()
    print("✓ Authentication successful!")
    print()

    # Try to fetch some basic data
    print("Testing API access...")
    try:
        # Get NFL leagues for 2020
        leagues = ctx.get_leagues('nfl', [2020])
        print(f"✓ Found {len(leagues)} NFL league(s) for 2020")

        if leagues:
            print()
            print("Leagues found:")
            for league in leagues:
                print(f"  - {league.name} (ID: {league.league_id})")
    except Exception as e:
        print(f"✗ Error fetching leagues: {e}")
        print()
        print("This might mean:")
        print("  - You don't have any Yahoo Fantasy leagues for 2020")
        print("  - The league is private and you don't have access")
        print("  - The league ID is different than expected")

except Exception as e:
    print(f"✗ Authentication failed: {e}")
    print()
    print("Please check:")
    print("  1. Run 'yahoofantasy login' first")
    print("  2. Make sure your Yahoo app is configured correctly")
    print("  3. Check the redirect URI is http://localhost:8000")
