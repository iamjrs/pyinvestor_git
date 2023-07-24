from math import ceil
from Imports import *
from Strategies import *
from Account import *
from Info import *
from Logger import *

if __name__ == '__main__':

    l = Logger('errors')
    delta = int( time.time() ) - int( datetime.utcnow().timestamp() )

    for t,e in l.logs.items():
        t = int(t + delta)
        print( datetime.fromtimestamp(t).time() )
        print(e)

    input('finito')