from Imports import *
from Ticker import *

def get_price(stock: Stock):
    price = stock.bid_price + stock.net_spread #* 0.5
    delta: int
    place: int
    if price > 1:
        delta = 0.01
        place = 2
    elif price < 1:
        delta = 0.0001
        place = 4
    buy_price = round(price, place)
    sell_price = round(price + delta, place)
    if buy_price == sell_price:
        sell_price = round(price + delta + delta, place)
    return (buy_price, sell_price)

@dataclass
class buy:

    @staticmethod
    def limit(symbol: str, price: float, quantity=1, duration='GOOD_TILL_CANCEL'):
        return {
            'orderStrategyType':    'SINGLE',
            'orderType':            'LIMIT',
            'session':              'NORMAL',
            'duration':             duration,
            'price':                price,
            'orderLegCollection': [{
                'instruction':      'BUY',
                'quantity':         quantity,
                'instrument': {
                    'assetType':    'EQUITY',
                    'symbol':       symbol
                    }
                }
            ]
        }

@dataclass
class sell:

    @staticmethod
    def limit(symbol: str, quantity: int, price: float, duration='GOOD_TILL_CANCEL'):

        assert type(symbol)     == str
        assert type(quantity)   == int
        assert type(price)      == float

        return {
            'orderStrategyType':    'SINGLE',
            'orderType':            'LIMIT',
            'session':              'NORMAL',
            'duration':             duration,
            'price':                price,
            'orderLegCollection': [{
                'instruction':      'SELL',
                'quantity':         quantity,
                'instrument': {
                    'assetType':    'EQUITY',
                    'symbol':       symbol
                    }
                }
            ]
        }

    @staticmethod
    def trail(symbol: str, quantity: int, offset=2, basisType='PERCENT', basis='BID', duration='GOOD_TILL_CANCEL'):

        assert type(symbol)     == str
        assert type(quantity)   == int

        return {
            'orderStrategyType':    'SINGLE',
            'orderType':            'TRAILING_STOP',
            'session':              'NORMAL',
            'duration':             duration,
            'stopType':             basis,
            'stopPriceLinkBasis':   basis,
            'stopPriceLinkType':    basisType,
            'stopPriceOffset':      offset,
            'orderLegCollection': [{
                'instruction':      'SELL',
                'quantity':         quantity,
                'instrument': {
                    'assetType':    'EQUITY',
                    'symbol':       symbol
                    }
                }
            ]
        }

    @staticmethod
    def market(symbol: str, quantity: int, duration='GOOD_TILL_CANCEL'):
        
        assert type(symbol)     == str
        assert type(quantity)   == int

        return {
            'orderStrategyType':    'SINGLE',
            'orderType':            'MARKET',
            'session':              'NORMAL',
            'duration':             duration,
            'orderLegCollection': [{
                'instruction':      'SELL',
                'quantity':         quantity,
                'instrument': {
                    'assetType':    'EQUITY',
                    'symbol':       symbol
                    }
                }
            ]
        }

def multi_order(parentOrder: dict, childOrder: dict):
    parentOrder['orderStrategyType']    = 'TRIGGER'
    parentOrder['childOrderStrategies'] = [childOrder]
    return parentOrder
