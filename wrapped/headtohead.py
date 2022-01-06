import json
import requests
from pprint import pprint
import pandas as pd
import sys
import pickle
from collections import defaultdict


def gather_data(leagueId, seasonId, swid, espn_s2):
    print(leagueId, seasonId, swid, espn_s2)
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
    return data, data2, regular_season_length

def get_league_name(league_id, season_id, swid, espn_s2):
    url3 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(season_id) + '/segments/0/leagues/'  + str(league_id) + '?view=mSettings'
    r3 = requests.get(url3, cookies={"swid": swid, "espn_s2": espn_s2})
    data3 = json.loads(r3.content)
    league_name = data3['settings']['name']
    return league_name

def get_h2h(leagueId, seasonId, swid, espn_s2):
    try:
        data, data2, reg_szn_len = gather_data(leagueId, seasonId, swid, espn_s2)
    except:
        return "Error gathering data from api."

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
            return 'Error creating dataframe.'
        try:
            team_df.to_html('wrapped/templates/' + teams[current_team]['name'] + '.html')
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
    leagueId = sys.argv[3]
    seasonId = sys.argv[4]
    swid = sys.argv[2]
    espn_s2 = sys.argv[1]
    get_h2h(leagueId, seasonId, swid, espn_s2)