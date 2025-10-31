#!/usr/bin/env python3
"""
Recalculate MFL points by summing weekly matchup scores
Since division years had 2 games per week, we need to sum both
"""
import json
from pathlib import Path
from collections import defaultdict

def calculate_season_points(year):
    """Calculate accurate PF/PA for a season from weekly results"""
    print(f"\nProcessing {year}...")

    mfl_file = Path(__file__).parent / 'output' / 'mfl' / f'mfl_{year}.json'
    with open(mfl_file, 'r') as f:
        data = json.load(f)

    # Get weekly results
    weekly_results_file = Path(__file__).parent / 'output' / 'mfl' / f'mfl_{year}_weekly_results.json'
    if not weekly_results_file.exists():
        print(f"  No weekly results file found for {year}")
        return None

    with open(weekly_results_file, 'r') as f:
        weekly_data = json.load(f)

    # Calculate totals per franchise
    franchise_totals = defaultdict(lambda: {'pf': 0.0, 'pa': 0.0, 'games': 0})

    for week_data in weekly_data:
        week = week_data['week']
        matchups = week_data.get('matchups', [])

        for matchup in matchups:
            franchise1 = matchup['franchise'][0]
            franchise2 = matchup['franchise'][1]

            id1 = franchise1['id']
            id2 = franchise2['id']
            score1 = float(franchise1.get('score', 0))
            score2 = float(franchise2.get('score', 0))

            # Add to each franchise's totals
            franchise_totals[id1]['pf'] += score1
            franchise_totals[id1]['pa'] += score2
            franchise_totals[id1]['games'] += 1

            franchise_totals[id2]['pf'] += score2
            franchise_totals[id2]['pa'] += score1
            franchise_totals[id2]['games'] += 1

    print(f"  Calculated totals for {len(franchise_totals)} franchises")
    return dict(franchise_totals)

def main():
    years = [2016, 2017, 2018, 2019]
    all_totals = {}

    for year in years:
        totals = calculate_season_points(year)
        if totals:
            all_totals[year] = totals

    # Save results
    output_file = Path(__file__).parent / 'output' / 'mfl' / 'mfl_recalculated_points.json'
    with open(output_file, 'w') as f:
        json.dump(all_totals, f, indent=2)

    print(f"\n✓ Saved recalculated points to {output_file}")

    # Show sample for verification
    if 2016 in all_totals and '0014' in all_totals[2016]:
        ryan_2016 = all_totals[2016]['0014']
        print(f"\nRyan (0014) 2016 recalculated:")
        print(f"  PF: {ryan_2016['pf']:.2f}")
        print(f"  PA: {ryan_2016['pa']:.2f}")
        print(f"  Games: {ryan_2016['games']}")

if __name__ == "__main__":
    main()
