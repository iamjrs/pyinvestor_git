from Imports import *
from Credentials import *
from Strategies import *
from Account import *
from Ticker import *
from Symbols import *


class Commands:

    def __init__( self, creds ):

        self.creds = creds

        self.login = {
            'account':          self.creds.userid,
            'source':           self.creds.appid,
            'service':          'ADMIN',
            'command':          'LOGIN',
            'parameters': {
                'credential':   urlencode( self.creds.json ),
                'token':        self.creds.token,
                'version':      '1.0',
                'qoslevel':     0
                }
            }

        self.logout = {
            'account':          self.creds.userid,
            'source':           self.creds.appid,
            "service":          "ADMIN",
            "command":          "LOGOUT",
            "parameters":       {}
            }

        self.activity = {
            'account':          self.creds.userid,
            'source':           self.creds.appid,
            "service":          "ACCT_ACTIVITY",
            "command":          "SUBS",
            "parameters": {
                "keys":         self.creds.streamKey,
                "fields":       "0,1,2,3"
                }
            }

        self.qos = {
            'account':          self.creds.userid,
            'source':           self.creds.appid,
            "service":          "ADMIN",
            "command":          "QOS",
            "parameters": {
                "qoslevel": "0"
                }
            }

        s = Symbols()
        s.update()

        l = s.list
        l.extend( Ticker.indexList )

        self.quotes = {
            'account':          self.creds.userid,
            'source':           self.creds.appid,
            "service":          "QUOTE",
            "command":          "SUBS",
            "parameters": {
                "keys":         ','.join( l ),
                "fields":       ','.join( Stock.fields.keys() )
                }
            }

        n = 0
        for v in vars(self):
            if type( getattr(self, v) ) == dict:
                getattr(self, v)['requestid'] = n
                n += 1


class Connection:

    def __init__( self, creds=Credentials() ):

        self.creds      = creds
        self.commands   = Commands( self.creds )
        self.connect()

    def read(self):

        try:
            data = self.ws.recv()
            if data:
                data = data.strip()
            return data

        except:
            error()
            self.connect()

    def connect(self):

        print('[*] websocket connecting...')

        while True:
            try:

                if hasattr(self, 'ws'):
                    self.ws.close()
                    self.ws = None
                    time.sleep(1)

                self.ws         = WebSocket()
                self.ws.url     = 'wss://' + self.creds.userprincipals['streamerInfo']['streamerSocketUrl'] + '/ws'
                self.ws.timeout = None
                self.ws.connect( self.ws.url )

                while not self.ws.connected:
                    time.sleep(1)

                reqs = {
                    'requests': [
                        self.commands.login,
                        self.commands.qos,
                        self.commands.activity,
                        self.commands.quotes,
                    ]
                }

                try:

                    self.ws.send(
                        json.dumps(reqs)
                        )

                    _ = self.ws.recv()

                    for resp in json.loads(_)['response']:
                        code = resp['content']['code']
                        msg  = resp['content']['msg']
                        assert code == 0, f'{msg}'

                except:
                    continue

                assert self.ws.connected, 'websocket closed, retrying...'

                print('[*] websocket connected.')

                return self.ws

            except:
                error()


if __name__ == '__main__':

    conn = Connection()
    conn.connect()

    while True:

        data = conn.read()

        if data:
            
            print( data[:200] )
            time.sleep(.1)

    print('finito')

