from Imports import *
from Credentials import *
from Strategies import *
from Account import *
from Ticker import *
from Logger import *
from Symbols import *
from Connection import *

if __name__ == '__main__':

    try:

        d = datetime.now().weekday()
        assert d < 5, 'not a weekday'

        print('[*] syncing time...')
        sync_time()

        print('[*] checking session...')
        while get_session() != 'normal':
            time.sleep(1)

        print('[*] tda initializing...')

        ticker      = Ticker()

        logger      = Logger('orders')
        messages    = Logger('messages')
    
        creds       = Credentials()
        conn        = Connection(creds)
        account     = Account(creds)

        print('[*] tda initialized.')

    except:
        error()
        exit()

    high_thresh         = 0
    low_thresh          = 0

    min_angle           = 0
    max_angle           = 0
    max_spread          = 0

    min_market_angle    = 0

    max_order_age       = 0
    _quantity           = 0
    _offset             = 0

    _basisType          = 'VALUE' # 'PERCENT'
    _basis              = 'BID'

    system('cls')

    while get_session() == 'normal':
        try:

            try:
                recv = conn.read()

            except:
                error()
                continue

            if not recv:
                continue

            recv = json.loads(recv)

            if 'data' in recv:

                for update in recv['data']:

                    service = update['service']
                    content = update['content']
                    tstamp  = update['timestamp']

                    if service == 'ACCT_ACTIVITY':
                        pass

                    elif service == 'QUOTE':
                        try: ticker.update(content, tstamp)
                        except: pass

                actives = []

                for stock in sorted(
                [ ticker.symbol(stock) for stock in ticker.stocks ],
                key=lambda stock: stock.angle,
                reverse=True
                ):

                    needs = [
                        'pct_change',
                        'angle',
                        'high_pct_change',
                        'last_price'
                    ]

                    if not all([ hasattr(stock, need) for need in needs ]):
                        continue

                    # and ticker.market_angle <=      min_market_angle                    \

                    if  high_thresh         >=      stock.pct_change    >=  low_thresh  \
                    and max_angle           >=      stock.angle         >=  min_angle   \
                    and stock.pct_change    ==      stock.high_pct_change               \
                    and stock.pct_spread    <=      max_spread                          \
                    and 1                   <=      stock.last_price    <=  5           \
                    and not account.contains(stock.symbol)                              \
                    and True:

                        logger.log( vars(stock) )
                        buy_price, sell_price = get_price(stock)

                        trail = round( buy_price * 0.01 * _offset, 2 )

                        account.queue[stock.symbol] = account.place_order(

                            multi_order(

                                buy.limit(
                                    stock.symbol,
                                    buy_price,
                                    _quantity
                                    ),

                                sell.trail(
                                    stock.symbol,
                                    _quantity,
                                    trail,
                                    _basisType,
                                    _basis
                                )

                            ), blocking=False
                        )

                        s  = f'[*] BUY\t'
                        s += f'\t{stock.symbol}'
                        s += f'\t$ {round(stock.last_price,     2)}'
                        s += f'\t% {round(stock.pct_change,     2)}'
                        s += f'\t^ {round(stock.pct_spread,     2)}'
                        s += f'\t| {round(stock.angle,          2)}'
                        s += f'\t? {round(ticker.market_angle,  2)}'
                        messages.log(s)

                    actives.append( stock )

                account.sync()

                for o in account.all_orders():
                    if o.symbol not in account.queue:
                        if o.cancelable:
                            if o.instruction == 'BUY':
                                if o.age() >= max_order_age:
                                    account.queue[o.symbol] = o.cancel(blocking=False)
                                    s = f'[*] CANCEL\t{o.symbol}'
                                    messages.log(s)

                system('cls')

                print(f'[*] Profit:\t$ {account.net_profit}')
                print(f'[*] Highest:\t$ {account.highest}\t{account.highest_time_str}')
                print(f'[*] Active:\t{len(actives)}\n')
                print(f'[*] Positions:')

                for p in account.positions:

                    mark = ' '
                    if p.currentDayProfitLoss < 0:
                        mark = '-'

                    profit = round( abs(p.currentDayProfitLoss), 2)

                    s = f'    {p.symbol}  \t{mark}{profit}'
                    print(s)

                print()

                for _,b in list(messages.logs.items())[-25:]:
                    print(b)

        except KeyboardInterrupt:
            break

        except:
            error()

    print()

    if get_session() == 'close':
        print('[*] closing open positions...')
        account.cancel_all_orders()
        account.close_all_positions()

    print('[*] finito.')
