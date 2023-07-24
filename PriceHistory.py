from statistics import *
from Api import *

class PriceHistory:

    def __init__(self, symbol: str):
        
        self.api    = Api()
        self.data   = self.api.PriceHistory( symbol )

        self.sma200 = mean(
            list(self.data.values())[-200:]
        )

        self.sma50  = mean(
            list(self.data.values())[-50:]
        )

        self.trend  = self.sma50 > self.sma200

if __name__ == '__main__':

    ph = PriceHistory('AAPL')

    print('finito')