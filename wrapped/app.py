from flask import Flask, render_template, request, Response, send_file, redirect, url_for
from wrapped.headtohead import *
from wrapped.draft import *
import os


app = Flask(__name__)
current_dir = os.path.dirname(__file__)

@app.route('/info', methods = ['POST', 'GET'])
def data():
    if request.method == 'POST':
        if request.form.get("Submit", False) == 'Submit':
            league_id = request.form.get("league_id", False)
            season_id = request.form.get("season_id", False)
            swid, espn_s2 = request.form.get("swid", False), request.form.get("espn_s2", False)
            for file in os.listdir(os.path.join(current_dir, 'templates/')):
                if 'generated' in str(file):
                    os.remove(os.path.join(current_dir, 'templates/' + file))
            a = get_h2h(league_id, season_id, swid, espn_s2)
            b = get_draft_df(league_id, season_id, swid, espn_s2)
            # try:
            #     get_draft_df(league_id, season_id, swid, espn_s2)
            # except:
            #     return f"Error with draft data."
            if a or b:
                if str(league_id) == '39276' and int(season_id) < 2018:
                    return render_template('boi.html')
                if a:
                    return f"{a}"
                if b:
                    return f"{b}"
            try:
                with open('wrapped/static/team_names.pkl', 'rb') as f:
                    teams = pickle.load(f)
                with open('wrapped/static/league_name.txt', 'r') as f:
                    league_name = f.read()
                return render_template('results_home.html', league_name=league_name, teams=[teams[team]['name'] for team in teams.keys()])
            except:
                return f"Error redirecting to league results."

        if request.form.get("Info", False) == 'Info':
            return render_template('info.html')

@app.route('/info', methods = ['POST', 'GET'])
def info():
        if request.form.get("Home", False) == 'Home':
            home()

def display_loading_screen():
    return render_template('loading_screen.html')

@app.route('/', methods = ['POST', 'GET'])
def home():
    return render_template('league_form.html')

@app.route('/league_results', methods = ['POST'])
def league_results():
    with open('wrapped/static/team_names.pkl', 'rb') as f:
        teams = pickle.load(f)
    team_names = [teams[team]['name'] for team in teams.keys()]
    if request.form.get("h2h", False) == 'Head to head':
        return render_template('results_h2h.html', teams=team_names)
    elif request.form.get("ss", False) == 'Same schedule':
        return render_template('results_ss.html', teams=team_names)
    elif request.form.get("home", False) == 'Home' or request.form.get("teams", False) == 'Teams':
        with open('wrapped/static/league_name.txt', 'r') as f:
            league_name = f.read()
        return render_template('results_home.html', teams=team_names, league_name=league_name)
    elif request.form.get("draft", False) == 'Draft analysis':
        return render_template('results_draft.html', teams=team_names)
    elif request.form.get("leader", False) == 'Leaderboard':
        t, d, t_d, d_d, isl, tsl, dsl = leaderboard(status=True)
        return render_template('results_leaderboard.html', teams=t, df=d, t_df=t_d, d_df=d_d, ind_scoring_leaders=isl, team_scoring_leaders=tsl, draft_scoring_leaders=dsl)
        # with open('wrapped/static/roster_df.pkl', 'rb') as f:
        #     df = pickle.load(f)
        # return render_template('results_leaderboard.html', teams=team_names, df=df)
    else:
        with open('wrapped/static/pie_info.pkl', 'rb') as f:
            pie_info = pickle.load(f)
        for team in teams.keys():
            if request.form.get('team', False) == teams[team]['name']:
                return render_template('team_page.html', actualname=teams[team]['name'], teamname='team' + str(team), record=teams[team]['record'], expected_wins=round(teams[team]['expected wins'], 3), teams=team_names, data1=pie_info[team][0])#, data2=pie_info[team][1])

