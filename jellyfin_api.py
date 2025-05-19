import requests
import os
from dotenv import load_dotenv

load_dotenv()

JELLYFIN_URL = os.getenv('JELLYFIN_URL')
JELLYFIN_USER = os.getenv('JELLYFIN_USER')
JELLYFIN_PASS = os.getenv('JELLYFIN_PASS')

class JellyfinAPI:
    def __init__(self, url=None, user=None, password=None):
        self.url = url or JELLYFIN_URL
        self.user = user or JELLYFIN_USER
        self.password = password or JELLYFIN_PASS
        self.token = None
        self.user_id = None

    def authenticate(self):
        headers = {
            'Content-Type': 'application/json',
            'X-Emby-Authorization': f'MediaBrowser Client="JellyfinBot", Device="TelegramBot", DeviceId="telegrambot", Version="1.0"'
        }
        data = {
            'Username': self.user,
            'Pw': self.password
        }
        resp = requests.post(f'{self.url}/Users/AuthenticateByName', json=data, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        self.token = result['AccessToken']
        self.user_id = result['User']['Id']
        return self.token

    def get_libraries(self):
        if not self.token:
            self.authenticate()
        headers = {
            'X-Emby-Token': self.token
        }
        resp = requests.get(f'{self.url}/Users/{self.user_id}/Items', headers=headers)
        resp.raise_for_status()
        return resp.json()

    def search_media(self, query):
        if not self.token:
            self.authenticate()
        headers = {
            'X-Emby-Token': self.token
        }
        params = {'SearchTerm': query}
        resp = requests.get(f'{self.url}/Search/Hints', headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()