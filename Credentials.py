from Imports import *

class Credentials:

    def __init__(self):

        while True:
            try:
                with open('data\\files\\refresh_token', 'r') as _:

                    self.refresh_token = json.loads(_.read())
                    self.client_id = self.refresh_token['client_id']
                    _.close()

                with requests.post(
                    'https://api.tdameritrade.com/v1/oauth2/token',
                    data=self.refresh_token
                    ) as _:

                    self.access_token = json.loads(_.content)['access_token']
                    _.close()

                self.request_id = 0

                with requests.get(
                    'https://api.tdameritrade.com/v1/userprincipals?fields=streamerSubscriptionKeys%2CstreamerConnectionInfo',
                    headers={'Authorization': f'Bearer {self.access_token}'}
                    ) as _:

                    self.userprincipals = json.loads(_.content)
                    _.close()

                self.accountId = self.userprincipals['accounts'][0]['accountId']
                self.streamKey = self.userprincipals['streamerSubscriptionKeys']['keys'][0]['key']

                self.credentials = {
                    'userid':      self.accountId,
                    'token':       self.userprincipals['streamerInfo']['token'],
                    'company':     self.userprincipals['accounts'][0]['company'],
                    'segment':     self.userprincipals['accounts'][0]['segment'],
                    'cddomain':    self.userprincipals['accounts'][0]['accountCdDomainId'],
                    'usergroup':   self.userprincipals['streamerInfo']['userGroup'],
                    'accesslevel': self.userprincipals['streamerInfo']['accessLevel'],
                    'authorized':  'Y',
                    'timestamp': int((
                        datetime.strptime(self.userprincipals['streamerInfo']['tokenTimestamp'][:-5], '%Y-%m-%dT%H:%M:%S')
                            - datetime.utcfromtimestamp(0)).total_seconds() * 1000.0),
                    'appid': self.userprincipals['streamerInfo']['appId'],
                    'acl': self.userprincipals['streamerInfo']['acl']
                }

                old = self.credentials
                unpack(self, self.credentials)
                self.json = old
                break

            except:
                error()
                time.sleep(1)
                continue

    def remaining(self):
        expiration  = datetime.fromisoformat( self.userprincipals['tokenExpirationTime'].split('+')[0] )
        remaining   = expiration.timestamp() - datetime.utcnow().timestamp()
        return remaining

if __name__ == '__main__':

    creds = Credentials()
