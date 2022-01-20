import json
import requests
from pprint import pprint
import pandas as pd
import sys
import pickle
from collections import defaultdict
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


lineup_positions_key = {0: 'Quarterback (QB)', 1: 'Team Quarterback (TQB)', 2: 'Running Back (RB)',3: 'Running Back/Wide Receiver (RB/WR)'
    , 4: 'Wide Receiver (WR)', 5: 'Wide Receiver/Tight End (WR/TE)', 6: 'Tight End (TE)', 23: 'Flex (FLEX)', 20: 'Bench (BE)'
    , 21: 'Injured Reserve (IR)', 17: 'Place Kicker (K)', 16: 'Team Defense/Special Teams (D/ST)', 19: 'Head Coach (HC)', 18: 'Punter (P)', 
    7: 'Offensive Player Utility (OP)', 8: 'Defensive Tackle (DT)', 9: 'Defensive End (DE)', 10: 'Linebacker (LB)', 
    11: 'Defensive Line (DL)', 12: 'Cornerback (CB)', 13: 'Safety (S)', 14: 'Defensive Back (DB)', 15: 'Defensive Player Utility (DP)'}

actual_positions_key = {16: 'D/ST', 14: 'HC', 5: 'K', 1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 7: 'K', 9: 'RB'}

def get_roster_results(leagueId, seasonId, swid, espn_s2, regular_season_length):
    #First, pull roster structure info from league settings
    url3 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?view=mSettings'
    r3 = requests.get(url3, cookies={"swid": swid, "espn_s2": espn_s2})
    data3 = json.loads(r3.content)
    league_settings = data3['settings']
    roster_slot_counts = league_settings['rosterSettings']['lineupSlotCounts']

    existings_positions = [lineup_positions_key[int(key)] for key in roster_slot_counts.keys() if roster_slot_counts[key]]
    pre_df = []

    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/' + str(leagueId) + '?view=mMatchup&view=mMatchupScore'
    all_data = {}
    for week in range(1, regular_season_length + 1):
        # Get the data one week at a time
        r = requests.get(url, params={'scoringPeriodId': week}, cookies={"SWID": swid, "espn_s2": espn_s2})
        d = r.json()
        for team_data in d['teams']:
            team_name = team_data['id']
            team_week_data = dict.fromkeys(existings_positions, 0)
            for current in team_data['roster']['entries']:
                current_dict = current['playerPoolEntry']
                score = 0
                for stat in current_dict['player']['stats']:
                    if stat['scoringPeriodId'] != week:
                        continue
                    if stat['statSourceId'] == 0:
                        score = stat['appliedTotal']
                team_week_data[lineup_positions_key[current['lineupSlotId']]] += score
                pre_df.append([team_name, week, current_dict['player']['defaultPositionId'], current['lineupSlotId'], current_dict['player']['fullName'], score])

                # print("LINEUP POSITION: ", current_dict['lineupSlotId'])
                # print("SCORE: ", str(round(current_dict['appliedStatTotal'], 2)))
                # print("PLAYER: ", current_dict['player']['fullName'])
                # # print("slots: ", current_dict['player']['eligibleSlots'])
                # for key in current_dict['player'].keys():
                #     if key != 'rankings' and key != 'stats':
                #         print(key, current_dict['player'][key])
            if team_name not in all_data.keys():
                all_data[team_name] = {}
            all_data[team_name][week] = team_week_data
    roster_df = pd.DataFrame(pre_df, columns=['team id', 'week', 'position id', 'roster slot id', 'player', 'score'])


    #summary_data = dict.fromkeys(existings_positions, dict.fromkeys(all_data.keys(), {'total': 0, 'average': 0}))
    summary_data = {pos: {team: {'total': 0, 'average': 0} for team in all_data.keys()} for pos in existings_positions}
    for team in all_data.keys():
        for week in all_data[team].keys():
            for position in existings_positions:
                summary_data[position][team]['total'] += all_data[team][week][position]
    for position in summary_data.keys():
        order = sorted([summary_data[position][team]['total'] for team in all_data.keys()])[::-1]
        for team in summary_data[position].keys():
            for id in lineup_positions_key.keys():
                if lineup_positions_key[id] == position:
                    roster = roster_slot_counts[str(id)]
            summary_data[position][team]['average'] = summary_data[position][team]['total'] / (regular_season_length * roster)
            summary_data[position][team]['place'] = order.index(summary_data[position][team]['total']) + 1
            summary_data[position][team]['total'] = round(summary_data[position][team]['total'], 2)

    return summary_data, roster_df

