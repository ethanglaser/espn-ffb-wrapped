from flask import Flask, render_template, request, Response, send_file, redirect, url_for
from headtohead import *

 
app = Flask(__name__)
 
@app.route('/info', methods = ['POST', 'GET'])
def data():
    if request.method == 'GET':
        #idk what to put here or if GET is even necessary
        pass
    if request.method == 'POST':
        if request.form.get("Submit", False) == 'Submit':
            try:
                f1, f2 = get_h2h(request.form.get("league_id", False), request.form.get("season_id", False), request.form.get("swid", False), request.form.get("espn_s2", False))
            except:
                return f"Error: Invalid League ID, Season ID, or SWID"
            return send_file(f1, as_attachment=True)#, send_file(f2, as_attachment=True)
        if request.form.get("Info", False) == 'Info':
            return render_template('info.html')

@app.route('/info', methods = ['POST', 'GET'])
def info():
        if request.form.get("Home", False) == 'Home':
            home()

@app.route('/', methods = ['POST', 'GET'])
def home():
    return render_template('league_form.html')


# construct your app

@app.route("/get-file")
def get_file():
    return send_file("requirements.txt", as_attachment=True)