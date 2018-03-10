'''
Make sure to have Flask and textblob installed.

pip install textblob
pip install flask
'''

from flask import Flask
from flask import request
from textblob import TextBlob
app = Flask(__name__)


@app.route('/getresults')
def index():
    query = request.args.get('query')
    filter = request.args.get('filter')

'''
Function that gets average sentiment over list of tweets (strings).
'''
def get_overall_sentiment(tweets):
    if (len(tweets) < 1):
        return str(0.0)

    sentiment = 0.0
    for tweet in tweets:
        sentiment += get_tweet_sentiment(tweet)
    sentiment = sentiment / len(tweets)

    return sentiment

'''
Function that returns sentiment of a single tweet (one string).
Returns floating point number corresponding to sentiment.
'''
def get_tweet_sentiment(tweet):
    blob = TextBlob(tweet)
    return blob.sentiment.polarity

if __name__== '__main__':
    app.run(debug=False)
