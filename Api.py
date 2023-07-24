from Credentials import *
import matplotlib.pyplot as plt
from statistics import *

false   = False
true    = True

api_key = 'api_key_here'

class Api:

    def __init__(self):
        self.creds  = Credentials()
 

    def SearchInstruments(self, symbol=None, projection='fundamental'):
    
        '''
        \r@symbol:
        \r  Value to pass to the search. See projection description for more information.

        \r@projection:
        \r  symbol-search: Retrieve instrument data of a specific symbol or cusip

        \r  symbol-regex: Retrieve instrument data for all symbols matching regex.
        \r  Example: symbol=XYZ.* will return all symbols beginning with XYZ

        \r  desc-search: Retrieve instrument data for instruments whose description contains the word supplied.
        \r  Example: symbol=FakeCompany will return all instruments with FakeCompany in the description.

        \r  desc-regex: Search description with full regex support.
        \r  Example: symbol=XYZ.[A-C] returns all instruments whose descriptions contain a word beginning with XYZ followed by a character A through C.

        \r  fundamental: Returns fundamental data for a single instrument specified by exact symbol.
        '''

        u  = 'https://api.tdameritrade.com/v1/instruments?'

        if not symbol:
            symbol      = '[A-Z\.\-]*'
            projection  = 'symbol-regex'

        query = {
            'apikey':       api_key,
            'symbol':       symbol,
            'projection':   projection
        }

        u += urlencode(query)
        r = requests.get( u )

        return eval( r.text )


    def GetQuotes(self, symbol: str or list):

        u  = 'https://api.tdameritrade.com/v1/marketdata/quotes?'

        if not symbol:
            symbol      = '[A-Z\.\-]*'
            projection  = 'symbol-regex'

        query = {
            'apikey':       api_key,
            'symbol':       symbol,
            'projection':   projection
        }

        u += urlencode(query)
        r = requests.get( u )

        return eval( r.text )


    def ShowPriceHistory(self, symbol):
        r = self.PriceHistory(symbol)
        plt.plot( list(r.keys()), list(r.values()) )
        plt.title('Price History')
        plt.xlabel('Datetimes')
        plt.ylabel('Prices')
        plt.show()


    def PriceHistory(self, symbol):
        
        u = f'https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory?'

        query = {
            'apikey':           api_key,
            'periodType':       'year',
            'period':           1,
            'frequencyType':    'daily',
            'frequency':        1
        }

        u += urlencode(query)
        r = requests.get( u )
        d = eval( r.text )['candles']

        prices = {}

        for day in d:
            prices.update(
                { day['datetime']: day['close'] }
            )

        return prices


if __name__ == '__main__':

    api = Api()
    
    symbol = 'TSLA'

    prices = api.PriceHistory( symbol )

    sma200 = mean(
        list(prices.values())[-200:]
        )
    
    sma50 = mean(
        list(prices.values())[-50:]
        )

    print('sma 200-day:', sma200)
    print('sma 50-day:', sma50)
    print('bulling:', sma50>sma200)

    # api.ShowPriceHistory( symbol )

    print('finito')

