#!/usr/bin/env python3
"""
Extract playoff results from MyFantasyLeague data
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
    """Get playoff results for a given year"""
    league_id = '59111'
    base_url = f'https://api.myfantasyleague.com/{year}/export'

    print('\n' + '='*80)
    print(f'{year} PLAYOFFS')
    print('='*80)

    # Fetch weeks 14, 15, 16 (playoff weeks)
    playoff_weeks = []
    for week in [14, 15, 16]:
        params = {
            'TYPE': 'weeklyResults',
            'L': league_id,
            'W': str(week),
            'JSON': '1'
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        print(f'\nWeek {week}:')

        if 'weeklyResults' in data and 'matchup' in data['weeklyResults']:
            matchups = data['weeklyResults']['matchup']
            if not isinstance(matchups, list):
                matchups = [matchups]

            week_data = []
            for matchup in matchups:
                franchises = matchup.get('franchise', [])
                if not isinstance(franchises, list):
                    franchises = [franchises]

                if len(franchises) >= 2:
                    f1 = franchises[0]
                    f2 = franchises[1]

                    id1 = f1.get('id', '?')
                    id2 = f2.get('id', '?')
                    score1 = f1.get('score', 'N/A')
                    score2 = f2.get('score', 'N/A')

                    name1 = get_owner_name(id1)
                    name2 = get_owner_name(id2)

                    winner = '?'
                    winner_id = '?'
                    if score1 != 'N/A' and score2 != 'N/A':
                        if float(score1) > float(score2):
                            winner = name1
                            winner_id = id1
                        else:
                            winner = name2
                            winner_id = id2

                    is_playoff = matchup.get('playoff', 'N') == 'Y'
                    bracket = matchup.get('bracket', '?')

                    bracket_label = ''
                    if is_playoff:
                        if bracket == '1':
                            bracket_label = ' [Championship Bracket]'
                        elif bracket == '2':
                            bracket_label = ' [Sacco Bracket]'
                        else:
                            bracket_label = f' [Bracket {bracket}]'

                    print(f'  {name1} ({score1}) vs {name2} ({score2}) - Winner: {winner}{bracket_label}')

                    week_data.append({
                        'team1': name1,
                        'team1_id': id1,
                        'team1_score': score1,
                        'team2': name2,
                        'team2_id': id2,
                        'team2_score': score2,
                        'winner': winner,
                        'winner_id': winner_id,
                        'is_playoff': is_playoff,
                        'bracket': bracket
                    })

            playoff_weeks.append({
                'week': week,
                'matchups': week_data
            })

    # Find championship game (week 16, first matchup is usually championship)
    print(f'\n{"="*80}')
    print(f'{year} CHAMPION:')
    print(f'{"="*80}')

    champion = None
    for week_data in playoff_weeks:
        if week_data['week'] == 16:
            # First matchup in week 16 is typically the championship
            if week_data['matchups']:
                matchup = week_data['matchups'][0]
                runner_up = matchup["team1"] if matchup["winner"] == matchup["team2"] else matchup["team2"]
                print(f'{matchup["winner"]} - defeated {runner_up} in championship')
                print(f'Final Score: {matchup["team1"]} {matchup["team1_score"]} - {matchup["team2_score"]} {matchup["team2"]}')
                champion = {
                    'year': year,
                    'champion': matchup["winner"],
                    'champion_id': matchup["winner_id"],
                    'runner_up': runner_up,
                    'champion_score': matchup["team1_score"] if matchup["winner"] == matchup["team1"] else matchup["team2_score"],
                    'runner_up_score': matchup["team2_score"] if matchup["winner"] == matchup["team1"] else matchup["team1_score"]
                }

    return playoff_weeks, champion

if __name__ == "__main__":
    all_champions = []
    for year in [2016, 2017, 2018, 2019]:
        playoff_data, champion = get_playoff_results(year)
        if champion:
            all_champions.append(champion)

    # Save champions data
    with open('output/mfl/mfl_champions.json', 'w') as f:
        json.dump(all_champions, f, indent=2)

    print(f'\n\nChampions data saved to output/mfl/mfl_champions.json')
    print('\nSummary:')
    for champ in all_champions:
        print(f'  {champ["year"]}: {champ["champion"]}')
