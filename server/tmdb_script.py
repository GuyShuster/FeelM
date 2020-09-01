from tmdbv3api import TMDb, Movie, Genre, Configuration
from datetime import datetime
from requests import exceptions


# Custom Exceptions


class TMDBConnectionException(Exception):
    def __init__(self):
        super().__init__()


class TMDBParsingException(Exception):
    def __init__(self):
        super().__init__()

########################################################################################################################


def initiate_api(api_key):
    tmdb = TMDb()
    tmdb.api_key = api_key
    tmdb.language = 'en'
    tmdb.debug = True


def tmdb_api(movie_name):
    try:
        movie = Movie()
        genre = Genre()
        config = Configuration()
        info = config.info()
        secure_base_url = info.images['secure_base_url']
        poster_size = "w500/"
        ret_dict = {}
        genres = {}
        genres_objs = genre.movie_list()
        for g in genres_objs:
            genres[g.id] = g.name
        movie_list = movie.search(movie_name)
        for i, m in enumerate(movie_list):
            external_ids = movie.external_ids(m.id)
            if 'imdb_id' in external_ids and external_ids['imdb_id'] is not None:
                external_id = external_ids['imdb_id'][2:]
                release_date = ""
                if hasattr(m, 'release_date') and m.release_date != "":
                    rel_date = m.release_date
                    date_obj = datetime.strptime(rel_date, '%Y-%m-%d')
                    release_date = date_obj.strftime('%d %B %Y')
                poster_path = ""
                if hasattr(m, 'poster_path') and m.poster_path != "" and str(m.poster_path) != "None":
                    poster_path = secure_base_url + poster_size + str(m.poster_path)
                ret_dict[i] = {
                    'title': m.title if hasattr(m, 'title') else "",
                    'plot': m.overview if hasattr(m, 'overview') else "",
                    'image':  poster_path,
                    'director': "",
                    'release_date': release_date,
                    'genre': ', '.join(map(lambda x: genres[x], m.genre_ids)) if hasattr(m, 'genre_ids') else "",
                    'movie_id': external_id
                }
        return ret_dict

    except exceptions.ConnectionError:
        raise TMDBConnectionException()
    except Exception:
        raise TMDBParsingException()
