from urllib3.exceptions import InsecureRequestWarning
from selenium.webdriver import Chrome, ChromeOptions
from urllib.parse import quote, unquote
from urllib3 import disable_warnings
from functions import error
import webbrowser
import requests
import socket
import base64
import json
import time
import re
import os

# cred information
client_id    = 'client_id_here'
redirect_uri = 'http://127.0.0.1'
username     = 'username_here'
password     = input('password: ')

auth_url  = 'https://auth.tdameritrade.com/auth?'
auth_url += 'response_type=code&'
auth_url += 'redirect_uri={}&'.format( quote(redirect_uri, safe="") )
auth_url += 'client_id={}'.format( quote(client_id, safe="") )

test_url = 'https://api.tdameritrade.com/v1/oauth2/token'

b64_creds = base64.b64encode(
    bytes(f'{username}:{password}', 'utf-8')
    ).decode()

if __name__ == '__main__':

    # test existing tokens
    if os.path.exists('data\\files\\refresh_token'):
        with open('data\\files\\refresh_token', 'r') as _tokenfile:
            with requests.post( test_url, data=json.loads(_tokenfile.read()) ) as r:
                status = r.status_code
                if status == 200:
                    print('[*] authentication successful, code', status)
                    exit()
                else:
                    print('[!] auth failure, generating new tokens...')

    try:

        # verify that 127.0.0.1:80 is listening
        addr = '127.0.0.1'
        listening = socket.create_connection((addr, 80))

        # get new code
        options = ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-notifications')

        chrome = Chrome('data\\files\\chromedriver.exe', options=options)
        chrome.get(auth_url)

        uname_field = chrome.find_element_by_xpath('//*[@id="username0"]')
        uname_field.send_keys(username)

        pword_field = chrome.find_element_by_xpath('//*[@id="password1"]')
        pword_field.send_keys(password)

        submit_button = chrome.find_element_by_xpath('//*[@id="accept"]')
        submit_button.click()

        continue_button = chrome.find_element_by_xpath('//*[@id="accept"]')
        continue_button.click()

        remember_button = chrome.find_element_by_xpath(".//*[contains(text(), 'Trust this device')]")
        remember_button.click()

        new_auth_code = None

        last_url = chrome.current_url

        while True:
            if chrome.current_url != last_url:
                last_url = chrome.current_url
                groups = re.search(
                    r'code=(.+)',
                    chrome.current_url
                    )
                if groups is not None:
                    new_auth_code = groups.groups()[0]
                    new_auth_code = unquote(new_auth_code)
                    print('[*] new_auth_code obtained')
                    break

        chrome.quit()

        auth_head = {'authorization': f'basic {b64_creds}'}
        auth_body  = {
            'grant_type': 'authorization_code',
            'access_type': 'offline',
            'code': new_auth_code,
            'client_id': client_id,
            'redirect_uri': redirect_uri
        }

        r = requests.post(
            url     = test_url,
            data    = auth_body
            )

        assert r.status_code == 200

        refresh_token = json.loads(r.content)['refresh_token']

        tokens = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id
        }

        with open('data\\files\\refresh_token', 'w') as _file:
            _file.write(json.dumps(tokens))
            _file.close()

        print('[*] tokens file created successfully')
        print('finito')

    except:
        error()
        exit()