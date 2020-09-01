from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from server import tmdb_script, ost_script, defaults, welfords_algorithm
import os

ENV = 'dev'  # DON'T FORGET TO CHANGE TO prod WHEN DEPLOYING TO A PRODUCTION SERVER
app = Flask(__name__)

########################################################################################################################

if ENV == 'dev':
    app.debug = True
    app.testing = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:{0}@localhost/FeelMData'.format(
        os.environ.get('DB_PASSWORD'))
elif ENV == 'prod':
    app.debug = False
    app.testing = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

########################################################################################################################

#  initialize TMDB API
tmdb_script.initiate_api(os.environ.get('TMDB_KEY'))
#  initialize OpenSubtitles API
ost_script.login(os.environ.get('OST_USER'), os.environ.get('OST_PASSWORD'))
#  initialize Welford's algorithm for the normal distribution calculation of the movie sentiment scores (smiley faces)
welfords_algorithm.initialize([movie_tuple[1] for movie_tuple in defaults.initial_movie_scores])
#  database initialization happens automatically in the db_and_models.py script

########################################################################################################################

#  import here only to work around circular imports
from server import routes

