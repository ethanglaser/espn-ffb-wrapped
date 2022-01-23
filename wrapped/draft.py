import requests
import json
from pprint import pprint
import os
import sys
import pandas as pd
import numpy as np
import pickle
from sklearn.svm import SVR



def getFantasyTeams(espn_s2, swid, url):
    fantasyTeamsKey = {}
    r = requests.get(url, cookies={"swid": swid, "espn_s2": espn_s2})
    data = json.loads(r.content)
    for team in data['teams']:
        fantasyTeamsKey[team['id']] = team['location'] + ' ' + team['nickname']
    return fantasyTeamsKey

def getSeasonResults(espn_s2, swid, url, positionsKey, nflTeamsKey, leagueId, seasonId):
    playerData = {}
    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?view=kona_player_info'
    r = requests.get(url, cookies={"swid": swid, "espn_s2": espn_s2}, headers={'x-fantasy-filter': '{"players": {"sortAppliedStatTotal":{"sortAsc":false,"sortPriority":2,"value":"00' + str(seasonId) + '"}}}'})
    #r = requests.get(url, cookies={"swid": swid, "espn_s2": espn_s2}, params={"view": 'kona_player_info'}, headers={"x-fantasy-filter": '{"players":{"filterSlotIds":{"value":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23,24]},"sortAppliedStatTotal":{"sortAsc":false,"sortPriority":2,"value":"002020"},"sortAppliedStatTotalForScoringPeriodId":null,"sortStatId":null,"sortStatIdForScoringPeriodId":null,"sortPercOwned":{"sortPriority":3,"sortAsc":false},"filterRanksForSlotIds":{"value":[0,2,4,6,17,16]},"filterStatsForTopScoringPeriodIds":{"value":2,"additionalValue":["002020","102020","002019","022020"]}}}'})
    data = json.loads(r.content)
    if int(seasonId) >= 2021:
        default_weeks = 17
    else:
        default_weeks = 16
    for player in data['players']:
        if 'ratings' in player.keys():
            playerData[player['id']] = {}
            playerData[player['id']]['Player Name'] = player['player']['fullName']
            playerData[player['id']]['nflTeam'] = nflTeamsKey[player['player']['proTeamId']]
            playerData[player['id']]['Position'] = positionsKey[player['player']['defaultPositionId']]
            playerData[player['id']]['Overall Finish'] = int(player['ratings']['0']['totalRanking'])
            playerData[player['id']]['Position-Based Season Finish'] = int(player['ratings']['0']['positionalRanking'])
            # if player['player']['fullName'] == "Josh Allen":
            #     pprint(player)
            #playerData[player['id']]['Total Points'] = round(float(player['ratings']['0']['totalRating']), 3)
            # if player['player']['fullName'] == "Rondale Moore" or player['player']['fullName'] == "Tom Brady":
            #     pprint(player['player']['stats'])
            for current in player['player']['stats']:
                if current['id'] == '00' + str(seasonId):
                #if round(current['appliedTotal'], 2) == round(playerData[player['id']]['Total Points'], 2):
                    playerData[player['id']]['Average Weekly Scoring'] = round(current['appliedAverage'], 3)
                    playerData[player['id']]['Total Points'] = round(current['appliedTotal'], 3)
            if 'Average Weekly Scoring' not in playerData[player['id']].keys() and playerData[player['id']]['Total Points'] > 100:
                pprint(playerData[player['id']])
                pprint(player['player']['stats'])

            if playerData[player['id']]['Position'] == 'HC' or playerData[player['id']]['Position'] == 'D/ST':
                playerData[player['id']]['Number of Weeks Missed'] = 0
            elif playerData[player['id']]['Average Weekly Scoring'] == 0:
                playerData[player['id']]['Number of Weeks Missed'] = default_weeks
            else:
                playerData[player['id']]['Number of Weeks Missed'] = round(default_weeks - playerData[player['id']]['Total Points'] / playerData[player['id']]['Average Weekly Scoring'])

        
    return playerData

def getDraftResults(espn_s2, swid, url, playerData, fantasyTeamsKey):
    draftData = {}
    draftPositionOrder = {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'K': 1, 'D/ST': 1, 'HC': 1}
    r = requests.get(url, cookies={"swid": swid, "espn_s2": espn_s2}, params={"view": 'mDraftDetail'})
    data = json.loads(r.content)
    for pick in data['draftDetail']['picks']:
        draftData[pick['playerId']] = playerData[pick['playerId']]
        draftData[pick['playerId']]['Overall Draft Pick'] = pick['overallPickNumber']
        draftData[pick['playerId']]['Fantasy Team'] = fantasyTeamsKey[pick['teamId']]
        draftData[pick['playerId']]['Position-Based Draft Pick'] = draftPositionOrder[draftData[pick['playerId']]['Position']]
        draftPositionOrder[draftData[pick['playerId']]['Position']] += 1

    return draftData


def process_season(df, drop_cols, position_normalize_cols, general_normalize_cols, draft_perform_ratio=False, log_positions=False, top_finish=False):
    # drop specified columns
    df = df.drop(columns=drop_cols)
    # normalize specified columns
    for col in position_normalize_cols:
        #TODO pull out col after grouping by position
        groups = df.groupby('Position')[col]
        df['normal_' + col] = groups.transform(lambda x: (x - x.mean()) / x.std())
    for col in general_normalize_cols:
        df['normal_' + col] = (df[col] - df[col].mean()) / df[col].std()
    
    if draft_perform_ratio:
        df['draft_perform_ratio'] = np.log(df['position_draft'] / df['position_finish'])
    if log_positions:
        df['log_finish'] = np.log(df['position_finish'])
        df['log_draft'] = np.log(df['position_draft'])
    if top_finish:
        df['top_finish'] = df['position_finish'] == 1
        df['top_3_finish'] = df['position_finish'] <= 3
    # return processed dataframe
    return df

