from flask import render_template, request, session
from server import app, ost_script, defaults, tmdb_script, welfords_algorithm, sentiment_analysis, db
from server.db_and_models import SentimentHistory, DBException
import os
import scipy.stats as st


def add_film_description(movies):
    """ Gets a dictionary of dictionaries and adds a pretty printed description of the film metadata """
    for key, movie in movies.items():
        desc = ''
        if movie['genre'] != '':
            desc += movie['genre'].replace(',', '/') + ', '
        if movie['director'] != '':
            desc += 'directed by ' + movie['director'] + ', '
        if movie['release_date'] != '':
            desc += 'released on ' + movie['release_date'] + ', '
        if len(desc) > 0:
            desc = desc[0:-2] + '.'
            movie['description'] = desc[0].capitalize() + desc[1:]


def predict_sentiment(movie_id, avg_score):
    """ Gets an average score for the current movie, and predicts it's sentiment based on previous movie searches """
    try:
        if db.session.query(SentimentHistory).filter(SentimentHistory.movie_imdb_id == movie_id).count() == 0:
            welfords_algorithm.add(avg_score)  # if the movie wasn't already in the average score, add it
            data = SentimentHistory(movie_id, avg_score)
            db.session.add(data)
            if len(db.session.query(SentimentHistory).all()) > 9500:  # Heroku allows about 10000 rows on the free plan
                db.session.delete(db.session.query(SentimentHistory).first())
                # keep the average score updated to the latest movies
                welfords_algorithm.initialize([movie.movie_score for movie in db.session.query(SentimentHistory).all()])

            db.session.commit()
    except Exception:
        raise DBException()

    mean = welfords_algorithm.welfrod.mean
    std = welfords_algorithm.welfrod.std

    # normal distribution weights
    very_negative = 0.2
    negative = 0.2
    neutral = 0.2
    positive = 0.2
    # very_positive = 0.2

    # normal distribution z-scores
    first_z_score = st.norm.ppf(very_negative)
    second_z_score = st.norm.ppf(very_negative + negative)
    third_z_score = st.norm.ppf(very_negative + negative + neutral)
    fourth_z_score = st.norm.ppf(very_negative + negative + neutral + positive)

    # boundaries that separate film sentiment grades according to the z-score standard formula
    first_boundary = first_z_score * std + mean
    second_boundary = second_z_score * std + mean
    third_boundary = third_z_score * std + mean
    fourth_boundary = fourth_z_score * std + mean

    if -1 <= avg_score < first_boundary:
        return 'Very Negative'
    elif first_boundary <= avg_score < second_boundary:
        return 'Negative'
    elif second_boundary <= avg_score < third_boundary:
        return 'Neutral'
    elif third_boundary <= avg_score < fourth_boundary:
        return 'Positive'
    else:  # has to be fourth_boundary <= avg_score < 1
        return 'Very Positive'


#  initialize defaults to appear on the opening page
add_film_description(defaults.default_movies)


@app.route('/', methods=['POST', 'GET'])
def index():
    error_message = None

    if request.method == 'GET':
        #  Each time a user accesses the website, we want to "freshly" log in and initialize the default searched movies
        session['searched_movies'] = defaults.default_movies
        ost_script.login(os.environ.get('OST_USER'), os.environ.get('OST_PASSWORD'))
        if not ost_script.logged_in:
            error_message = '''We could not log in to the Open Subtitles API.
            Please try to reload the page in a couple of minutes.
            If this message shows up again, please raise an issue on our github repository 
            (link at the bottom of this page).'''
        return render_template('index.html', movies=session['searched_movies'], graph_data=defaults.default_graph,
                               error_message=error_message, sentiment=predict_sentiment(defaults.default_movie[0],
                                                                                        defaults.default_movie[1]))
    else:
        if 'search' in request.form:
            movie_name = request.form['movie']
            try:
                session['searched_movies'] = tmdb_script.tmdb_api(movie_name)
                add_film_description(session['searched_movies'])
                return render_template('index.html', movies=session['searched_movies'], scroll='content_section_1')
            except tmdb_script.TMDBConnectionException:
                error_message = '''We could not connect to the TMDB API.
                            Please try to reload the page in a couple of minutes.
                            If this message shows up again, please raise an issue on our github repository 
                            (link at the bottom of this page).'''
                return render_template('index.html', movies=session['searched_movies'], error_message=error_message)
            except tmdb_script.TMDBParsingException:
                error_message = '''Could not parse the data from the TMDB API correctly.
                            Please reload the page and try searching a different movie.
                            If this message shows up again, please raise an issue on our github repository 
                            (link at the bottom of this page).'''
                return render_template('index.html', movies=session['searched_movies'], error_message=error_message)
        else:
            movie_id = request.form['movie_id']
            try:
                encoding = ost_script.download_srt(movie_id)
            except ost_script.OSTDownloadException:
                error_message = '''Could not download the chosen movie.
                            Please reload the page and try it one more time.
                            If you can find the chosen movie on the Open Subtitle website but can't analyze it here, 
                            please raise an issue on our github repository 
                            (link at the bottom of this page).'''
                return render_template('index.html', movies=session['searched_movies'], error_message=error_message)
            try:
                sentiment_result = sentiment_analysis.get_sentiment(str(movie_id), encoding)
                graph_data = defaults.default_graph
                graph_data['series'] = [{'name': request.form['movie_name'], 'data': sentiment_result}]
                os.remove(str(movie_id))

                sentiment = predict_sentiment(movie_id, sentiment_analysis.average(sentiment_result))
                return render_template('index.html', movies=session['searched_movies'], graph_data=graph_data, sentiment=sentiment)
            except sentiment_analysis.SubtitleFileException:
                error_message = '''Could not read the downloaded subtitle file correctly.
                                            Please reload the page and try it one more time.
                                            If this message shows up again, 
                                            please raise an issue on our github repository 
                                            (link at the bottom of this page).'''
                return render_template('index.html', movies=session['searched_movies'], error_message=error_message)
            except sentiment_analysis.SubtitleParsingException:
                error_message = '''Could not parse the downloaded subtitle correctly.
                                            Please reload the page and try it one more time.
                                            If this message shows up again, 
                                            please raise an issue on our github repository 
                                            (link at the bottom of this page).'''
                return render_template('index.html', movies=session['searched_movies'], error_message=error_message)
            except DBException:
                error_message = '''This is a database exception.
                                please raise an issue on our github repository 
                                (link at the bottom of this page).'''
                return render_template('index.html', movies=session['searched_movies'], error_message=error_message)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/data_analysis')
def data_analysis():
    return render_template('data_analysis.html')


@app.route('/top_results')
def top_results():
    return render_template('top_results.html', movies=defaults.top_results_default_movies)
