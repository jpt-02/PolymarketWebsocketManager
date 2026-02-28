from OpenSocket import WebSocketOrderBook
from dotenv import load_dotenv, find_dotenv
import os
from bookslots import OrderBook


class Bookmaker:
    def __init__(self):
        self.load_details()
    
    def load_details(self):
        self.url = "wss://ws-subscriptions-clob.polymarket.com"
        env_path = find_dotenv()
        load_dotenv(self.env_path)
        api_key = os.getenv('POLY_API_KEY')
        api_secret = os.getenv('POLY_API_SECRET')
        api_passphrase = os.getenv('POLY_API_PASSPHRASE')
        self.auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}

    def calculate_latency(localtime,timestamp):
        pass


class MarketBookmaker(Bookmaker):
    # TO DO:
    #   -make it so bookdict gets rid of books once a market expires
    def __init__(self):
        super().__init__(self)
        self.bookdict = {} # assetID : OrderBook object from bookslots.py

    def message_input(self,message,localtime):
        # message is already json.loads in the websocket on_message function
        if isinstance(message,list):
            for item in message: self.message_input(item,localtime)
        elif isinstance(message,dict):
            try: # try statement in case there is no event_type
                event_type = message['event_type'] # Get the variable once to save lookups
                if event_type == 'book':
                    if message['asset_id'] not in self.bookdict:
                        self.bookdict[message['asset_id']] = OrderBook(message['asset_id'])
                        self.bookdict[message['asset_id']].update_book(message)
                    else:
                        self.bookdict[message['asset_id']].update_book(message)
                elif event_type == 'price_change':
                    for change in message['price_changes']:
                        self.bookdict[change['asset_id']].update_asset(change)
            except Exception as e:
                print(e)

class UserBookmaker(Bookmaker):
    def __init__(self):
        super().__init__(self)

class RTDSBookmaker(Bookmaker):
    def __init__(self):
        super().__init__(self)



import json

tstring = '[{"name": "John", "age": 30, "city": "New York"}]'
for key in json.loads(tstring):
    print(type(key))