def initial_processing(current, column_renames):
    current = current.rename(columns=column_renames)
    if "Points in Final 8 Weeks" in current.columns:
        current = current.drop(columns=["Points in Final 8 Weeks"])
    current = current.dropna()
    current['Position'] = current[column_renames['Position']]
    current = pd.get_dummies(current, columns=[column_renames["Position"]], prefix=column_renames["Position"])
    current[column_renames["Position-Based Draft Pick"]] = current[column_renames["Position-Based Draft Pick"]]
    current[column_renames["Position-Based Season Finish"]] = current[column_renames["Position-Based Season Finish"]]
    current = current.replace({column_renames["Position-Based Season Finish"]: 0}, 100)
    return current


def get_draft_df(leagueId, seasonId, swid, espn_s2):

    url2 = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(seasonId) + '/segments/0/leagues/'  + str(leagueId) + '?'
    positionsKey = {16: 'D/ST', 14: 'HC', 5: 'K', 1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 7: 'K', 9: 'RB'}
    nflTeamsKey = {0: 'FA', 34: 'Texans', 33: 'Ravens', 30: 'Jaguars', 29: 'Panthers',  28: 'Redskins', 27: 'Buccaneers', 26: 'Seahawks', 25: '49ers', 24: 'Chargers', 23: 'Steelers', 22: 'Cardinals', 21: 'Eagles', 20: 'Jets', 19: 'Giants', 18: 'Saints', 17: 'Patriots', 16: 'Vikings', 15: 'Dolphins', 14: 'Rams', 13: 'Raiders', 12: 'Chiefs', 11: 'Colts', 10: 'Titans', 9: 'Packers', 8: 'Lions', 7: 'Broncos', 6: 'Cowboys', 5: 'Browns', 4: 'Bengals', 3: 'Bears', 2: 'Bills', 1: 'Falcons'}
    column_renames = {'Pick Rating (1 worst, 10 best)': 'rating', 'Position-Based Draft Pick': 'position_draft', 'Position-Based Season Finish': 'position_finish', 'Overall Draft Pick': 'ovr_draft', 'Overall Finish': 'ovr_finish', 'Total Points': 'pts_total', 'Number of Weeks Missed': 'wks_out', 'Average Weekly Scoring': 'pts_avg', 'Position': 'pos'}
    try:    
        fantasyTeamsKey = getFantasyTeams(espn_s2, swid, url2)
    except:
        return 'Error retrieving data from API'
    playerData = getSeasonResults(espn_s2, swid, url2, positionsKey, nflTeamsKey, leagueId, seasonId)
    draftData = getDraftResults(espn_s2, swid, url2, playerData, fantasyTeamsKey)
    initial_df = pd.DataFrame(draftData.values()).drop(columns=['nflTeam'])
    df = initial_processing(initial_df, column_renames)
    processed_df = process_season(df, ['ovr_finish'], ['pts_total', 'pts_avg'], [], draft_perform_ratio=True, log_positions=True, top_finish=True)

    with open('wrapped/model/model_features.pkl', 'rb') as f:
        model_features = pickle.load(f)
    with open('wrapped/model/model_pkl.pkl', 'rb') as f:
        model = pickle.load(f)
    for feature in model_features:
        if feature not in processed_df.columns:
            print(feature)
            processed_df[feature] = 0
    #processed_df.to_csv('temppp.csv')
    processed_df.fillna(0, inplace=True)
    processed_df['rating'] = model.predict(processed_df[model_features]).round(3)
    with open('wrapped/static/draft_data.pkl', 'wb') as f:
        pickle.dump(processed_df, f)
    #processed_df.rename(columns={'position_draft': 'Position-Based Draft Pick', 'position_finish': 'Position-Based Season Finish', 'pts_total': 'Total Points', 'pts_avg': 'Average Points', 'rating': 'Rating', 'ovr_draft': 'Overall Draft Pick'})[['Overall Draft Pick', 'Player Name', 'Fantasy Team', 'Position', 'Position-Based Draft Pick', 'Position-Based Season Finish', 'Total Points', 'Average Points', 'Rating']])#.to_html('wrapped/templates/generated_draft_results.html', index=False)

def color_picks(df):
    if df['rating'] > 7:
        return ['background-color: green']*5
    elif df['rating'] > 3:
        return ['background-color: yellow']*5
    else:
        return ['background-color: red']*5



if __name__ == '__main__':
    
    leagueId = 39276
    seasonId = 2020
    swid = '52D54CB4-4327-465C-954C-B44327565CE4'
    espn_s2 = 'AEBnWn0Q%2FQq3y30XLqg2RtnOgZntUFEoOOEeDAdAGw6dknSQ7yZKbP4B9CZvcX%2FtRfl8mCmo2kGqf6FVtXHGc7mZMfxvPZxzLtD%2FoxD5dHrhhszJuotzsKdU5YynGsX3FIC7Gt9WBJ0uK%2B%2BDaRvEpWgLjGtKyArcxY8vdZnkx%2FdfQdCi5EKIOJTvIjY43geIECUNfpbmfkDurg6RaerrozFMfHuCceDAe7QvbS9t%2FYNERrfNZpc86J0A5k1OOZUK7uZxLuImUKd09J7sWjnN4yad'
    get_draft_df(leagueId, seasonId, swid, espn_s2)