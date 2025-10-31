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

# Load the MFL data for each year
for year in [2016, 2017, 2018, 2019]:
    print('\n' + '='*80)
    print(f'{year} PLAYOFF BRACKET')
    print('='*80)

    with open(f'output/mfl/mfl_{year}.json', 'r') as f:
        data = json.load(f)

    # Look at the schedule to find playoff weeks
    if 'schedule' in data and 'leagueSchedules' in data['schedule']:
        schedules = data['schedule']['leagueSchedules']
        if 'weeklySchedule' in schedules:
            weekly = schedules['weeklySchedule']
            if isinstance(weekly, list):
                # Find playoff weeks (usually weeks 14-16)
                playoff_weeks = [w for w in weekly if int(w.get('week', 0)) >= 14]

                for week_data in playoff_weeks:
                    week = week_data.get('week', '')
                    print(f'\nWeek {week}:')
                    matchups = week_data.get('matchup', [])
                    if not isinstance(matchups, list):
                        matchups = [matchups]

                    for matchup in matchups:
                        franchise_list = matchup.get('franchise', [])
                        if not isinstance(franchise_list, list):
                            franchise_list = [franchise_list]

                        if len(franchise_list) >= 2:
                            f1 = franchise_list[0]
                            f2 = franchise_list[1]

                            id1 = f1.get('id', '?')
                            id2 = f2.get('id', '?')
                            score1 = f1.get('score', 'N/A')
                            score2 = f2.get('score', 'N/A')

                            name1 = get_owner_name(id1)
                            name2 = get_owner_name(id2)

                            winner = '?'
                            if score1 != 'N/A' and score2 != 'N/A':
                                try:
                                    if float(score1) > float(score2):
                                        winner = name1
                                    else:
                                        winner = name2
                                except:
                                    pass

                            print(f'  {name1} ({score1}) vs {name2} ({score2}) - Winner: {winner}')
