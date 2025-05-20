import requests
import os
import uuid
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

JELLYFIN_URL = os.getenv('JELLYFIN_URL')
JELLYFIN_USER = os.getenv('JELLYFIN_USER')
JELLYFIN_PASS = os.getenv('JELLYFIN_PASS')

def gen_device_id():
    return str(uuid.uuid4())

class JellyfinAPI:
    def __init__(self, url=None, user=None, password=None):
        self.url = url or JELLYFIN_URL
        if self.url and not (self.url.endswith("/emby") or self.url.endswith("/jellyfin")):
            if "jellyfin" in self.url.lower():
                self.url += "/jellyfin"
            else:
                self.url += "/emby"
        self.user = user or JELLYFIN_USER
        self.password = password or JELLYFIN_PASS
        self.token = None
        self.user_id = None
        self.device_id = gen_device_id()
        self.default_headers = {
            'Content-Type': 'application/json',
            'X-Emby-Client': 'TelegramBot',
            'X-Emby-Device-Name': 'TelegramBot',
            'X-Emby-Client-Version': '1.0.0',
            'X-Emby-Device-Id': self.device_id,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

    def authenticate(self):
        """Autentica no servidor Jellyfin/Emby e obtém o token de acesso"""
        try:
            headers = self.default_headers.copy()
            headers['X-Emby-Authorization'] = f'MediaBrowser Client="JellyfinBot", Device="TelegramBot", DeviceId="{self.device_id}", Version="1.0"'
            
            data = {
                'Username': self.user,
                'Pw': self.password
            }
            resp = requests.post(f'{self.url}/Users/AuthenticateByName', json=data, headers=headers, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            self.token = result['AccessToken']
            self.user_id = result['User']['Id']
            return self.token
        except requests.exceptions.ConnectionError:
            print(f"Erro de conexão ao autenticar no servidor: {self.url}")
            raise
        except requests.exceptions.Timeout:
            print(f"Timeout ao tentar autenticar no servidor: {self.url}")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP ao autenticar no servidor: {str(e)}")
            raise
        except Exception as e:
            print(f"Erro inesperado na autenticação: {str(e)}")
            raise

    def _get_auth_headers(self):
        """Retorna os headers com o token de autenticação"""
        try:
            if not self.token:
                self.authenticate()
            headers = self.default_headers.copy()
            headers['X-Emby-Token'] = self.token
            return headers
        except Exception as e:
            print(f"Erro ao obter headers de autenticação: {str(e)}")
            raise

    def get_libraries(self):
        """Obtém todas as bibliotecas disponíveis para o usuário"""
        headers = self._get_auth_headers()
        resp = requests.get(f'{self.url}/Users/{self.user_id}/Views', headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_items(self, parent_id=None, include_item_types=None, recursive=True, fields=None):
        """Obtém itens de uma biblioteca específica ou todos os itens"""
        headers = self._get_auth_headers()
        params = {
            'ParentId': parent_id,
            'Recursive': str(recursive).lower(),
            'SortBy': 'SortName',
            'SortOrder': 'Ascending'
        }
        if include_item_types:
            params['IncludeItemTypes'] = include_item_types
        if fields:
            params['Fields'] = fields
            
        resp = requests.get(f'{self.url}/Users/{self.user_id}/Items', headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def search_media(self, query, include_media_types=None, limit=20):
        """Pesquisa por mídia no servidor"""
        headers = self._get_auth_headers()
        params = {
            'SearchTerm': query,
            'Limit': limit
        }
        if include_media_types:
            params['IncludeMediaTypes'] = include_media_types
            
        resp = requests.get(f'{self.url}/Search/Hints', headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_item_details(self, item_id):
        """Obtém detalhes de um item específico"""
        headers = self._get_auth_headers()
        resp = requests.get(f'{self.url}/Users/{self.user_id}/Items/{item_id}', headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_system_info(self):
        """Obtém informações do sistema Jellyfin/Emby"""
        try:
            headers = self._get_auth_headers()
            resp = requests.get(f'{self.url}/System/Info/Public', headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter informações do sistema: {str(e)}")
            raise

    def get_users(self):
        """Obtém todos os usuários (requer permissão de administrador)"""
        headers = self._get_auth_headers()
        resp = requests.get(f'{self.url}/Users', headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_recently_added(self, limit=10, include_item_types=None):
        """Obtém itens adicionados recentemente"""
        headers = self._get_auth_headers()
        params = {
            'Limit': limit,
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending',
            'Recursive': 'true'
        }
        if include_item_types:
            params['IncludeItemTypes'] = include_item_types
            
        resp = requests.get(f'{self.url}/Users/{self.user_id}/Items/Latest', headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_sessions(self):
        """Obtém as sessões ativas no servidor (requer permissão de administrador)"""
        headers = self._get_auth_headers()
        resp = requests.get(f'{self.url}/Sessions', headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_server_activity(self):
        """Obtém a atividade do servidor (requer permissão de administrador)"""
        headers = self._get_auth_headers()
        resp = requests.get(f'{self.url}/System/ActivityLog/Entries', headers=headers)
        resp.raise_for_status()
        return resp.json()