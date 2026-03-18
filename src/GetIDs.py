import requests
import ast
import asyncio
import time

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



if __name__ == "__main__":
    slug = "btc-updown-15m-1771519500"
    print(market_from_slug(slug))


KNOWN_COIN_MARKETS = {
    'btc':['5min','15min','1hour','4hour'],
    'eth':['5min','15min','1hour','4hour'],
    'xrp':['5min','15min','1hour','4hour'],
    'sol':['5min','15min','1hour','4hour']
}



class MarketIdentifier:
    def __init__(self,coin,duration,time):
        assert (coin in KNOWN_COIN_MARKETS), f'Coin name {coin} not recognized'
        assert (duration in KNOWN_COIN_MARKETS[coin]), f'Duration {duration} not recognized for coin {coin}'

        self.coin = coin
        self.duration = duration
        #self.time = 

    def _duration_slug_part(self,duration):
        duration_slug_dict = {
            '5min':'5m',
            '15min':'15m',
            '1hour':'',
            '4hour':'4h'
        }
        return duration_slug_dict[duration]

    def _crypto_slug_part(self,coin,duration):
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


    def _timestamp_slug_part(self,time,duration):
        pass

    def make_slug(self,coin,duration,time):
        pass



class IDManager:
    def __init__(self,websocket):
        self.websocket = websocket
        self.current_assets = []
        self.queued_assets = []



