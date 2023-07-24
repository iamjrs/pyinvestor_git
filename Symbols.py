from Imports import *
import bs4
from bs4 import BeautifulSoup
import re
import pickle
import os
from urllib.parse import *
import Levenshtein
from multiprocessing import Pool
from klepto.archives import *
import string
import csv
from collections import namedtuple


def clean_string(s):

    s = s.lower()

    removes = [
        r'common stock.*',
        r'common shares.*',
        r'common unit.*',
        r'preferred shares.*',
        r'deposit.ry shares.*',
        r'ordinary shares.*',
        r'sponsored adr.*',
        r'class a.*',
        r'warrant.*',
        r'ads each.*',
        r', each.*',
        r', repr.*',
        fr'[{string.punctuation}\\]'
    ]

    subs = [
        ( 'corporation', 'corp' ),
        ( 'company', 'co' ),
        ( 'limited', 'ltd' ),
        ( r'\s+', ' ' )
    ]

    for remove in removes:
        s = re.sub( remove, str(), s )

    for sub1, sub2 in subs:
        s = re.sub( sub1, sub2, s )

    return s


def compare_strings( c ):

    a,b = c
    a   = a[ : len( b ) ]

    if b:
        ratio   = Levenshtein.ratio( a, b )
    else:
        ratio   = 0.0 

    return { ratio: b }


class Symbols:


    def __init__(self):
        self.cik_lookup = dir_archive(  '.\\data\\objects\\Symbols\\cik_lookup',    cached=False )
        self.cik_map    = dir_archive(  '.\\data\\objects\\Symbols\\cik_map',       cached=False )
        self.last_req   = time.time()
        self.symbols    = {}
        self.list       = []
        self.updated    = 0


    def update(self, filter_symbols=True, filter_prices=True, save=True):

        start = time.time()

        self.get_symbols()

        if filter_symbols:
            self._filter_symbols()

        self.get_prices()

        for s in list(self.symbols).copy():
            v = self.symbols[s]
            if ('openPrice' not in v) and ('closePrice' not in v):
                self.symbols.pop(s)

        if filter_prices:
            self._filter_prices()

        self.get_industries()

        self.list       = list( set( self.symbols.keys() ) )
        self.updated    = time.time()

        end = time.time()

        print(f'[*] all updates completed. ({round(end-start,2)}s)', end='\n\n')


    def get_symbols(self):

        start   = time.time()
        banner  = '\r[*] updating symbols list... '

        print(banner, end='', flush=True)
        
        u  = 'https://api.tdameritrade.com/v1/instruments'
        u += '?apikey=api_key_here'
        u += '&symbol=%5BA-Z%5C.%5C-%5D*'
        u += '&projection=symbol-regex'

        while True:
            try:

                self.wait()
                self.last_req = time.time()
                r = requests.get(u)

                if r.status_code in [200, 201]:
                    break

                else:
                    self.wait()

            except:
                error()

        self.symbols.update( dict(json.loads( r.content )) )

        end = time.time()
        print(f'done. ({round(end-start,2)}s)')
        return self.symbols


    def _filter_symbols(self):
    
        for s in list( self.symbols.keys() ).copy():
            v = self.symbols[s]

            if not ( v['assetType'] == 'EQUITY' and v['exchange'] in ['NYSE', 'NASDAQ', 'AMEX'] ):
                self.symbols.pop(s)


    def get_prices(self):

        start   = time.time()
        banner  = '\r[*] updating symbol prices... '

        print(banner, end='', flush=True)

        for x in range( 0, len( self.symbols ), 500 ):

            pct     = str( round( x / len( self.symbols ) * 100, 2 ) ) + ' %' + ' '
            print(banner + pct, end='', flush=True)

            chunk   = list(self.symbols.keys())[ x : x + 500 ]
            result  = self._get_prices_chunk( chunk )

            for s in result:
                result[s]['exchange']       = self.symbols[s]['exchange']
                result[s]['description']    = clean_string( result[s]['description'] )
                self.symbols[s].update( result[s] )

        end = time.time()
        print(banner + f'done. ({round(end-start,2)}s)')
        return self.symbols


    def _get_prices_chunk(self, chunk):

        if not type(chunk) == list:
            chunk = [chunk]
    
        u  = 'https://api.tdameritrade.com/v1/marketdata/quotes'
        u += '?apikey=api_key_here'
        u += '&symbol=' + quote( ','.join( chunk ) )

        while True:
            try:

                self.wait()
                self.last_req = time.time()
                r = requests.get( u )

                if r.status_code in [200, 201]:
                    break

                else:
                    print(r.status_code)
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
                    self._get_prices_chunk( missing )
                )

        return d


    def _filter_prices(self, low=1, high=5):

        for s in list(self.symbols).copy():
            v = self.symbols[s]

            if not low < v['openPrice'] < high:
                self.symbols.pop(s)


    def get_industries(self):

        start   = time.time()
        banner  = '\r[*] updating industries... '
        print( banner, end='', flush=True )

        u = 'https://www.sec.gov/Archives/edgar/cik-lookup-data.txt'
        
        h = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36'
        }

        r = requests.get( u, headers=h )
        name_map = {}

        for line in r.text.splitlines():

            line    = line[:-1]
            k       = line[:-11].strip()
            v       = line[-10:].strip()
            k       = clean_string( k )

            if k not in name_map:
                name_map[k] = []

            if v not in name_map[k]:
                name_map[k].append(v)

        missing = []

        for s in self.symbols:
            if s not in self.cik_lookup:
                missing.append( s )

        print( 'missing: ', len(missing) )

        for n,symbol in enumerate(missing):

            pct = '%.2f' % round( n / len( missing ) * 100, 2 ) + ' %' + ' '
            print( banner + pct, end='', flush=True )

            results = {}

            for name in name_map:
                r = compare_strings( ( self.symbols[symbol]['description'], name ) )
                results.update( r )

            high = max( results.keys() )

            if high > .75:

                k       = results[high]
                ciks    = name_map[k]

                self.cik_lookup[symbol] = ciks

                for cik in ciks:
                    if cik not in self.cik_map:
                        self.cik_map[cik] = self.get_cik_data(cik)

        end = time.time()
        print(f'{banner}done. ({round(end-start,2)}s)')
        return self.symbols


    def get_cik_data(self, cik):

        h = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36'
        }

        u   = f'https://data.sec.gov/submissions/CIK{cik}.json'

        while True:
            try:

                self.wait( 1/9 )
                self.last_req = time.time()
                r = requests.get( u, headers=h )

                if r.status_code in [ 200, 201 ]:
                    break

                else:
                    print( r.status_code )
                    self.wait()

            except:
                pass

        d   = dict( json.loads( r.content ) )
        
        return d


    def wait(self, wait=1/1.95):
        delta   = time.time() - self.last_req
        if delta <= wait:
            time.sleep( wait - delta )


