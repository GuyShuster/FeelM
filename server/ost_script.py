from pythonopensubtitles.opensubtitles import OpenSubtitles


# Custom Exceptions


class OSTDownloadException(Exception):
    def __init__(self):
        super().__init__()

########################################################################################################################


ost = OpenSubtitles()
logged_in = False


def login(username, password):
    global logged_in
    try:
        ost.login(username, password)
        logged_in = True
    except Exception:
        logged_in = False


def download_srt(movie_id):
    try:
        data = ost.search_subtitles([{'imdbid': movie_id, 'sublanguageid': 'eng'}])
        if len(data) == 0:
            raise Exception("Wrong movie ID or subtitles not available for this movie")
        max_index = 0
        max_rating = 0
        index = 0
        for srt in data:
            if srt['LanguageName'] == 'English' and float(srt['SubRating']) > max_rating:
                max_rating = float(srt['SubRating'])
                max_index = index
            index = index+1
        id_subtitle_file = data[max_index]['IDSubtitleFile']

        ost.download_subtitles([id_subtitle_file],
                               override_filenames={id_subtitle_file: str(movie_id)},
                               output_directory='',
                               extension='srt')
        try:
            f = open(movie_id, 'r')
        except Exception:
            raise OSTDownloadException()
        finally:
            f.close()

        return data[max_index]['SubEncoding']
    except Exception:
        raise OSTDownloadException()


