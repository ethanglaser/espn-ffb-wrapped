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

@app.route('/', methods = ['POST', 'GET'])
def home():
    return render_template('league_form.html')

@app.route('/league_results', methods = ['POST', 'GET'])
def league_results():
    with open('wrapped/static/team_names.pkl', 'rb') as f:
        teams = pickle.load(f)
    team_names = [teams[team]['name'] for team in teams.keys()]
    if request.form.get("h2h", False) == 'Head to head':
        return render_template('results_h2h.html', teams=team_names)
    elif request.form.get("ss", False) == 'Same schedule':
        return render_template('results_ss.html', teams=team_names)
    elif request.form.get("home", False) == 'Home':
        return render_template('results_home.html', teams=team_names)
    elif request.form.get("draft", False) == 'Draft analysis':
        return render_template('results_draft.html', teams=team_names)
    elif request.form.get("leader", False) == 'Leaderboard':
        return render_template('results_leaderboard.html', teams=team_names)
    else:
        print("ab")
        for team in teams.keys():
            print(teams[team]['name'])
            if request.form.get(teams[team]['name'], False) == teams[team]['name']:
                return render_template('team_page.html', teamname=teams[team]['name'], record=teams[team]['record'], expected_wins=round(teams[team]['expected wins'], 3), teams=team_names)

@app.route("/get-file")
def get_file():
    return send_file("requirements.txt", as_attachment=True)