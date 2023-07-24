from Imports import *

def get_letter(lock, symbols, url, market):
    r = requests.get(url)
    if r.status_code == 200:
        links = re.findall(rf'href=".*?{market}/(.*?).htm"', r.content.decode())
        lock.acquire()
        for link in links:
            if link not in symbols:
                symbols.append(link)
        lock.release()

def get_stocks(letter):

    markets = [ 'NYSE', 'NASDAQ' ]
    symbols = []
    threads = []

    lock = Lock()

    for market in markets:
        url = f'https://www.eoddata.com/stocklist/{market}/{letter}.htm'
        thread = Thread(
            target = get_letter,
            args   = [ lock, symbols, url, market ]
            )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return symbols

if __name__ == '__main__':

    symbols = []
    res = {}

    with Pool(4) as pool:
        res.update(zip(
            string.ascii_uppercase, pool.map(get_stocks, string.ascii_uppercase)
            ))

    for letter in res:
        for l in res[letter]:
            if l not in symbols:
                symbols.append(l)

    with open('data\\stocks.csv', 'w') as f:
        f.write('\n'.join(sorted(symbols)))
        f.close()

    print(f'[INFO] stocks.csv has been updated ({len(symbols)})')