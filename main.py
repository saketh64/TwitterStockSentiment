'''
Make sure to have Flask and textblob installed.

pip install textblob
pip install flask

TODO: most recent or popular?
'''
import requests
import base64
import nltk
from nltk.corpus import stopwords
import string
import re
import json
import datetime
from collections import Counter
from flask import Flask
from flask import request
from flask import jsonify
from textblob import TextBlob
from secret_keys import client_key
from secret_keys import client_secret
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')

app = Flask(__name__)

base_url = 'https://api.twitter.com/'
search_url = '{}1.1/search/tweets.json'.format(base_url)

data = []

def set_auth_header():

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

@app.route("/getpastdata")
def pastdata():
    stock = request.args.get('name')

    with open('data.txt', 'r') as outfile:
        data = json.load(outfile)

        result = {}
        result["C"] = getdataforstockfilter(stock, "C", data)
        result["D"] = getdataforstockfilter(stock, "D", data)
        result["H"] = getdataforstockfilter(stock, "H", data)
        result["N"] = getdataforstockfilter(stock, "N", data)
        result["None"] = getdataforstockfilter(stock, "None", data)

        return jsonify(result)

def getdataforstockfilter(stock, filter, data):
    result = []
    associatedWords = [x["data"]["related_sentiments"] for x in data["main"] if (x["name"] == stock) and (x["filter"] == filter)]
    words = {}
    for item in associatedWords:
        for word in item.keys():
            if (word in words.keys()):
                words[word] += 1
            else:
                words[word] = 1
    mostFrequentWords = dict(Counter(words).most_common(5))
    for word in mostFrequentWords.keys():
        values = []
        for item in associatedWords:
            if (word in item.keys()):
                values.append({"value": item[word]})
            else:
                values.append({"value": 0})
        item = [{"word": word}, {"values": values}]
        result.append(item)

    return result

@app.route('/getresults')
def index():
    results = {}

    query = request.args.get('query')
    keyword_filter = request.args.get('filter')
    tweets = get_tweets(query)
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

    # UNCOMMENT THIS TO PRINT LOGS TO FILE (not during testing)

    with open('data.txt', 'a') as outfile:
        now = datetime.datetime.now()
        outfile.write("{\"name\": \"" + query + "\", \"filter\": \"" + keyword_filter + "\", \"date\": \"" + str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "\", \"data\": ")
        json.dump(results, outfile)
        outfile.write("},\n")


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
Function that gets the 100 most tweets for a specific query
Returns a list of the 100 tweets
'''
def get_tweets(query):
    search_params = {
        'q': query,
        'result_type': 'recent',
        'exclude':'retweets',
        'count': 100,
    }

    search_resp = requests.get(search_url, headers=search_headers, params=search_params)
    tweet_data = search_resp.json()
    max_id = tweet_data['search_metadata']['max_id']
    tweets = []
    for x in tweet_data['statuses']:
        tweets.append(x['text'])

    for i in range(5):
        search_params = {
            'q': query,
            'result_type': 'recent',
            'exclude':'retweets',
            'count': 100,
            'max_id': max_id
        }
        search_resp = requests.get(search_url, headers=search_headers, params=search_params)
        tweet_data = search_resp.json()
        max_id = tweet_data['search_metadata']['max_id']
        for x in tweet_data['statuses']:
            tweets.append(x['text'])

    print(len(tweets))
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
    cachedStopWordsCapitals = set([i.capitalize() for i in stopwords.words("english")])

    #Loop through all the tweets

    for i in range (len(listOfTweets)):

        filteredTweet = listOfTweets[i]

        #---------------------------------------------Pre Processing the tweets --------------------------------------------------

        #Eliminates stop words
        filteredTweet = ' '.join([word for word in filteredTweet.split() if word not in (cachedStopWords and cachedStopWordsCapitals)])

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
                word = word.replace("’", "")
                if word and word[0] != '#' and word[0] != '$' and word[0] != '@' and word != "..." and word != '\'' :
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





    return filteredTweets





if __name__== '__main__':
    app.run(debug=False)
