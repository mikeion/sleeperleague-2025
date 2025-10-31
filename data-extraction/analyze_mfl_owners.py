#!/usr/bin/env python3
"""
Analyze MFL franchise consistency across years to identify owners
"""

import json
from pathlib import Path
from collections import defaultdict

def load_mfl_data(year):
    """Load MFL data for a given year"""
    file_path = Path(__file__).parent / 'output' / 'mfl' / f'mfl_{year}.json'
    with open(file_path, 'r') as f:
        return json.load(f)

def analyze_franchises():
    """Track franchise names across all years"""
    years = [2016, 2017, 2018, 2019]

    # Collect all team names by franchise ID
    franchise_history = defaultdict(dict)

    for year in years:
        data = load_mfl_data(year)
        franchises = data['league']['league']['franchises']['franchise']

        for franchise in franchises:
            fid = franchise.get('id')
            name = franchise.get('name', 'Unknown')
            franchise_history[fid][year] = name

    # Print the evolution of each franchise
    print("=" * 100)
    print("FRANCHISE EVOLUTION (2016-2019)")
    print("=" * 100)
    print()

    # Sort by franchise ID
    for fid in sorted(franchise_history.keys()):
        history = franchise_history[fid]
        print(f"Franchise {fid}:")
        print("-" * 100)

        for year in years:
            if year in history:
                print(f"  {year}: {history[year]}")
            else:
                print(f"  {year}: [NOT IN LEAGUE]")

        print()

    # Try to identify patterns (owners who kept similar naming styles)
    print("=" * 100)
    print("POTENTIAL OWNER PATTERNS")
    print("=" * 100)
    print()

    # Look for franchises that appeared in all 4 years (likely core owners)
    consistent_franchises = []
    for fid, history in franchise_history.items():
        if len(history) == 4:  # Appeared in all 4 years
            consistent_franchises.append((fid, history))

    print(f"Found {len(consistent_franchises)} franchises that appeared in all 4 years:")
    print()

    for fid, history in sorted(consistent_franchises):
        print(f"Franchise {fid}: {', '.join([history[y] for y in years])}")

    print()
    print("=" * 100)

    # Look for name patterns that might indicate the same owner
    print("\nLooking for naming patterns...")
    print()

    # Check if any franchise kept the same base name
    for fid, history in sorted(franchise_history.items()):
        names = [history.get(y, '') for y in years if y in history]

        # Check for common words (might indicate same owner)
        if len(names) >= 2:
            # Simple check: see if first word appears in multiple years
            words = [name.split()[0] if name.split() else '' for name in names if name]
            if len(set(words)) == 1 and words[0]:  # Same first word across years
                print(f"Franchise {fid} kept similar naming: {', '.join(names)}")

if __name__ == "__main__":
    analyze_franchises()