def gather_data(leagueId, seasonId, swid, espn_s2):
    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?'
    url2 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?view=mMatchup'
    url3 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?view=mSettings'
    
    r = requests.get(url, cookies={"swid": swid, "espn_s2": espn_s2})
    data = (json.loads(r.content))
    r2 = requests.get(url2, cookies={"swid": swid, "espn_s2": espn_s2})
    data2 = json.loads(r2.content)

    r3 = requests.get(url3, cookies={"swid": swid, "espn_s2": espn_s2})
    data3 = json.loads(r3.content)
    regular_season_length = data3['settings']['scheduleSettings']['matchupPeriodCount']
    roster_dict, roster_df = get_roster_results(leagueId, seasonId, swid, espn_s2, regular_season_length)
    return data, data2, regular_season_length, roster_dict, roster_df

def get_league_name(league_id, season_id, swid, espn_s2):
    url3 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(season_id) + '/segments/0/leagues/'  + str(league_id) + '?view=mSettings'
    r3 = requests.get(url3, cookies={"swid": swid, "espn_s2": espn_s2})
    data3 = json.loads(r3.content)
    league_name = data3['settings']['name']
    return league_name

def get_performance_leaders(df, constraints={}, starters_only=True, n=10, best=True, rating=False):
    if starters_only:
        df = df[(df['roster slot id'] != 20) & (df['roster slot id'] != 21)]
    if rating:
        metric = 'rating'
    else:
        metric = 'score'
    for key in constraints.keys():
        df = df[df[key] == constraints[key]]
    if best:
        return df.nlargest(n, metric)
    else:
        return df.nsmallest(n, metric)

def get_pie_chart_info(df, starters_only=True):
    if starters_only:
        df = df[(df['roster slot id'] != 20) & (df['roster slot id'] != 21)]

    pie_chart_data = defaultdict(float)
    pie_chart_data['position'] = 'proportion'
    for position_id in df['position id'].unique():
        if position_id in actual_positions_key.keys():
            pie_chart_data[actual_positions_key[position_id]] += df[df['position id'] == position_id]['score'].sum()
        else:
            pie_chart_data[lineup_positions_key[position_id]] += df[df['position id'] == position_id]['score'].sum()
    return pie_chart_data

