#!/usr/bin/env python3
"""
Find all Yahoo Fantasy leagues for the authenticated user
"""

from yahoofantasy import Context
import requests

ctx = Context()

print("Searching for all your Yahoo Fantasy leagues...\n")

# The Yahoo API endpoint to get all user games/leagues
base_url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nfl/leagues"

try:
    # Make direct API call
    response = ctx.get(base_url)

    print("Raw response:")
    print(response.text[:1000])
    print("\n" + "="*80 + "\n")

    # Try to parse it
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.text)

    # Yahoo API uses XML with namespaces
    ns = {'fantasy': 'http://fantasysports.yahooapis.com/fantasy/v2/base.rng'}

    games = root.findall('.//fantasy:game', ns)
    print(f"Found {len(games)} NFL game(s)\n")

    for game in games:
        game_key = game.find('fantasy:game_key', ns)
        season = game.find('fantasy:season', ns)

        if game_key is not None and season is not None:
            print(f"NFL Season {season.text} (Game Key: {game_key.text})")

            # Find leagues for this game
            leagues = game.findall('.//fantasy:league', ns)
            for league in leagues:
                league_key = league.find('fantasy:league_key', ns)
                league_name = league.find('fantasy:name', ns)
                league_id = league.find('fantasy:league_id', ns)

                if league_key is not None:
                    print(f"  ✓ {league_name.text if league_name is not None else 'Unknown'}")
                    print(f"    League Key: {league_key.text}")
                    print(f"    League ID: {league_id.text if league_id is not None else 'Unknown'}")
                    print()

except Exception as e:
    print(f"Error fetching leagues: {e}")
    print("\nTrying alternative method...")

    # Try getting user info
    try:
        user_url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1"
        response = ctx.get(user_url)
        print("User info:")
        print(response.text[:500])
    except Exception as e2:
        print(f"Also failed: {e2}")

print("\n" + "="*80)
print("If you see your leagues above, note the 'League Key' for each one.")
print("We need the full league key (e.g., '399.l.1061934') not just the ID.")
