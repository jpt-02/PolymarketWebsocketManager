'''
Docstring for src.bookslots
'''

class OrderBook:
    __slots__ = ['assetID','bids','asks']

    def __init__(self,assetID):
        self.assetID = assetID
        self.bids = {}
        self.asks = {}
    
    def update(self, price, size, side):
        # Dictionary access is the fastest way to route this
        target = self.bids if side == 'BUY' else self.asks
        
        # In HFT, size 0 means the price level is gone
        if size == 0:
            target.pop(price, None)
        else:
            target[price] = size
        
    def update_book(self,message):
        # wipes the book for a specific assetID and replaces with book message contents
        # float the size because that changes, price stays as string
        for bid in message['bids']:
            self.bids = {bid['price']: float(bid['size'])}
        for ask in message['asks']:
            self.asks = {ask['price']: float(ask['size'])}

    def update_asset(self,price_changes):
        for change in price_changes:
            target = self.bids if change['side'] == 'BUY' else self.asks
            price = price_changes['price']
            size = float(price_changes['size'])

            if size == 0:
                target.pop(price, None)
            else:
                target[price] = size
