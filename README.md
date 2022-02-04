# espn-ffb-wrapped

This project is a full stack/data science ESPN Fantasy Football league season analysis website that can be accessed (here)[https://fast-plains-72353.herokuapp.com/]. The backend is Python with Flask that links to front-end HTML/CSS and the entire thing is deployed using Heroku.

The python scripts gather data using the ESPN fantasy football API (which is essentially undocumented) with *app.py* that controls the Flask/front-end. The *draft.py* file assembles draft information from the league for the indicated season and then uses player performance data to evaluate draft picks on a trained model trained (here)[https://github.com/ethanglaser/espn-fantasy-football/tree/model_updates]. The *headtohead.py* script originated (here)[https://github.com/ethanglaser/espn-ffb-schedule-analysis] and now includes individual and team performance data, as well as information specific to various teams in the league. Navigating the API was quite tedious, with minimal resources to help but (this)[https://stmorse.github.io/journal/espn-fantasy-v3.html] helped with getting started.

The front-end was developed from scratch and is my first time developing in HTML so don't judge too hard.

Once you navigate to the (website)[https://fast-plains-72353.herokuapp.com/], it should be relatively self explanatory. The cookies aren't ideal but so far there appears to be no alternative.

This is an ongoing project and the variety of analysis, user interface, error handling, and overall quality will continue to improve.