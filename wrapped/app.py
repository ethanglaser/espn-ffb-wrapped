from flask import Flask, render_template, request, Response, send_file, redirect, url_for
from wrapped.headtohead import *
import os


app = Flask(__name__)

@app.route('/info', methods = ['POST', 'GET'])
def data():
    if request.method == 'GET':
        #idk what to put here or if GET is even necessary
        pass
    if request.method == 'POST':
        if request.form.get("Submit", False) == 'Submit':
            try:
                if os.path.exists("wrapped/templates/sameschedule.html"):
                    os.remove("wrapped/templates/sameschedule.html")
                if os.path.exists("wrapped/templates/headtohead.html"):
                    os.remove("wrapped/templates/headtohead.html")
                league_id = request.form.get("league_id", False)
                season_id = request.form.get("season_id", False)
                swid, espn_s2 = request.form.get("swid", False), request.form.get("espn_s2", False)
                a = get_h2h(league_id, season_id, swid, espn_s2)
                if a:
                    return f"{a}"
                try:
                    with open('wrapped/static/team_names.pkl', 'rb') as f:
                        teams = pickle.load(f)
                    league_name = get_league_name(league_id, season_id, swid, espn_s2)
                    return render_template('results_home.html', league_name=league_name, teams=[teams[team]['name'] for team in teams.keys()])
                except:
                    return f"Error redirecting to league results."
                #return render_template('league_results.html')
                # try:
                #     f1, f2 = get_h2h(league_id, season_id, swid, espn_s2)
                #     #f1, f2 = get_h2h(request.form.get("league_id", False), request.form.get("season_id", False), request.form.get("swid", False), request.form.get("espn_s2", False))
                # except:
                #     return f"Error: Invalid League ID, Season ID, or SWID {league_id} {season_id} {swid} {espn_s2}"
            except:
                return f"could not get from request.form"
            #return send_file(f1, as_attachment=True)#, send_file(f2, as_attachment=True)
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
        return render_template('results_home.html', teams=team_names)
    elif request.form.get("draft", False) == 'Draft analysis':
        return render_template('results_draft.html', teams=team_names)
    elif request.form.get("leader", False) == 'Leaderboard':
        t, d = leaderboard(status=True)
        return render_template('results_leaderboard.html', teams=t, df=d)
        # with open('wrapped/static/roster_df.pkl', 'rb') as f:
        #     df = pickle.load(f)
        # return render_template('results_leaderboard.html', teams=team_names, df=df)
    else:
        with open('wrapped/static/pie_info.pkl', 'rb') as f:
            pie_info = pickle.load(f)
        for team in teams.keys():
            if request.form.get('team', False) == teams[team]['name']:
                print(pie_info[team])
                return render_template('team_page.html', actualname=teams[team]['name'], teamname='team' + str(team), record=teams[team]['record'], expected_wins=round(teams[team]['expected wins'], 3), teams=team_names, data=pie_info[team])

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
    get_individual_performance_leaders(df, constraints=constraints, n=n, best=best).drop(columns=['team id', 'position id', 'roster slot id', 'roster slot']).to_html('wrapped/templates/generated/ind_scoring_leaders_stats.html', index=False)
    if status:
        return team_names, df
    else:
        return render_template('results_leaderboard.html', teams=team_names, df=df)