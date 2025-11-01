#!/usr/bin/env python3
"""
Extract playoff results from MyFantasyLeague playoff brackets
"""
import requests
import json

# Load owner mapping
with open('owner_mapping.json', 'r') as f:
    owner_map = json.load(f)
    mfl_to_sleeper = owner_map['mfl_to_sleeper']

def get_owner_name(franchise_id):
    """Get the real name for a franchise ID"""
    franchise_id = str(franchise_id).zfill(4)
    if franchise_id in mfl_to_sleeper:
        return mfl_to_sleeper[franchise_id].get('real_name', 'Unknown')
    return f'Franchise {franchise_id}'

def get_playoff_results(year):
    """Get playoff results for a given year using playoff bracket API"""
    league_id = '59111'
    base_url = f'https://api.myfantasyleague.com/{year}/export'

    print('\n' + '='*80)
    print(f'{year} PLAYOFFS')
    print('='*80)

    results = {
        'year': year,
        'champion': None,
        'runner_up': None,
        'third_place': None,
        'sacko': None
    }

    # Get Championship Bracket (id=1) - final game is championship
    params = {
        'TYPE': 'playoffBracket',
        'L': league_id,
        'BRACKET_ID': '1',
        'JSON': '1'
    }
    response = requests.get(base_url, params=params)
    champ_bracket = response.json()

    if 'playoffBracket' in champ_bracket and 'playoffRound' in champ_bracket['playoffBracket']:
        rounds = champ_bracket['playoffBracket']['playoffRound']
        if not isinstance(rounds, list):
            rounds = [rounds]

        # Last round is the championship
        final_round = rounds[-1]
        if 'playoffGame' in final_round:
            games = final_round['playoffGame']
            if not isinstance(games, list):
                games = [games]

            # First game in final round is championship
            champ_game = games[0]
            away_id = champ_game['away']['franchise_id']
            home_id = champ_game['home']['franchise_id']
            away_score = float(champ_game['away']['points'])
            home_score = float(champ_game['home']['points'])

            if away_score > home_score:
                results['champion'] = get_owner_name(away_id)
                results['runner_up'] = get_owner_name(home_id)
            else:
                results['champion'] = get_owner_name(home_id)
                results['runner_up'] = get_owner_name(away_id)

            print(f"Championship: {results['champion']} defeated {results['runner_up']}")
            print(f"  Score: {away_score} - {home_score}")

    # Get Sacco Bracket (id=2) - winner gets Sacko
    params['BRACKET_ID'] = '2'
    response = requests.get(base_url, params=params)
    sacco_bracket = response.json()

    if 'playoffBracket' in sacco_bracket and 'playoffRound' in sacco_bracket['playoffBracket']:
        rounds = sacco_bracket['playoffBracket']['playoffRound']
        if not isinstance(rounds, list):
            rounds = [rounds]

        # Last round - winner gets Sacko
        final_round = rounds[-1]
        if 'playoffGame' in final_round:
            games = final_round['playoffGame']
            if not isinstance(games, list):
                games = [games]

            # First game in final round
            # In Sacco bracket, loser of the final gets the Sacko (last place)
            sacco_game = games[0]
            away_id = sacco_game['away']['franchise_id']
            home_id = sacco_game['home']['franchise_id']
            away_score = float(sacco_game['away']['points'])
            home_score = float(sacco_game['home']['points'])

            # Loser gets the Sacko
            if away_score > home_score:
                results['sacko'] = get_owner_name(home_id)  # home lost
            else:
                results['sacko'] = get_owner_name(away_id)  # away lost

            print(f"Sacko: {results['sacko']} (lost the Sacco Bracket final)")
            print(f"  Score: {away_score} - {home_score}")

    # Get 3rd Place Bracket (id=4)
    params['BRACKET_ID'] = '4'
    response = requests.get(base_url, params=params)
    third_bracket = response.json()

    if 'playoffBracket' in third_bracket and 'playoffRound' in third_bracket['playoffBracket']:
        playoff_round = third_bracket['playoffBracket']['playoffRound']
        if 'playoffGame' in playoff_round:
            game = playoff_round['playoffGame']
            away_id = game['away']['franchise_id']
            home_id = game['home']['franchise_id']
            away_score = float(game['away']['points'])
            home_score = float(game['home']['points'])

            if away_score > home_score:
                results['third_place'] = get_owner_name(away_id)
            else:
                results['third_place'] = get_owner_name(home_id)

            print(f"3rd Place: {results['third_place']}")
            print(f"  Score: {away_score} - {home_score}")

    return results

if __name__ == "__main__":
    all_results = []
    for year in [2016, 2017, 2018, 2019]:
        results = get_playoff_results(year)
        if results:
            all_results.append(results)

    # Save playoff results
    with open('output/mfl/mfl_playoff_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f'\n\n{"="*80}')
    print('Playoff results saved to output/mfl/mfl_playoff_results.json')
    print('='*80)
    print('\nSummary:')
    for result in all_results:
        print(f"\n{result['year']}:")
        print(f"  🏆 Champion: {result['champion']}")
        print(f"  🥈 Runner-up: {result['runner_up']}")
        if result['third_place']:
            print(f"  🥉 3rd Place: {result['third_place']}")
        if result['sacko']:
            print(f"  💩 Sacko: {result['sacko']}")
