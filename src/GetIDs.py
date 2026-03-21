import requests
import ast
import time
from datetime import datetime
import pytz

def market_from_slug(slug):
    # Gamma API endpoint for fetching market by its URL slug
    url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        #ast.literal_eval is necessary because otherwise its a string of IDs, not a list of strings
        upID, downID = ast.literal_eval(data['clobTokenIds'])
        conditionID = data['conditionId']
        question = data['question']
        
        return question, conditionID, upID, downID
    else:
        print("Error fetching market data")
        return None




KNOWN_COIN_MARKETS = {
    'btc':['5min','15min','1hour','4hour'],
    'eth':['5min','15min','1hour','4hour'],
    'xrp':['5min','15min','1hour','4hour'],
    'sol':['5min','15min','1hour','4hour']
}



class MarketIdentifier:
    def __init__(self,coin,duration,timeframe='now'):
        assert (coin in KNOWN_COIN_MARKETS), f'Coin name {coin} not recognized'
        assert (duration in KNOWN_COIN_MARKETS[coin]), f'Duration {duration} not recognized for coin {coin}'
        assert (timeframe=='now' or timeframe=='next'), f"Timeframe entered is '{timeframe}', must be either 'now' or 'next'"

        self.coin = coin
        self.duration = duration
        self.timeframe = timeframe

        self.slug = self._make_slug()

    def _duration_slug_part(self):
        duration = self.duration
        duration_slug_dict = {
            '5min':'5m-',
            '15min':'15m-',
            '1hour':'',
            '4hour':'4h-'
        }
        return duration_slug_dict[duration]

    def _crypto_slug_part(self):
        coin = self.coin
        duration = self.duration
        if duration == '1hour':
            crypto_slug_dict = {
                'btc':'bitcoin-up-or-down-',
                'eth':'ethereum-up-or-down-',
                'xrp':'xrp-up-or-down-',
                'sol':'solana-up-or-down-'
            }
            return crypto_slug_dict[coin]
        else:
            crypto_slug_dict = {
                'btc':'btc-updown-',
                'eth':'eth-updown-',
                'xrp':'xrp-updown-',
                'sol':'sol-updown-'
            }
            return crypto_slug_dict[coin]

    def _duration_in_seconds(self):
        duration = self.duration
        duration_time_dict = {
            '5min':300,
            '15min':900,
            '1hour':3600,
            '4hour':14400
        }
        return duration_time_dict[duration]

    def _interval_timestamp(self):
        timeframe = self.timeframe
        if timeframe == 'now': timeref = time.time()
        if timeframe == 'next': timeref = time.time() + self._duration_in_seconds()

        duration_s = self._duration_in_seconds()
        roundtime = round(timeref - (timeref%duration_s))
        return str(roundtime)

    def _timestamp_slug_part(self):
        duration = self.duration

        if duration == '1hour':
            interval_stamp = int(self._interval_timestamp())
            est_tz = pytz.timezone("America/New_York")
            dt_object = datetime.fromtimestamp(interval_stamp, tz=est_tz)
            monthname = dt_object.strftime('%B').lower()
            day = dt_object.day
            year = dt_object.year
            time_ = dt_object.strftime('%#I%p').lower()
            return f'{monthname}-{day}-{year}-{time_}-et'
        else:
            return self._interval_timestamp()

    def _make_slug(self):
        coinpart = self._crypto_slug_part()
        durationpart = self._duration_slug_part()
        timepart = self._timestamp_slug_part()
        return coinpart+durationpart+timepart

if __name__ == "__main__":
    slug = "btc-updown-15m-1771519500"
    #print(market_from_slug(slug))
    TestIdentifier1 = MarketIdentifier('btc','15min','now')
    #print(TestIdentifier1._crypto_slug_part())
    #print(TestIdentifier1._duration_slug_part())
    #print(TestIdentifier1._timestamp_slug_part())
    print(TestIdentifier1.slug)
    TestIdentifier2 = MarketIdentifier('btc','1hour','now')
    #print(TestIdentifier2._crypto_slug_part())
    #print(TestIdentifier2._duration_slug_part())
    #print(TestIdentifier2._timestamp_slug_part())
    print(TestIdentifier2.slug)



class IDManager:
    def __init__(self,websocket):
        self.websocket = websocket
        self.current_assets = []
        self.queued_assets = []



