from klepto.archives import file_archive
from datetime import datetime, timedelta
import time

class Logger:

    def __init__(self, directory='test1', date=datetime.today().strftime('%Y%m%d')):
        self.path   = f'logs\\{directory}\\{date}'
        self.logs   = file_archive( self.path, cached=False )

    def log(self, item):
        stamp = datetime.utcnow().timestamp()
        self.logs[stamp] = item

if __name__ == '__main__':

    logger = Logger('messages')

    delta = int( time.time() ) - int( datetime.utcnow().timestamp() )

    for t,l in logger.logs.items():
        t = int(t + delta)
        print( '{}\t{}'.format( datetime.fromtimestamp(t).time(), l ) )
    print()
    
    input('finito')