def get_h2h(leagueId, seasonId, swid, espn_s2, create_files=True):
    try:
        data, data2, reg_szn_len, roster_dict, roster_df = gather_data(leagueId, seasonId, swid, espn_s2)
    except:
        return "Error gathering data from api."
    teams = {}
    teams_pre_df = []
    for team in data['teams']:
        teams[team['id']] = {}
        teams[team['id']]['name'] = team['location'] + ' ' + team['nickname']
        teams[team['id']]['scores'] = []
        teams[team['id']]['opponents'] = []
        teams[team['id']]['opponents scores'] = []
    for game in data2['schedule'][:reg_szn_len * int(len(teams) / 2)]:
        teams[game['away']['teamId']]['scores'].append(game['away']['totalPoints'])
        teams[game['away']['teamId']]['opponents'].append(game['home']['teamId'])
        teams[game['away']['teamId']]['opponents scores'].append(game['home']['totalPoints'])
        teams[game['home']['teamId']]['scores'].append(game['home']['totalPoints'])
        teams[game['home']['teamId']]['opponents'].append(game['away']['teamId'])
        teams[game['home']['teamId']]['opponents scores'].append(game['away']['totalPoints'])

        teams_pre_df.append([game['matchupPeriodId'], game['away']['teamId'], game['home']['teamId'], game['away']['totalPoints'], game['home']['totalPoints']])
        teams_pre_df.append([game['matchupPeriodId'], game['home']['teamId'], game['away']['teamId'], game['home']['totalPoints'], game['away']['totalPoints']])
    teams_df = pd.DataFrame(teams_pre_df, columns=['week', 'team', 'opponent', 'score', 'opponent score'])
    teams_df['team name'] = teams_df['team'].map(lambda x: teams[x]['name'])
    teams_df['opponent name'] = teams_df['opponent'].map(lambda x: teams[x]['name'])
    with open('wrapped/static/weekly_team_scores.pkl', 'wb') as f:
        pickle.dump(teams_df, f)
    
    scheduleinfo = defaultdict(dict)
    number_of_teams = len(teams)
    pie_info = {}
    for current_team in teams.keys():
        headtohead = []
        sameschedule = []
        opp_names, record_logs = [], []
        scheduleinfo[current_team]['expected wins'] = 0
        for current_opp in teams.keys():
            wins_h, losses_h, ties_h = 0, 0, 0
            wins_s, losses_s, ties_s = 0, 0, 0
            for team_score, opp_score, opp_opp_score in zip(teams[current_team]['scores'], teams[current_opp]['scores'], teams[current_opp]['opponents scores']):
                if team_score > opp_score:
                    wins_h += 1
                    scheduleinfo[current_team]['expected wins'] += (1 / (number_of_teams - 1))
                elif team_score < opp_score:
                    losses_h += 1
                else:
                    ties_h += 1
                if team_score > opp_opp_score:
                    wins_s += 1
                elif team_score < opp_opp_score:
                    losses_s += 1
                elif team_score > opp_score:
                    wins_s += 1
                elif team_score < opp_score:
                    losses_s += 1
                else:
                    ties_s += 1
            record_h = str(wins_h) + '-' + str(losses_h)
            if ties_h:
                record_h +=  '-' + str(ties_h)
            record_s = str(wins_s) + '-' + str(losses_s)
            if ties_s:
                record_s +=  '-' + str(ties_s)

            if current_team == current_opp:
                scheduleinfo[current_team]['record'] = record_s
            headtohead.append(record_h)
            sameschedule.append(record_s)
            if current_team != current_opp:
                opp_names.append(teams[current_opp]['name'])
                record_logs.append([record_h, record_s])
        try:
            team_df = pd.DataFrame(record_logs, index=opp_names, columns=['Head to Head', 'Same Schedule'])
        except:
            return 'Error creating record dataframe.'
        #try:
        positions = []
        roster_logs = []
        for position in roster_dict.keys():
            if position != 'Bench (BE)' and position != 'Injured Reserve (IR)':
                positions.append(position)
                roster_logs.append([round(roster_dict[position][current_team]['average'], 2), roster_dict[position][current_team]['place']])

        team_roster_df = pd.DataFrame(roster_logs, index=positions, columns=['Average', 'Place'])
        pie_info[current_team] = get_pie_chart_info(roster_df[roster_df['team id'] == current_team])
        #except:
        #    return 'Error creating roster dataframe.'             
        try:
            if create_files:
                team_df.to_html('wrapped/templates/generated_team' + str(current_team) + '.html')
                team_roster_df.to_html('wrapped/templates/generated_team' + str(current_team) + '_roster.html')
        except:
            return 'Error creating html file for ' + teams[current_team]['name']
        scheduleinfo[current_team]['name'] = teams[current_team]['name']
        scheduleinfo[current_team]['headtohead'] = headtohead
        scheduleinfo[current_team]['sameschedule'] = sameschedule
    
    roster_df['team name'] = roster_df['team id'].map(lambda x: teams[x]['name'])
    roster_df['position'] = roster_df['position id'].map(lambda x: actual_positions_key[x])
    roster_df['roster slot'] = roster_df['roster slot id'].map(lambda x: lineup_positions_key[x])
    with open('wrapped/static/roster_df.pkl', 'wb') as f:
        pickle.dump(roster_df, f)
    with open('wrapped/static/pie_info.pkl', 'wb') as f:
        pickle.dump(pie_info, f)

    h = [scheduleinfo[key]['headtohead'] for key in sorted(scheduleinfo.keys())]
    s = [scheduleinfo[key]['sameschedule'] for key in sorted(scheduleinfo.keys())]
    t = [scheduleinfo[key]['name'] for key in sorted(scheduleinfo.keys())]
    try:
        with open('wrapped/static/team_names.pkl', 'wb') as f:
            pickle.dump(scheduleinfo, f)
    except:
        return str(scheduleinfo)
    try:
        hdf = pd.DataFrame(h, columns = t, index = t)
        sdf = pd.DataFrame(s, columns = t, index = t)
        if create_files:
            hdf.to_html('wrapped/templates/generated_headtohead.html')
            sdf.to_html('wrapped/templates/generated_sameschedule.html')
    except:
        return "Error creating dataframes."


if __name__ == "__main__":
    # leagueId = sys.argv[3]
    # seasonId = sys.argv[4]
    # swid = sys.argv[2]
    # espn_s2 = sys.argv[1]
    # get_h2h(leagueId, seasonId, swid, espn_s2)
    
    #leagueId = 558120502
    leagueId = 39276
    seasonId = 2021
    swid = '52D54CB4-4327-465C-954C-B44327565CE4'
    espn_s2 = 'AEBnWn0Q%2FQq3y30XLqg2RtnOgZntUFEoOOEeDAdAGw6dknSQ7yZKbP4B9CZvcX%2FtRfl8mCmo2kGqf6FVtXHGc7mZMfxvPZxzLtD%2FoxD5dHrhhszJuotzsKdU5YynGsX3FIC7Gt9WBJ0uK%2B%2BDaRvEpWgLjGtKyArcxY8vdZnkx%2FdfQdCi5EKIOJTvIjY43geIECUNfpbmfkDurg6RaerrozFMfHuCceDAe7QvbS9t%2FYNERrfNZpc86J0A5k1OOZUK7uZxLuImUKd09J7sWjnN4yad'
    print(get_h2h(leagueId, seasonId, swid, espn_s2, create_files=False))