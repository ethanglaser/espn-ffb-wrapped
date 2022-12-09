from flask import Flask, render_template, request, Response, send_file, redirect, url_for
from wrapped.headtohead import *
from wrapped.draft import *
import os
import requests
from selenium import webdriver
import time

app = Flask(__name__)
current_dir = os.path.dirname(__file__)

def get_credentials(user=None):
    '''
    This function identifies the SWID and ESPN_S2 for a user using Selenium.
    
    The function will identify the default Chrome profile for a user on the
    machine, and open up a browser using this account.
    
    The user will be prompted to sign in to their ESPN account if they are
    not auto-signed in by their browser.
    
    The swid and espn_s2 cookies are identified and returned.
    '''
    # Get list of users on computer
    users = os.listdir('C:\Users')
    for i in ['All Users', 'Default', 'Default User', 'desktop.ini', 'Public']:
        users.remove(i)
    print("[FETCHING CREDENTIALS] All users: ", users)
    
    if user is None:
        # Select first user
        user = users[0]
        print("[FETCHING CREDENTIALS] Using user: {}".format(users[0]))
    
    # Locate and use the default Chrome profile for the user
    print("[FETCHING CREDENTIALS] Locating default Chrome profile...")
    options = webdriver.ChromeOptions() 
    options.add_argument(r'--user-data-dir=C:/Users/{}/AppData/Local/Google/Chrome/User Data'.format(user))
    options.add_argument('--profile-directory=Default')

    # Instantiate Chrome instance using Selenium and the default Chrome profile
    print("[FETCHING CREDENTIALS] Instantiating Chrome browser...")
    DRIVER_PATH = 'C://chromedriver.exe'
    try: 
        driver = webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=options)
    except:
        if "user data directory is already in use" in str(e):
            #driver.close()  # Close window
            raise Exception("Chrome is already open in another window. Please close all other Chrome windows and re-launch.")
    
    # Navigate to ESPN website for league and login
    driver.get('https://fantasy.espn.com/')
    print(driver.get_cookies())

    # Check if user is logged in automatically by browser
    cookies = [cookie["name"] for cookie in driver.get_cookies()] # Get list of cookie names
    if ("SWID" not in cookies) or ("espn_s2" not in cookies):
        # Wait for user to log in maunally
        print("[FETCHING CREDENTIALS] Login to ESPN account in browser.")
        driver.find_element_by_xpath('//*[@id="global-user-trigger"]').click()
        #driver.find_element_by_xpath('//*[@id="global-viewport"]/div[3]/div/ul[1]/li[7]/a').click()
        while True:
            time.sleep(5)
            cookies = [cookie["name"] for cookie in driver.get_cookies()] # Get updated list of cookie names
            if ("SWID" in cookies) and ("espn_s2" in cookies):
                print("[FETCHING CREDENTIALS] Login detected.")
                break;            
            print("[FETCHING CREDENTIALS] Login not detected... waiting 5 seconds...")
    else:
        print("[FETCHING CREDENTIALS] Login detected.")
        pass
           
    # Identify cookies for user
    swid, espn_s2 = None, None
    cookies = driver.get_cookies()
    for cookie in cookies:
        if cookie['name'] == 'SWID':
            swid = cookie['value'][1:-1]
        if cookie['name'] == 'espn_s2':
            espn_s2 = cookie['value']
    
    #return driver
    if swid is None:
        raise Exception("[FETCHING CREDENTIALS] ERROR: SWID cookie not found.")
    if espn_s2 is None:
        raise Exception("[FETCHING CREDENTIALS] ERROR: SWID cookie not found.")    
    
    # Close the browser        
    driver.close()
    
    print("[FETCHING CREDENTIALS] ESPN Credenitals:\n[FETCHING CREDENTIALS] ---------------------")
    print("[FETCHING CREDENTIALS] swid: {}\n[FETCHING CREDENTIALS] espn_s2: {}".format(swid, espn_s2))
    return swid, espn_s2


