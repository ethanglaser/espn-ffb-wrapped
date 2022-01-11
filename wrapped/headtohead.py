import json
import requests
from pprint import pprint
import pandas as pd
import sys
import pickle
from collections import defaultdict


def get_roster_results(leagueId, seasonId, swid, espn_s2, regular_season_length):
    url3 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?view=mSettings'
    r3 = requests.get(url3, cookies={"swid": swid, "espn_s2": espn_s2})
    data3 = json.loads(r3.content)
    league_settings = data3['settings']
    roster_slot_counts = league_settings['rosterSettings']['lineupSlotCounts']

    lineup_positions_key = {0: 'Quarterback (QB)', 1: 'Team Quarterback (TQB)', 2: 'Running Back (RB)',3: 'Running Back/Wide Receiver (RB/WR)'
    , 4: 'Wide Receiver (WR)', 5: 'Wide Receiver/Tight End (WR/TE)', 6: 'Tight End (TE)', 23: 'Flex (FLEX)', 20: 'Bench (BE)'
    , 21: 'Injured Reserve (IR)', 17: 'Place Kicker (K)', 16: 'Team Defense/Special Teams (D/ST)', 19: 'Head Coach (HC)', 18: 'Punter (P)', 
    7: 'Offensive Player Utility (OP)', 8: 'Defensive Tackle (DT)', 9: 'Defensive End (DE)', 10: 'Linebacker (LB)', 
    11: 'Defensive Line (DL)', 12: 'Cornerback (CB)', 13: 'Safety (S)', 14: 'Defensive Back (DB)', 15: 'Defensive Player Utility (DP)'}

    existings_positions = [lineup_positions_key[int(key)] for key in roster_slot_counts.keys() if roster_slot_counts[key]]


    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/' + str(leagueId) + '?view=mMatchup&view=mMatchupScore'
    all_data = {}
    for week in range(1, regular_season_length + 1):
        r = requests.get(url, params={'scoringPeriodId': week}, cookies={"SWID": swid, "espn_s2": espn_s2})
        d = r.json()
        if week == 2:
            with open('temp.json', 'w') as outfile:
                json.dump(d['teams'], outfile)
        for index, team_data in enumerate(d['teams']):
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

                # print("LINEUP POSITION: ", current_dict['lineupSlotId'])
                # print("SCORE: ", str(round(current_dict['appliedStatTotal'], 2)))
                # print("PLAYER: ", current_dict['player']['fullName'])
                # print("slots: ", current_dict['player']['eligibleSlots'])
                # for key in current_dict['player'].keys():
                #     if key != 'rankings' and key != 'stats':
                #         print(key, current_dict['player'][key])
            if team_name not in all_data.keys():
                all_data[team_name] = {}
            all_data[team_name][week] = team_week_data

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

    return summary_data

            


    # NWL: {'0': 1, '1': 0, '2': 2, '3': 0, '4': 2, '5': 1, '6': 1, '7': 0, '8': 0, '9': 0, '10': 0, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0, '16': 1, '17': 0, '18': 0, '19': 1, '20': 7, '21': 2, '22': 0, '23': 1, '24': 0}
    # Nut station: {'0': 2, '1': 0, '2': 3, '3': 0, '4': 3, '5': 0, '6': 1, '7': 0, '8': 0, '9': 0, '10': 0, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0, '16': 1, '17': 1, '18': 0, '19': 1, '20': 9, '21': 2, '22': 0, '23': 3, '24': 0}



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
    roster_results = get_roster_results(leagueId, seasonId, swid, espn_s2, regular_season_length)
    return data, data2, regular_season_length, roster_results

def get_league_name(league_id, season_id, swid, espn_s2):
    url3 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(season_id) + '/segments/0/leagues/'  + str(league_id) + '?view=mSettings'
    r3 = requests.get(url3, cookies={"swid": swid, "espn_s2": espn_s2})
    data3 = json.loads(r3.content)
    league_name = data3['settings']['name']
    return league_name

