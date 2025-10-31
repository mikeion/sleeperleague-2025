#!/usr/bin/env python3
from yahoofantasy import Context, League

ctx = Context()

# Yahoo league keys follow the format: game_code.l.league_id
# For NFL 2020, game code should be something like 390
# For NFL 2021, game code should be something like 399

# Let's try to construct league keys
# Yahoo game codes for NFL: https://developer.yahoo.com/fantasysports/guide/game-resource.html
# 2020 = 390, 2021 = 399, 2022 = 406, 2023 = 414, 2024 = 423

league_configs = [
    ("390.l.114631", "2020"),  # NFL 2020
    ("399.l.1061934", "2021"),  # NFL 2021
]

for league_key, year in league_configs:
    print(f"\nTrying {year} with league key: {league_key}")
    try:
        league = League(ctx, league_key)
        print(f"✓ Success! League: {league.name}")
        print(f"  Season: {league.season if hasattr(league, 'season') else 'unknown'}")
        print(f"  Number of teams: {league.num_teams if hasattr(league, 'num_teams') else 'unknown'}")
    except Exception as e:
        print(f"✗ Error: {e}")
