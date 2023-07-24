from os import close
from Imports import *
from Credentials import *
from Account import *
from functions import *

class Info:

    def __init__(self, creds, delta=0):
        self.positions  = list()
        self.orders     = list()
        self.creds      = creds
        self.delta      = delta

    def update(self):
        self.load_stocks()
        self.update_orders()
        self.update_positions()

    def update_orders(self):
        today = datetime.today()
        past  = today + timedelta(self.delta)
        today = today.strftime('%Y-%m-%d')
        past  = past.strftime('%Y-%m-%d')
        u  = f'https://api.tdameritrade.com/v1/accounts/'
        u += f'{self.creds.accountId}/orders?'
        u += f'fromEnteredTime={quote(past)}&'
        u += f'toEnteredTime={quote(today)}'
        r = requests.get( u, headers={'Authorization': f'Bearer {self.creds.access_token}'} )
        j = json.loads(r.content)
        _orders = j
        orders = list()
        for o in _orders:
            o = Order(o, '')
            orders.append(o)
        orders.sort(key=lambda x: x.enteredTime, reverse=True)
        self.orders = orders
        return self.orders

    def update_positions(self):
        openers     = []
        closers     = []
        positions   = []
        for o in self.all_orders():
            if o.status == 'FILLED':
                effect = o.orderLegCollection.positionEffect
                if effect == 'OPENING':
                    openers.append(o)
                elif effect == 'CLOSING':
                    closers.append(o)
        openers.sort(key=lambda o: o.orderActivityCollection.executionLegs.time)
        closers.sort(key=lambda c: c.orderActivityCollection.executionLegs.time)
        for o in openers:
            p = Container()
            p.symbol = o.symbol
            p.enterTime = o.enteredTime
            for c in closers:
                if o.symbol == c.symbol:
                    if o.closeTime < c.closeTime:
                        p.openTime  = o.closeTime
                        p.closeTime = c.closeTime
                        p.profit    = c.orderActivityCollection.executionLegs.price - o.orderActivityCollection.executionLegs.price
                        p.profit    = round(p.profit, 3)
                        break
            ref = 0
            for t,s in list([ (t,s) for (t,s) in self.stocks.items() if p.symbol == s.symbol ]):                
                if abs(p.enterTime.timestamp() - t) < abs(p.enterTime.timestamp() - ref):
                    p.stock = s
                    ref     = t
            positions.append(p)
        self.winners    = [ p for p in positions if p.profit > 0 ]
        self.losers     = [ p for p in positions if p.profit <= 0 ]
        self.positions  = positions

    def get_price_history(self, symbol):
        periodType      = None
        period          = None
        frequencyType   = None
        frequency       = None
        startDate       = None
        endDate         = None
        u  = f'https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory?'
        u += f'apikey={self.creds.client_id}&'
        # u += f'periodType={periodType}'
        r = requests.get( u, headers={'Authorization': f'Bearer {self.creds.access_token}'} )
        j = json.loads(r.content)
        pprint(j)

    def all_orders(self):
        orderList = []
        for o in self.orders.copy():
            orderList.append(o)
            if o.orderStrategyType == 'TRIGGER':
                orderList.append(o.childOrderStrategies)
        return orderList

    def load_symbols(self):
        with open('symbols_list.txt', 'r') as f:
            self.symbols_list = sorted(
                set(
                    f.read().strip().splitlines()
                ) )
            f.close()

    def load_stocks(self):
        _stocks = {}
        for delta in range(self.delta, 1):
            date    = ( datetime.today() + timedelta(delta) )
            if 1 <= date.isoweekday() <= 5:
                stocks  = dict( Logger( 'orders', date.strftime('%Y%m%d') ).logs )
                for t,s in stocks.copy().items():
                    stock = Container()
                    unpack(stock, s)
                    stocks[t] = stock
                _stocks.update(stocks)
        self.stocks = _stocks

    def report(self):
        p1      = self.positions[0]
        keys    = [ k for (k,v) in p1.stock.dict().items() if type(v) == float ][:-1]
        for k in keys:
            wVals = [ getattr(x.stock, k) for x in self.winners ]
            wVals = reject_outliers(wVals)
            w = sum(wVals) / len(wVals)
            lVals = [ getattr(x.stock, k) for x in self.losers ]
            lVals = reject_outliers(lVals)
            l = sum(lVals) / len(lVals)
            s = '{:<15s}\t{:20.3f}\t{:20.3f}'.format(
                k, round(w, 3), round(l, 3) )
            print(s)

if __name__ == '__main__':

    creds   = Credentials()
    info    = Info(creds, -14)

    info.update()
    info.report()
