'''
Make sure to have Flask and textblob installed.

pip install textblob
pip install flask

TODO: most recent or popular?
'''
import requests
import base64
import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')
#nltk.download('stopwords')
from nltk.corpus import stopwords
import string
import re
from collections import Counter
from flask import Flask
from flask import request
from flask import jsonify
from textblob import TextBlob
from secret_keys import client_key
from secret_keys import client_secret
app = Flask(__name__)

base_url = 'https://api.twitter.com/'
search_url = '{}1.1/search/tweets.json'.format(base_url)

def set_auth_header():
    client_key = 'CAyOqosKb6fU86YC1a8zxV2l0'
    client_secret = 'PTCnPc4EmCx0vV9UNQxY5AVz07j2y3QXAkf4dweQfayoDmyqLp'

    key_secret = '{}:{}'.format(client_key, client_secret).encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret)
    b64_encoded_key = b64_encoded_key.decode('ascii')


    base_url = 'https://api.twitter.com/'
    auth_url = '{}oauth2/token'.format(base_url)

    auth_headers = {
        'Authorization': 'Basic {}'.format(b64_encoded_key),
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    auth_data = {
        'grant_type': 'client_credentials'
    }

    auth_resp = requests.post(auth_url, headers=auth_headers, data=auth_data)

    access_token = auth_resp.json()['access_token']

    return { 'Authorization': 'Bearer {}'.format(access_token) }

search_headers = set_auth_header()



print(client_key)

@app.route('/getresults')
def index():
    results = {}

    query = request.args.get('query')
    keyword_filter = request.args.get('filter')
    tweets = get_tweets(query)
    print(tweets)
    sentiment = get_overall_sentiment(tweets)
    results['sentiment'] = sentiment
    words = get_most_related_words(tweets, keyword_filter, query)
    word_sentiments = {}
    for word in words:
        print('grabbing tweet')
        print(word)
        word_tweets = get_tweets(word[0])
        word_sentiments[word[0]] = get_overall_sentiment(word_tweets)

    results['related_sentiments'] = word_sentiments

    return jsonify(results)

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


'''
Function that sets the authorization header
Returns the Authorization header
'''
def set_auth_header():
    client_key = 'CAyOqosKb6fU86YC1a8zxV2l0'
    client_secret = 'PTCnPc4EmCx0vV9UNQxY5AVz07j2y3QXAkf4dweQfayoDmyqLp'

    key_secret = '{}:{}'.format(client_key, client_secret).encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret)
    b64_encoded_key = b64_encoded_key.decode('ascii')


    base_url = 'https://api.twitter.com/'
    auth_url = '{}oauth2/token'.format(base_url)

    auth_headers = {
        'Authorization': 'Basic {}'.format(b64_encoded_key),
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    auth_data = {
        'grant_type': 'client_credentials'
    }

    auth_resp = requests.post(auth_url, headers=auth_headers, data=auth_data)

    access_token = auth_resp.json()['access_token']

    return { 'Authorization': 'Bearer {}'.format(access_token) }

'''
Function that gets the 100 most tweets for a specific query
Returns a list of the 100 tweets
'''
def get_tweets(query):
    search_params = {
        'q': query,
        'result_type': 'recent',
        'count': 100,
    }

    search_resp = requests.get(search_url, headers=search_headers, params=search_params)
    tweet_data = search_resp.json()
    tweets = []
    for x in tweet_data['statuses']:
        tweets.append(x['text'])

    return tweets


def get_most_related_words(tweets, keyword_filter, query):
    combined = clean_tweet(tweets, keyword_filter, query)
    words = Counter(combined.split())
    return words.most_common(5)



def clean_tweet(listOfTweets, filterType, queryWord):

    #Initialize new Array
    filteredTweets = ""

    #Obtaining all stop words
    cachedStopWords = set(stopwords.words("english"))

    #Loop through all the tweets

    for i in range (len(listOfTweets)):

        filteredTweet = listOfTweets[i]

        #---------------------------------------------Pre Processing the tweets --------------------------------------------------

        #Eliminates stop words
        filteredTweet = ' '.join([word for word in filteredTweet.split() if word not in cachedStopWords])

        filteredTweet = filteredTweet.replace('RT', "")

        filteredTweet = filteredTweet.replace(queryWord, "")




        #---------------------------------------------Filtering words based on Filter Choice --------------------------------------------------

        if(filterType == 'C'):
            newTweetWithoutProperNouns = ""


            words = filteredTweet.split()
            for word in words:
                if word and word[0].isupper() and word[0] != '#' and word[0] != '$' and word[0] != '@':
                     word = re.sub(r'[^\w\s]', '', word)
                     newTweetWithoutProperNouns += word + " "

            filteredTweets += newTweetWithoutProperNouns + " "
        elif(filterType == 'D'):
            newTweetWithStockTag = ""
            words = filteredTweet.split()
            for word in words:
                if word and word[0] == '$':
                    newTweetWithStockTag += word + " "

            filteredTweets += newTweetWithStockTag + " "
        elif (filterType == 'H'):
            newTweetWithHashTag = ""
            words = filteredTweet.split()
            for word in words:
                if word and word[0] == '#':
                    newTweetWithHashTag += word + " "

            filteredTweets +=  newTweetWithHashTag + " "
        elif(filterType == 'N'):

            newFilteredTweet = ""
            words = filteredTweet.split()
            punctuation = string.punctuation
            punctuation = punctuation.replace('@', "").replace('#', "").replace('$', "")

            words = [''.join(c for c in s if c not in punctuation) for s in words]
            for word in words:
                if word and word[0] != '#' and word[0] != '$' and word[0] != '@':
                    newFilteredTweet += word + " "
            # function to test if something is a noun
            is_noun = lambda pos: pos[:2] == 'NN'
            # do the nlp stuff
            tokenized = nltk.word_tokenize(newFilteredTweet)

            nouns = ' '.join([word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)])

            filteredTweets += nouns + " "

        else:

            filteredTweet = re.sub(r'[^\w\s]', '', filteredTweet)
            filteredTweets += filteredTweet + " "
            #print (filteredTweets)





    return filteredTweets





if __name__== '__main__':
    app.run(debug=False)


