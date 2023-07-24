from Imports import *
from Logger import *

def sync_time():
    call(['net', 'stop', 'w32time'], stderr=DEVNULL, stdout=DEVNULL)
    call(['net', 'start', 'w32time'], stderr=DEVNULL, stdout=DEVNULL)
    call(['w32tm', '/resync'], stderr=DEVNULL, stdout=DEVNULL)

def get_session():

    amStart     = 3*60
    amEnd       = 8*60 + 30

    normalStart = amEnd
    normalEnd   = 15*60-1
    
    closeStart  = normalEnd
    closeEnd    = normalEnd+1

    pmStart     = closeEnd
    pmEnd       = 19*60

    clock       = datetime.now()
    minuteOfDay = clock.hour * 60 + clock.minute
    session     = 'none'

    if amStart <= minuteOfDay <= amEnd:
        session = 'am'

    elif normalStart <= minuteOfDay < normalEnd:
        session = 'normal'

    elif closeStart <= minuteOfDay < closeEnd:
        session = 'close'

    elif pmStart <= minuteOfDay < pmEnd:
        session = 'pm'

    return session

@dataclass
class Container:
    def dict(self):
        return vars(self)
    def items(self):
        yield from self.dict().items()
    def __repr__(self):
        return str(vars(self))

def unpack(obj, d: dict):
    for k, v in d.items():
        if type(v) == list:
            if len(v) > 1:
                setattr(obj, k, [])
                for i in v:
                    if type(i) == dict:
                        c = Container()
                        unpack(c, i)
                        getattr(obj, k).append(c)
            else:
                i = v[0]
                if type(i) == dict:
                    c = Container()
                    unpack(c, i)
                    setattr(obj, k, c)
        elif type(v) == dict:
            setattr(obj, k, Container())
            unpack(getattr(obj, k), v)
        else:
            setattr(obj, k, v)

def error():
    rows = []
    for frame in trace():
        row = [
            frame.function, 
            frame.lineno, 
            frame.code_context[-1].strip()
        ]
        rows.append(row)
    m = np.mat(rows)
    cols = np.asarray(m.T)
    widths = [ max([ len(cell) for cell in c ]) for c in cols ]
    logger = Logger('errors')
    log    = []
    for _,row in enumerate(np.asarray(m)):
        data = [ (cell,widths[n]+5) for (n,cell) in enumerate(row) ]
        blocks = []
        for d in data:
            for v in d[:3]:
                blocks.append(v)
        if _ == 0: blocks[0] = '[!] ' + blocks[0]
        else: blocks[0] = '    ' + blocks[0]
        s = '{:{}} line {:{}}{:{}}'.format(*blocks)
        log.append(s)
    s = f'    [!] {sys.exc_info()[1]}'
    log.append(s)
    log.append('\n')
    log = '\n'.join(log)
    logger.log(log)
    print(log)
    try: Beep(250, 250)
    except: pass
    time.sleep(1)

def reject_outliers(data, m=2):
    filtered_data = np.array(data)[ abs(data - np.mean(data)) < m * np.std(data) ]
    return filtered_data

def analyze(ticker):
    results = {}
    for thresh in range(5, 25):
        thresh_matches = []
        for stock in [ ticker[s] for s in ticker ]:
            if stock.high_pct_change >= thresh \
            and stock.pct_spread <= 5:
                thresh_matches.append(stock.high_pct_change)
        thresh_matches = list( reject_outliers( np.array(thresh_matches), 1 ) )
        avg  = sum(thresh_matches) / len(thresh_matches)
        gain = (avg - thresh - 3)
        results[gain] = (thresh, len(thresh_matches))
    for r in sorted(results, reverse=True):
        print(r, *results[r])

if __name__ == '__main__':
    
    try:
        raise Exception
        
    except:
        error()

    print('finito')