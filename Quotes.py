from Imports import *
from Api import *


class Quotes:


    def __init__(self):
        self.api        = Api()
        self.last_req   = time.time()


    def update(self):

        self.symbols    = self.api.SearchInstruments()
        self._filter_symbols()
        self.get_quotes()


    def _filter_symbols(self):
    
        for s in list( self.symbols.keys() ).copy():
            v = self.symbols[s]

            if not ( v['assetType'] == 'EQUITY' and v['exchange'] in ['NYSE', 'NASDAQ', 'AMEX'] ):
                self.symbols.pop(s)


    def get_quotes(self):

        start   = time.time()
        banner  = '\r[*] updating symbol quotes... '

        print(banner, end='', flush=True)

        nSize = 500

        for x in range( 0, len( self.symbols ), nSize ):

            pct     = str( round( x / len( self.symbols ) * 100, 2 ) ) + ' %' + ' '
            print(banner + pct, end='', flush=True)

            chunk   = list(self.symbols.keys())[ x : x + nSize ]
            result  = self._get_quotes_chunk( chunk )

            for s in result:
                self.symbols[s].update( result[s] )

        end = time.time()
        print(banner + f'done. ({round(end-start,2)}s)')

        return self.symbols


    def _get_quotes_chunk(self, chunk):

        if not type(chunk) == list:
            chunk = [chunk]
    
        u  = 'https://api.tdameritrade.com/v1/marketdata/quotes?'
        
        query = {
            'apikey':       'api_key_here',
            'symbol':       ','.join(chunk)
        }

        u += urlencode(query)

        while True:
            try:

                self.wait()
                self.last_req = time.time()
                r = requests.get( u )

                if r.status_code in [200, 201]:
                    break

                else:
                    print( r.status_code )
                    self.wait()

            except:
                error()

        d = json.loads( r.content )

        missing = []
        for symbol in chunk:
            if symbol not in d:
                missing.append( symbol )

        if missing:
            if len( chunk ) > len( missing ):
                d.update(
                    self._get_quotes_chunk( missing )
                )

        return d


    def get(self, symbol: str):

        r = {}
    
        if symbol in self.symbols:
            r = self.symbols[symbol]

        return r


    def wait(self, wait=1/2):
        delta   = time.time() - self.last_req
        if delta <= wait:
            time.sleep( wait - delta )


if __name__ == '__main__':

    q = Quotes()
    q.update()

    for symbol,data in q.symbols.items():
        print(symbol,data)

    print('finito')