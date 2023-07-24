from Imports import *


class Ticker:

    indexList  = [ '$COMPX', '$DJI', '$SPX.X' ]

    def __init__(self):

        self.indices    = {}
        self.stocks     = {}

    def symbol(self, s):

        if s in self.indices:
            return self.index(s)

        elif s in self.stocks:
            return self.stock(s)

    def stock(self, s):

        if s in self.stocks:
            return self.stocks[s]

    def index(self, s):

        if s in self.indices:
            return self.indices[s]

    def update(self, update, tstamp):

        for u in update:
            symbol = u['key']

            if not self.symbol(symbol):
                
                if symbol[0] == '$':
                    self.indices[symbol] = Stock(u, tstamp)

                else:
                    self.stocks[symbol] = Stock(u, tstamp)

            else:
                self.symbol(symbol).update(u, tstamp)

        self._market_angle()

    def _market_angle(self):

        if all([ self.symbol(i).angle for i in self.indexList ]):
            self.market_angle = sum([ self.symbol(i).angle for i in self.indexList ]) / len( self.indexList )
        else:
            self.market_angle = 0



class Stock:

    fields = {
        '0':  'symbol',
        '1':  'bid_price',
        '2':  'ask_price',
        '3':  'last_price',
        '8':  'total_volume',
        '12': 'high_price',
        '13': 'low_price',
        '15': 'close_price',
        '28': 'open_price'
    }

    def __init__(self, update, tstamp):

        self.symbol     = update['key']
        self.history    = OrderedDict()
        self.updates    = 0
        self.oldest     = 0
        self.angle      = 0
        self.update( update, tstamp )

    def update(self, update, tstamp):

        for k,v in update.items():
            if k in Stock.fields:
                field = Stock.fields[k]
                setattr(self, field, v)

        if all([ hasattr(self, attr) for attr in ['open_price', 'high_price'] ]): # 'last_price', 
            self.net_change         = self.last_price - self.open_price
            self.pct_change         = self.net_change / self.open_price * 100
            self.high_net_change    = self.high_price - self.open_price
            self.high_pct_change    = self.high_net_change / self.open_price * 100

            if hasattr(self, 'bid_price'):
                self.net_spread         = abs(self.bid_price - self.ask_price)
                self.pct_spread         = self.net_spread / self.open_price * 100

            self.update_angle(tstamp)

    def update_angle(self, tstamp):

        self.history[ tstamp/1000 ] = self.last_price
        self.updates    += 1
        angles          = []

        if len(self.history) >= 3:

            if len( self.history ) > 3:
                self.history.popitem( last=False )

            n = len( self.history ) - 1

            for x in range(n):
                x1 = list(self.history)[x]
                x2 = list(self.history)[x + 1]
                y1 = self.history[x1]
                y2 = self.history[x2]
                a  = (y2-y1)/(x2-x1)
                a  = math.degrees( math.atan(a) )
                angles.append(a)

            self.angle = sum(angles) / len(angles)

        else:
            self.angle = 0

        self.oldest = list(self.history)[0]

    def active(self):
        if len( self.history.keys() ) >= 3:
            if all([ ts for ts in self.history.keys() if ts >= time.time() - 60 ]):
                return True



if __name__ == '__main__':

    pass
    