def get_h2h(leagueId, seasonId, swid, espn_s2):
    try:
        data, data2, reg_szn_len, roster_results = gather_data(leagueId, seasonId, swid, espn_s2)
    except:
        return "Error gathering data from api."
    print(data2['scoringPeriodId'])
    print(roster_results)
    teams = {}
    for team in data['teams']:
        teams[team['id']] = {}
        teams[team['id']]['name'] = team['location'] + ' ' + team['nickname']
        teams[team['id']]['scores'] = []
        teams[team['id']]['opponents'] = []
    for game in data2['schedule'][:reg_szn_len * int(len(teams) / 2)]:
        teams[game['away']['teamId']]['scores'].append(game['away']['totalPoints'])
        teams[game['away']['teamId']]['opponents'].append(game['home']['teamId'])
        teams[game['home']['teamId']]['scores'].append(game['home']['totalPoints'])
        teams[game['home']['teamId']]['opponents'].append(game['away']['teamId'])
    scheduleinfo = defaultdict(dict)
    number_of_teams = len(teams)
    for current_team in teams.keys():
        print(current_team)
        headtohead = []
        sameschedule = []
        opp_names, record_logs = [], []
        scheduleinfo[current_team]['expected wins'] = 0
        for current_opp in teams.keys():
            current_team_scores = teams[current_team]['scores']
            current_opp_scores = teams[current_opp]['scores']
            current_opp_opp_scores = []
            for index, opp in enumerate(teams[current_opp]['opponents']):
                current_opp_opp_scores.append(teams[opp]['scores'][index])
            records = []
            for scores in [current_opp_scores, current_opp_opp_scores]:
                wins = 0
                losses = 0
                ties = 0
                for score1, score2 in zip(current_team_scores, scores):
                    if score1 > score2:
                        wins += 1
                    elif score1 < score2:
                        losses += 1
                    else:
                        ties += 1
                record = str(wins) + '-' + str(losses)
                #if ties:
                #    record +=  '-' + str(ties)
                records.append(record)
            #get expected wins
            for score1, score2 in zip(current_team_scores, current_opp_scores):
                if score1 > score2:
                    scheduleinfo[current_team]['expected wins'] += (1 / (number_of_teams - 1))

            if current_team == current_opp:
                scheduleinfo[current_team]['record'] = records[1]
            headtohead.append(records[0])
            sameschedule.append(records[1])
            if current_team != current_opp:
                opp_names.append(teams[current_opp]['name'])
                record_logs.append(records)
        try:
            team_df = pd.DataFrame(record_logs, index=opp_names, columns=['Head to Head', 'Same Schedule'])
        except:
            return 'Error creating record dataframe.'
        #try:
        positions = []
        roster_logs = []
        for position in roster_results.keys():
            if position != 'Bench (BE)' and position != 'Injured Reserve (IR)':
                positions.append(position)
                roster_logs.append([roster_results[position][current_team]['average'], roster_results[position][current_team]['place']])

        roster_df = pd.DataFrame(roster_logs, index=positions, columns=['Average', 'Place'])
        #except:
        #    return 'Error creating roster dataframe.'
                        
        try:
            team_df.to_html('wrapped/templates/' + teams[current_team]['name'] + '.html')
            roster_df.to_html('wrapped/templates/' + teams[current_team]['name'] + '_roster.html')
        except:
            return 'Error creating html file.'
        scheduleinfo[current_team]['name'] = teams[current_team]['name']
        scheduleinfo[current_team]['headtohead'] = headtohead
        scheduleinfo[current_team]['sameschedule'] = sameschedule

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
        hdf.to_html('wrapped/templates/headtohead.html')
        sdf.to_html('wrapped/templates/sameschedule.html')
    except:
        return "Error creating dataframes."
    # hdf.to_excel('League Results/' + leagueId + '-' + seasonId + '-' + 'HeadToHeadRecords.xlsx')
    # sdf.to_excel('League Results/' + leagueId + '-' + seasonId + '-' + 'SameScheduleRecords.xlsx')
    # return 'League Results/' + leagueId + '-' + seasonId + '-' + 'HeadToHeadRecords.xlsx', 'League Results/' + leagueId + '-' + seasonId + '-' + 'SameScheduleRecords.xlsx'

if __name__ == "__main__":
    # leagueId = sys.argv[3]
    # seasonId = sys.argv[4]
    # swid = sys.argv[2]
    # espn_s2 = sys.argv[1]
    # get_h2h(leagueId, seasonId, swid, espn_s2)
    leagueId = 39276
    seasonId = 2021
    swid = '52D54CB4-4327-465C-954C-B44327565CE4'
    espn_s2 = 'AEBnWn0Q%2FQq3y30XLqg2RtnOgZntUFEoOOEeDAdAGw6dknSQ7yZKbP4B9CZvcX%2FtRfl8mCmo2kGqf6FVtXHGc7mZMfxvPZxzLtD%2FoxD5dHrhhszJuotzsKdU5YynGsX3FIC7Gt9WBJ0uK%2B%2BDaRvEpWgLjGtKyArcxY8vdZnkx%2FdfQdCi5EKIOJTvIjY43geIECUNfpbmfkDurg6RaerrozFMfHuCceDAe7QvbS9t%2FYNERrfNZpc86J0A5k1OOZUK7uZxLuImUKd09J7sWjnN4yad'
    print(get_h2h(leagueId, seasonId, swid, espn_s2))