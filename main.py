import time
import tweepy
from polygon import RESTClient
import pandas as pd
import config
import matplotlib.pyplot as plt

import datetime

auth = tweepy.OAuthHandler(config.TWITTER_API_KEY, config.API_SECRET)
auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


class Listener(tweepy.Stream):
    tweets = []
    limit = 100

    def on_status(self, status):
        self.tweets.append(status)
        if len(self.tweets) == self.limit:
            self.disconnect()


stream_tweet = Listener(config.TWITTER_API_KEY, config.API_SECRET, config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)


def post_tweet():
    # stream by keywords
    keywords = ['2022', '#python']
    stream_tweet.filter(track=keywords)
    data = []
    for tweet in stream_tweet.tweets:
        data.append([tweet.user.screen_name, tweet.text])
    df = pd.DataFrame(data, columns=['User', 'Tweet'])
    print(df)


def get_all_symbols():
    symbols = pd.read_csv('symbols.csv')
    symbols = symbols['Symbols'].tolist()
    return symbols


def get_stock_data():
    list_of_symbols = get_all_symbols()
    date_today = datetime.date.today()
    date_yesterday = (date_today - datetime.timedelta(days=1))

    # if yesterday was Sunday, get friday:
    if date_yesterday.isoweekday() == 7:
        date_yesterday = date_today - datetime.timedelta(days=3)

    final_percentage_changes = []
    request_counter = 0

    for x in range(len(list_of_symbols)):
        with RESTClient(config.POLYGON_API_KEY) as client:
            yesterday_response = client.stocks_equities_aggregates(ticker=list_of_symbols[x], multiplier=1,
                                                                   timespan='day',
                                                                   from_=date_yesterday, to=date_yesterday,
                                                                   adjusted=True)
            # adds one request and checks if it is the fifth one in a row without break, if yes, thread waits a minute
            request_counter += 1
            if request_counter % 5 == 0:
                time.sleep(62)
            today_response = client.stocks_equities_aggregates(ticker=list_of_symbols[x], multiplier=1, timespan='hour',
                                                               from_=date_today, to=date_today, adjusted=True)
            request_counter += 1
            if request_counter % 5 == 0:
                time.sleep(62)

            today_close = today_response.results[0]['c']
            yesterday_close = yesterday_response.results[0]['c']

            percentage_change = round((((today_close / yesterday_close) - 1) * 100), 2)

            final_percentage_changes.append(percentage_change)

    data = {'ticker': list_of_symbols, 'percentage_changes': final_percentage_changes}
    bar_colors = []
    for col in range(len(final_percentage_changes)):
        if final_percentage_changes[col] >= 0:
            bar_colors.append('green')
        else:
            bar_colors.append('red')

    df = pd.DataFrame(data)
    df.plot(kind='bar', x='ticker', y='percentage_changes', color=bar_colors)
    plt.legend(['Change of price in %'])
    plt.title("Today's Performance")
    result = '\U0001F4C8' + ' Today\'s performance of the biggest stocks on the market: ' + '\U0001F447' + '\n'
    for x in range(len(list_of_symbols)):
        result += (list_of_symbols[x] + " : " + str(final_percentage_changes[x]) + '%' + '\n')
    print(result)
    return result


if __name__ == "__main__":
    tweet_text = get_stock_data()
    api.update_status(tweet_text)