@app.route("/league_results", methods = ['GET'])
def leaderboard(status=False):
    with open('wrapped/static/roster_df.pkl', 'rb') as f:
        df = pickle.load(f)
    team_names = df['team name'].unique()
    constraints = {}
    week_constraint = request.args.get('lead_week', False)
    if week_constraint and week_constraint != 'all':
        constraints['week'] = int(week_constraint)
    team_constraint = request.args.get('lead_team', False)
    if team_constraint and team_constraint != 'all':
        constraints['team name'] = team_constraint
    position_constraint = request.args.get('lead_position', False)
    if position_constraint and position_constraint != 'all':
        constraints['position'] = position_constraint
    number_constraint = request.args.get('lead_number', False)
    if number_constraint:
        n = int(number_constraint)
    else:
        n = 10
    top_constraint = request.args.get('lead_top', False)
    if top_constraint == 'worst':
        best = False
    else:
        best = True
    if os.path.isfile(os.path.join(current_dir, 'templates/generated_ind_scoring_leaders_stats.html')):
        os.remove(os.path.join(current_dir, 'templates/generated_ind_scoring_leaders_stats.html'))
    ind_scoring_leaders = get_performance_leaders(df, constraints=constraints, n=n, best=best).rename(columns={'score': 'Score', 'player': 'Player', 'position': 'Position', 'team name': 'Team Name', 'week': 'Week'})[['Score', 'Player', 'Position', 'Team Name', 'Week']].to_html(index=False)
    
    with open('wrapped/static/weekly_team_scores.pkl', 'rb') as f:
        t_df = pickle.load(f)
    t_constraints = {}
    t_week_constraint = request.args.get('t_lead_week', False)
    if t_week_constraint and t_week_constraint != 'all':
        t_constraints['week'] = int(t_week_constraint)
    t_team_constraint = request.args.get('t_lead_team', False)
    if t_team_constraint and t_team_constraint != 'all':
        t_constraints['team name'] = t_team_constraint
    t_number_constraint = request.args.get('t_lead_number', False)
    if t_number_constraint:
        t_n = int(t_number_constraint)
    else:
        t_n = 10
    t_top_constraint = request.args.get('t_lead_top', False)
    if t_top_constraint == 'worst':
        t_best = False
    else:
        t_best = True
    #replace with get_team_performance_leaders
    if os.path.isfile(os.path.join(current_dir, 'templates/generated_team_scoring_leaders_stats.html')):
        os.remove(os.path.join(current_dir, 'templates/generated_team_scoring_leaders_stats.html'))
    team_scoring_leaders = get_performance_leaders(t_df, constraints=t_constraints, n=t_n, best=t_best, starters_only=False).rename(columns={'score': 'Score', 'team name': 'Team Name', 'week': 'Week'})[['Score', 'Team Name', 'Week']].to_html(index=False)    
    
    with open('wrapped/static/draft_data.pkl', 'rb') as f:
        d_df = pickle.load(f)
    d_constraints = {}
    d_position_constraint = request.args.get('d_lead_position', False)
    if d_position_constraint and d_position_constraint != 'all':
        d_constraints['Position'] = d_position_constraint
    d_team_constraint = request.args.get('d_lead_team', False)
    if d_team_constraint and d_team_constraint != 'all':
        d_constraints['Fantasy Team'] = d_team_constraint
    d_number_constraint = request.args.get('d_lead_number', False)
    if d_number_constraint:
        d_n = int(d_number_constraint)
    else:
        d_n = 10
    d_top_constraint = request.args.get('d_lead_top', False)
    if d_top_constraint == 'worst':
        d_best = False
    else:
        d_best = True
    #replace with get_team_performance_leaders
    if os.path.isfile(os.path.join(current_dir, 'templates/generated_draft_scoring_leaders_stats.html')):
        os.remove(os.path.join(current_dir, 'templates/generated_draft_scoring_leaders_stats.html'))
    draft_scoring_leaders = get_performance_leaders(d_df, constraints=d_constraints, n=d_n, best=d_best, starters_only=False, rating=True).rename(columns={'position_draft': 'Position-Based Draft Pick', 'position_finish': 'Position-Based Season Finish', 'pts_total': 'Total Points', 'pts_avg': 'Average Points'})[['Player Name', 'Fantasy Team', 'Position', 'Position-Based Draft Pick', 'Position-Based Season Finish', 'Total Points', 'Average Points']].to_html(index=False)    
    
    if status:
        return team_names, df, t_df, d_df, ind_scoring_leaders, team_scoring_leaders, draft_scoring_leaders
    else:
        return render_template('results_leaderboard.html', teams=team_names, df=df, t_df=t_df, d_df=d_df, ind_scoring_leaders=ind_scoring_leaders, team_scoring_leaders=team_scoring_leaders, draft_scoring_leaders=draft_scoring_leaders)