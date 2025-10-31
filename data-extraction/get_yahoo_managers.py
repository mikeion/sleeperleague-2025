#!/usr/bin/env python3
"""
Get manager names from Yahoo teams
"""
from yahoofantasy import Context
import json

ctx = Context()

# Get 2021 league
leagues = ctx.get_leagues('nfl', 2021)
league = None
for lg in leagues:
    if lg.league_key == '406.l.1061934':
        league = lg
        break

if league:
    print('2021 Teams and Managers:\n')
    standings = league.standings()

    for team in standings:
        team_name = team.name if hasattr(team, 'name') else 'Unknown'

        # Try to get manager info in different ways
        manager_name = None

        # Try manager object
        if hasattr(team, 'manager'):
            if hasattr(team.manager, 'nickname'):
                manager_name = team.manager.nickname
            elif hasattr(team.manager, 'manager_nickname'):
                manager_name = team.manager.manager_nickname
            elif hasattr(team.manager, 'guid'):
                manager_name = f"GUID: {team.manager.guid}"

        # Try managers list
        if not manager_name and hasattr(team, 'managers'):
            try:
                # The managers object has a manager attribute
                if hasattr(team.managers, 'manager'):
                    mgr = team.managers.manager
                    if hasattr(mgr, 'nickname'):
                        manager_name = mgr.nickname
                    elif hasattr(mgr, 'manager_nickname'):
                        manager_name = mgr.manager_nickname
            except Exception as e:
                print(f"Error accessing managers: {e}")

        # Print available attributes for debugging
        print(f"{team_name:40} -> {manager_name}")

    # Also print raw team object to see what's available
    print("\n\nDebug: First team object attributes:")
    if standings:
        first_team = standings[0]
        print(f"Available attributes: {dir(first_team)}")
        if hasattr(first_team, 'manager'):
            print(f"\nManager attributes: {dir(first_team.manager)}")
        if hasattr(first_team, 'managers'):
            print(f"\nManagers type: {type(first_team.managers)}")
            print(f"Managers attributes: {dir(first_team.managers)}")
