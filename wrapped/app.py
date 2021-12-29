from flask import Flask, render_template, request, Response, send_file, redirect, url_for
from wrapped.headtohead import *

 
app = Flask(__name__)

@app.route('/info', methods = ['POST', 'GET'])
def data():
    if request.method == 'GET':
        #idk what to put here or if GET is even necessary
        pass
    if request.method == 'POST':
        if request.form.get("Submit", False) == 'Submit':
            try:
                league_id = request.form.get("league_id", False)
                season_id = request.form.get("season_id", False)
                swid, espn_s2 = request.form.get("swid", False), request.form.get("espn_s2", False)
                a = get_h2h(league_id, season_id, swid, espn_s2)
                if a:
                    return f"{a}"
                try:
                    return render_template('league_results.html')
                    league_results(league_id)
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
    #if request.method == 'POST':
    if request.form.get("h2h", False) == 'Head to head':
        return render_template('headtohead.html')
    elif request.form.get("ss", False) == 'Same schedule':
        return render_template('sameschedule.html')
    elif request.form.get("team", False) == 'Team1':
        return f"COMING SOON"
    else:
        return f"ERROR"

@app.route("/get-file")
def get_file():
    return send_file("requirements.txt", as_attachment=True)