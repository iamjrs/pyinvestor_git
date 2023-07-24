from PriceHistory import *
from Fundamentals import *
from Quotes import *
from Api import *

class Views:

    def __init__(self):

        self.fundamentals   = Fundamentals()
        self.quotes         = Quotes()

    def update(self):

        self.fundamentals.update()
        self.quotes.update()


if __name__ == '__main__':

    views = Views()
    views.update()

    print('finito')