SIC = namedtuple( 'SIC', [ 'division', 'major', 'industry', 'sic' ], defaults=[None]*4 )


class SicParser:

    def __init__(self):
        
        self.divs   = {}
        self.majs   = {}
        self.inds   = {}
        self.sics   = {}

        self.load()

    def load(self):

        div_map = [
            ( range(10),        'A' ),
            ( range(10, 15),    'B' ),
            ( range(15, 18),    'C' ),
            ( range(20, 40),    'D' ),
            ( range(40, 50),    'E' ),
            ( range(50, 52),    'F' ),
            ( range(52, 60),    'G' ),
            ( range(60, 68),    'H' ),
            ( range(70, 90),    'I' ),
            ( range(91, 100),   'J' ),
        ]

        self.div_map = {}
        
        for k,v in div_map:
            for n in k:
                self.div_map[ str(n).zfill(2) ] = v

        csvs = [ 'osha', 'sec' ]
        path = '.\\data\\files\\'
        suff = '_sic_data.csv'

        for c in csvs:

            fp = path + c + suff

            with open(fp, 'r') as f:
                c = list( csv.reader( f.readlines(), delimiter=',', quotechar='"' ) )
                f.close()

            for line in c[1:]:

                if len(line) > 3:

                    sic_cd,sic_desc, ind_cd,ind_desc, maj_cd,maj_desc, div_cd,div_desc = line
                    
                    self.divs[div_cd]   = div_desc
                    self.majs[maj_cd]   = maj_desc
                    self.inds[ind_cd]   = ind_desc
                    self.sics[sic_cd]   = sic_desc

                else:
                    
                    sic_cd, ad_office, ind_desc = line
                    sic_cd      = str(sic_cd).zfill(4)
                    ind_desc    = str(ind_desc).title()

                    if sic_cd not in self.sics:
                        self.sics[sic_cd] = ind_desc

    def get(self, sic_cd):

        div_cd, div_desc, maj_desc = [None] * 3

        sic_cd      = str(sic_cd).zfill(4)
        sic_desc    = self.sics[ sic_cd ]
        ind_desc    = sic_desc

        try:
            div_cd      = self.div_map[ sic_cd[:2] ]
            div_desc    = self.divs[ div_cd ]
            maj_desc    = self.majs[ sic_cd[:2] ]
            ind_desc    = self.inds[ sic_cd[:3] ]

        except:
            pass

        ind_desc    = ind_desc or sic_desc
        obj         = SIC( div_desc, maj_desc, ind_desc, sic_desc )

        return obj

if __name__ == '__main__':

    s  = Symbols()
    # s.update(filter_prices=False)
    s.update()

    exit()

    missing = []

    cik_lookup  = s.cik_lookup
    cik_map     = s.cik_map

    for symbol,ciks in cik_lookup.items():
        if not any([ cik for cik in ciks if cik_map[cik]['sic'] ]):
            missing.append(symbol)

    print( len(cik_lookup) )
    print( len(missing) )

    print(
        len(missing) / len(cik_lookup) * 100
    )

    print(
        len(cik_lookup) - len(missing)
    )

    exit()

    for k,v in s.cik_lookup.items():
        
        data    = s.cik_map[v]
        filings = data['filings']['recent']
        tickers = data['tickers']

        print( ', '.join(tickers), data['name'] )

        headers = [
            ('filingDate', 14),
            ('accessionNumber', 24),
            ('primaryDocument', 40),
            ('primaryDocDescription', 20)            
        ]

        entries = 0

        for k2,v2 in filings.items():
            if type(v2) == list:
                entries = len(v2)

        for x in range(entries):
            
            docType = filings['primaryDocDescription'][x]
            
            if docType in ['10-Q', '10-K']:

                cik     = v
                folder  = re.sub( '-', '', filings['accessionNumber'][x] )
                doc     = filings['primaryDocument'][x]
                url     = f'https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{doc}'
                
                input(url)

        print()

    print('finito')