@app.route('/info', methods = ['POST', 'GET'])
def data():
    # OPEN WPM
    session = requests.Session()
    a_session = requests.Session()
    a_session.get('https://espn.com/')
    session_cookies = a_session.cookies
    cookies_dictionary = session_cookies.get_dict()
    print(cookies_dictionary)
    # other = requests.get(url="https://espn.com/")
    # #print(other.cookies._cookies)

    # #print(other.request._cookies._cookies)
    # r = a_session.post('https://espn.com', auth=('user', 'pass'),verify=False)
    # print(r.text.keys())
    print(get_credentials())


    if request.method == 'POST':
        if request.form.get("Submit", False) == 'Submit':
            league_id = request.form.get("league_id", False)
            season_id = request.form.get("season_id", False)
            swid, espn_s2 = request.form.get("swid", False), request.form.get("espn_s2", False)
            # aa = os.listdir(os.path.join(current_dir, 'templates/'))
            for file in os.listdir(os.path.join(current_dir, 'templates/')):
                if 'generated' in str(file):
                    os.remove(os.path.join(current_dir, 'templates/' + file))
            # bb = os.listdir(os.path.join(current_dir, 'templates/'))
            # if str(league_id) == '1303917':
            #     return f"{aa} {bb}"
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
        with open('wrapped/static/headtohead.pkl', 'rb') as f:
            headtohead = pickle.load(f)
        return render_template('results_h2h.html', teams=team_names, h2h=headtohead.to_html())
    elif request.form.get("ss", False) == 'Same schedule':
        with open('wrapped/static/sameschedule.pkl', 'rb') as f:
            sameschedule = pickle.load(f)
        return render_template('results_ss.html', teams=team_names, ss=sameschedule.to_html())
    elif request.form.get("home", False) == 'Home' or request.form.get("teams", False) == 'Teams':
        with open('wrapped/static/league_name.txt', 'r') as f:
            league_name = f.read()
        return render_template('results_home.html', teams=team_names, league_name=league_name)
    elif request.form.get("draft", False) == 'Draft analysis':
        with open('wrapped/static/draft_data.pkl', 'rb') as f:
            processed_df = pickle.load(f)
        #.to_html('wrapped/templates/generated_draft_results.html', index=False)

        return render_template('results_draft.html', teams=team_names, draft=processed_df.rename(columns={'position_draft': 'Position-Based Draft Pick', 'position_finish': 'Position-Based Season Finish', 'pts_total': 'Total Points', 'pts_avg': 'Average Points', 'rating': 'Rating', 'ovr_draft': 'Overall Draft Pick'})[['Overall Draft Pick', 'Player Name', 'Fantasy Team', 'Position', 'Position-Based Draft Pick', 'Position-Based Season Finish', 'Total Points', 'Average Points', 'Rating']].to_html(index=False))
    elif request.form.get("leader", False) == 'Leaderboard':
        t, d, t_d, d_d, isl, tsl, dsl = leaderboard(status=True)
        return render_template('results_leaderboard.html', teams=t, df=d, t_df=t_d, d_df=d_d, ind_scoring_leaders=isl, team_scoring_leaders=tsl, draft_scoring_leaders=dsl)
        # with open('wrapped/static/roster_df.pkl', 'rb') as f:
        #     df = pickle.load(f)
        # return render_template('results_leaderboard.html', teams=team_names, df=df)
    else:
        with open('wrapped/static/pie_info.pkl', 'rb') as f:
            pie_info = pickle.load(f)
        with open('wrapped/static/team_info.pkl', 'rb') as f2:
            team_info = pickle.load(f2)
        for team in teams.keys():
            if request.form.get('team', False) == teams[team]['name']:
                return render_template('team_page.html', actualname=teams[team]['name'], teamname='team' + str(team), record=teams[team]['record'], expected_wins=round(teams[team]['expected wins'], 3), teams=team_names, data1=pie_info[team][0], team_df_html=team_info[team]['team_df'].to_html(), team_roster_df_html=team_info[team]['team_roster_df'].to_html())#, data2=pie_info[team][1])

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
    
    draft_scoring_leaders = get_performance_leaders(d_df, constraints=d_constraints, n=d_n, best=d_best, starters_only=False, rating=True).rename(columns={'position_draft': 'Position-Based Draft Pick', 'position_finish': 'Position-Based Season Finish', 'pts_total': 'Total Points', 'pts_avg': 'Average Points'})[['Player Name', 'Fantasy Team', 'Position', 'Position-Based Draft Pick', 'Position-Based Season Finish', 'Total Points', 'Average Points']].to_html(index=False)    
    
    if status:
        return team_names, df, t_df, d_df, ind_scoring_leaders, team_scoring_leaders, draft_scoring_leaders
    else:
        return render_template('results_leaderboard.html', teams=team_names, df=df, t_df=t_df, d_df=d_df, ind_scoring_leaders=ind_scoring_leaders, team_scoring_leaders=team_scoring_leaders, draft_scoring_leaders=draft_scoring_leaders)