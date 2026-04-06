import requests
import ast
import time
from datetime import datetime
import pytz
import threading
import math

import logging
from logsconfig import console_logger
logger = logging.getLogger(__name__)



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

        self.durationtime = self._duration_in_seconds()
        self.starttime = int(self._interval_timestamp())
        self.stoptime = self.starttime + self.durationtime

        self.question, self.conditionID, self.upID, self.downID = self.market_from_slug(self.slug)

    def market_from_slug(self,slug):
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
            raise Exception(f"Error fetching market data for slug {slug}")

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

# if __name__ == "__main__":
#     slug = "btc-updown-15m-1771519500"
#     #print(market_from_slug(slug))
#     TestIdentifier1 = MarketIdentifier('btc','15min','now')
#     #print(TestIdentifier1._crypto_slug_part())
#     #print(TestIdentifier1._duration_slug_part())
#     #print(TestIdentifier1._timestamp_slug_part())
#     print(TestIdentifier1.slug)
#     TestIdentifier2 = MarketIdentifier('btc','1hour','now')
#     #print(TestIdentifier2._crypto_slug_part())
#     #print(TestIdentifier2._duration_slug_part())
#     #print(TestIdentifier2._timestamp_slug_part())
#     print(TestIdentifier2.slug)


class IDManager:
    def __init__(self,websocket):
        self.websocket = websocket
        self.focusdict = {} # duration: {coins:list, worker:thread}
        self.threads = {}
        self.current_assets = []
        self.queued_assets = []


    def add_focus(self,coin,duration):
        # tells manager which assets to focus on
        assert (coin in KNOWN_COIN_MARKETS), f'Coin name {coin} not recognized'
        assert (duration in KNOWN_COIN_MARKETS[coin]), f'Duration {duration} not recognized for coin {coin}'

        if duration not in self.focusdict:
            self.focusdict[duration] = {'coins':[coin]}
            new_thread = threading.Thread(target=self._worker, args=[duration], daemon=True)
            new_thread.start()
            self.focusdict[duration]['worker'] = new_thread

        elif coin not in self.focusdict[duration]['coins']:
            self.focusdict[duration]['coins'].append(coin)

        else:
            return


    def remove_focus(self,coin,duration):
        # tells manager to stop focusing on an asset
        # needs to be updated
        if (coin,duration) not in self.focuslist:
            self.focuslist.remove((coin,duration))


    def _worker(self,duration):
        while True:
            skipfirst = False
            # gather all coin IDs for duration
            current_ids = []
            next_ids = []
            for coin in self.focusdict[duration]['coins']:
                current_ids.append(MarketIdentifier(coin,duration,'now'))
                next_ids.append(MarketIdentifier(coin,duration,'next'))

            # work out timing
            if len(current_ids) > 0:
                market_start = current_ids[0].starttime
                market_end = current_ids[0].stoptime
                duration_s = current_ids[0].durationtime
                halfway_target = market_start + duration_s/2
                now = time.time()
            else:
                return # find some non-retarded way to break the loop

            if now < market_end-60:
                # if not before next market sub time
                print(f'{duration} Thread: waiting until {time.ctime(time.time()+(market_end-60-now))}')
                time.sleep(market_end-60-now) # wait until time is 4:00 or -1:00
            else:
                # if past halfway and subtime, wait until next loop and retry
                print(f'{duration} Thread: Waiting until next loop')
                time.sleep(duration_s/2)
                continue

            # sub to 'next' markets     -1:00
            print(f'{duration} Thread: subscribing to market start at {time.ctime(next_ids[0].starttime)} at {time.ctime()}')
            time.sleep(60)
            # markets officially start/end - do nothing       0:00
            time.sleep(60)
            # unsub from 'now' markets if not startup         1:00
            print(f'{duration} Thread: unsubscribing to market stop at {time.ctime(current_ids[0].stoptime)} at {time.ctime()}')
            # loop ends at around 1:00


               

if __name__ == '__main__':

    listener = console_logger()

    logger.info('Logging started locally')

    testmanager = IDManager('test')
    # testmanager.add_focus('btc','15min')
    # testmanager.add_focus('btc','15min')
    # testmanager.add_focus('btc','5min')
    # testmanager.add_focus('eth','5min')
    testmanager.add_focus('sol','1hour')
    testmanager.add_focus('xrp','4hour')
    print(testmanager.focusdict)

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass