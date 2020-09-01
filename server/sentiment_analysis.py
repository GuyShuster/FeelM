from datetime import date, datetime, timedelta, time
from textblob import TextBlob
import seaborn as sns
import re
import functools


# Custom Exceptions


class SubtitleFileException(Exception):
    def __init__(self):
        super().__init__()


class SubtitleParsingException(Exception):
    def __init__(self):
        super().__init__()

########################################################################################################################


sns.set()


def create_subs_array(filename, encoding):
    with open(filename, 'r', encoding=encoding, errors='ignore') as file:
        current_sub = []
        lines = file.readlines()
        subs = []
        for line in reversed(lines):
            if re.match('\d+:\d+:\d+,\d+\s-->\s\d+:\d+:\d+,\d+.', line):
                times = line.strip('\n').split(' --> ')
                start = datetime.strptime(times[0], '%H:%M:%S,%f')
                end = datetime.strptime(times[1], '%H:%M:%S,%f')
                subs.insert(0, (''.join(current_sub), start, end))
                current_sub = []
                continue
            if line != '\n' and not line.strip('\n').isnumeric():
                current_sub.insert(0, line)
        return subs


# Helper Function to create equally divided time intervals
# start - Starting Time
# end - Ending Time
# delta - Interval Period
def create_intervals(start, end, delta):
    curr = start
    while curr <= end:
        curr = (datetime.combine(date.today(), curr) + delta).time()
        yield curr


# Main Function to Get Sentiment Data
# file - srt file location
# delta - time interval in minutes
def get_sentiment(file, encoding, delta=2):
    # Reading Subtitle
    try:
        subs = create_subs_array(file, encoding.lower())
    except Exception:
        raise SubtitleFileException()
    try:
        n = len(subs)
        # List to store the time periods
        intervals = []
        # Start, End and Delta
        start = time(0, 0, 0)
        end = subs[-1][2].time()
        delta = timedelta(minutes=delta)
        for result in create_intervals(start, end, delta):
            intervals.append(result)
        # List to store sentiment polarity
        sentiments = []

        index = 0
        m = len(intervals)
        # Collect and combine all the text in each time interval
        for i in range(m):
            text = ""
            for j in range(index, n):
                # Finding all subtitle text in the each time interval
                if subs[j][2].time() < intervals[i]:
                    text += subs[j][0]
                else:
                    break
            # Sentiment Analysis
            blob = TextBlob(text)
            pol = blob.sentiment.polarity
            sentiments.append(pol)
            index = j

        # Adding Initial State
        intervals.insert(0, time(0, 0, 0))
        sentiments.insert(0, 0.0)

        # return intervals, sentiments
        return [[(timestamp.hour*60*60 + timestamp.minute*60 + timestamp.second)*1000,  # total seconds * 1000
                 sentiments[i]] for i, timestamp in enumerate(intervals)]
    except Exception:
        raise SubtitleParsingException()


# Utility to find average sentiment
def average(lst):
    sentiment_sum = functools.reduce(lambda a, b: a + b, [item[1] for item in lst])
    return float(sentiment_sum) / len(lst)

