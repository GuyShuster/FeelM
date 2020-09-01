from server import db, defaults


class DBException(Exception):
    def __init__(self):
        super().__init__()


class SentimentHistory(db.Model):
    __tablename__ = 'SentimentHistory'
    id = db.Column(db.Integer, primary_key=True)
    movie_score = db.Column(db.Float)
    movie_imdb_id = db.Column(db.String(200))

    def __init__(self, movie_imdb_id, movie_score):
        self.movie_score = movie_score
        self.movie_imdb_id = movie_imdb_id


#  initialize db with default data if empty


try:
    if len(db.session.query(SentimentHistory).all()) < 100:  # if the initial 153 movies haven't been added
        for movie_tuple in defaults.initial_movie_scores:
            db.session.add(SentimentHistory(movie_tuple[0], movie_tuple[1]))
    db.session.commit()
except Exception:
    pass
