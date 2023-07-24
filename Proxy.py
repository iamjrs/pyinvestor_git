from Imports import *

class Proxy:

    def __init__(self):

        self.server     = 'server_ip'
        self.port       = 12345
        self.username   = 'username_here'
        self.password   = 'password_here'

        self.header     = {
            'http':     f'http://{self.username}:{self.password}@{self.server}:{self.port}',
            'https':    f'https://{self.username}:{self.password}@{self.server}:{self.port}',
        }


if __name__ == '__main__':

    p   = Proxy()
    url = 'https://api.ipify.org?format=json'

    r = requests.get( url, proxies=p.header )

    print(r)
    print(r.text)

    print('\nfinito')