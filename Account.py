from numpy.core.shape_base import block
from Imports import *
from Credentials import *
from Strategies import *
from Logger import *
from functions import *
from pprint import pprint

class Position:

    def __init__(self, json: dict):
        unpack(self, json)
        self.symbol     = str(self.instrument.symbol)
        self.quantity   = int(self.longQuantity)
        self.price      = float(self.averagePrice)
    
    def dict(self):
        return vars(self)
    
    def __repr__(self):
        return str(self.dict())

class Order:
    
    def __init__(self, json: dict, access_token):

        unpack(self, json)
        self.symbol         = str(self.orderLegCollection.instrument.symbol)
        self.instruction    = str(self.orderLegCollection.instruction)
        self.quantity       = int(self.quantity)
        self.access_token   = access_token
        self.enteredTime    = datetime.fromisoformat( self.enteredTime.split('+')[0] )
        
        if hasattr(self, 'closeTime'):
            self.closeTime  = datetime.fromisoformat( self.closeTime.split('+')[0] )

        if self.orderStrategyType == 'TRIGGER':
            co = self.childOrderStrategies
            if type(co) == list:
                _co = co[-1]
                for o in co.copy():
                    if o.cancelable:
                        _co = o
                co = Order(_co, access_token)
            elif type(co) == Container:
                co  = Order(co.dict(), access_token)
            self.childOrderStrategies = co

    def age(self):
        delta = datetime.utcnow() - self.enteredTime
        return delta.seconds
    
    def cancel(self, blocking=True):
        t = Thread(target=self._cancel)
        t.start()
        if blocking:
            t.join()
        return t

    def replace(self, order, blocking=True):
        t = Thread(target=self._replace, args=(order,))
        t.start()
        if blocking:
            t.join()
        return t

    def _replace(self, order):
        if self.cancelable:
            u = f'https://api.tdameritrade.com/v1/accounts/{self.accountId}/orders/{self.orderId}'
            r = requests.put( u, headers={'Authorization': f'Bearer {self.access_token}'}, json=order )
            return r

    def _cancel(self):
        if self.cancelable:
            u = f'https://api.tdameritrade.com/v1/accounts/{self.accountId}/orders/{self.orderId}'
            r = requests.delete( u, headers={'Authorization': f'Bearer {self.access_token}'} )
            return r

    def dict(self):
        return vars(self)

    def __repr__(self):
        return str(self.dict())


class Account:

    def __init__(self, creds=Credentials()):
        self.profits    = Logger('profits')
        self.last_sync  = float()
        self.positions  = list()
        self.orders     = list()
        self.queue      = dict()
        self.creds      = creds
        self.highest    = -1
        self.sync()

    def sync(self, blocking=True, waiting=True):
        wait = 2
        if self.creds.remaining() <= 10:
            self.creds      = Credentials()
            self.last_sync  = time.time()
        if waiting:
            d = time.time() - self.last_sync
            if d < wait:
                time.sleep(wait - d)
        if time.time() - self.last_sync >= 1:
            t = Thread(target=self._sync)
            t.start()
            if blocking:
                t.join()
                self.queue.clear()
            self.last_sync = time.time()
            return t

    def get_order(self, symbol):
        for o in [ o for o in self.all_orders() if o.cancelable ]:
            if o.symbol == symbol:
                if o.cancelable:
                    return o

    def all_orders(self):
        orderList = []
        for o in self.orders.copy():
            orderList.append(o)
            if o.orderStrategyType == 'TRIGGER':
                orderList.append(o.childOrderStrategies)
        return orderList

    def get_position(self, symbol):
        for p in self.positions.copy():
            if p.symbol == symbol:
                return p

    def contains(self, symbol):
        if self.get_order(symbol):
            return True
        elif self.get_position(symbol):
            return True
        elif symbol in self.queue:
            return True
        else:
            return False

    def place_order(self, order, blocking=True):
        t = Thread(target=self._place_order, args=(order,))
        t.start()
        if blocking:
            t.join()
        return t

    def cancel_all_orders(self):
        self._sync()
        for o in self.all_orders():
            self.queue[o.symbol] = o.cancel(blocking=False)
        self._sync()

    def close_all_positions(self):
        self._sync()
        for p in self.positions:
            o = self.get_order(p.symbol)
            if not o:
                newOrder = sell.market(p.symbol, p.quantity)
                self.queue[p.symbol] = self.place_order(newOrder, blocking=False)
        self._sync()

    def cancel_replace(self, order, newOrder, blocking=True):
        t = Thread(target=self._cancel_replace, args=(order, newOrder,))
        t.start()
        if blocking:
            t.join()
        return t

    def _cancel_replace(self, order, newOrder):
        if order.cancelable:
            u = f'https://api.tdameritrade.com/v1/accounts/{order.accountId}/orders/{order.orderId}'
            r = requests.delete( u, headers={'Authorization': f'Bearer {order.access_token}'} )
            if r.status_code != 400:
                return self._place_order(newOrder)

    def _place_order(self, order):
        u  = f'https://api.tdameritrade.com/v1/accounts/'
        u += f'{self.creds.accountId}/orders'
        r = requests.post( u,
            headers={'Authorization': f'Bearer {self.creds.access_token}'},
            json=order )
        return r

    def _sync(self):
        for _,t in self.queue.items():
            t.join()
        ts = []
        for task in [ self._update_positions, self._update_orders ]:
            t = Thread(target=task, args=())
            t.start()
            ts.append(t)
        for t in ts:
            t.join()

    def _update_positions(self):

        try:
            u  = f'https://api.tdameritrade.com/v1/accounts/'
            u += f'{self.creds.accountId}'
            u += f'?fields=positions'

            r = requests.get( u, headers={'Authorization': f'Bearer {self.creds.access_token}'} )

            assert r.status_code == 200, '_update_positions(): ' + r.text

            j = json.loads(r.content)
            _positions = j['securitiesAccount']['positions']

            setattr(self, 'info', Container())
            unpack(self.info, j)
            initial = self.info.securitiesAccount.initialBalances.liquidationValue
            current = self.info.securitiesAccount.currentBalances.liquidationValue
            self.net_profit = round(current - initial, 3)

            if not self.profits.logs:
                self.profits.log(self.net_profit)

            elif list(self.profits.logs.values())[-1] != self.net_profit:
                self.profits.log(self.net_profit)

            for t,p in self.profits.logs.items():
                if p > self.highest:
                    self.highest_time = t
                    self.highest = p

            delta = int( time.time() ) - int( datetime.utcnow().timestamp() )
            self.highest_time_str   = datetime.fromtimestamp(
                int(self.highest_time) + int(delta)
                ).time()

            positions = list()
            for position in _positions:
                position = Position(position)
                if position.instrument.assetType == 'EQUITY':
                    positions.append(position)
            self.positions = positions

        except:
            error()

    def _update_orders(self):

        try:
            u  = f'https://api.tdameritrade.com/v1/accounts/'
            u += f'{self.creds.accountId}/orders'

            r = requests.get( u, headers={'Authorization': f'Bearer {self.creds.access_token}'} )

            assert r.status_code == 200, '_update_orders(): ' + r.text

            j = json.loads(r.content)
            _orders = j

            orders = list()
            for o in _orders:
                try:
                    o = Order(o, self.creds.access_token)
                    orders.append(o)
                except:
                    pass

            orders.sort(key=lambda x: x.enteredTime, reverse=True)
            self.orders = orders

        except:
            error()

    def __iter__(self):
        yield from vars(self)

    def __getitem__(self, item):
        return vars(self)[item]


if __name__ == '__main__':

    account = Account()