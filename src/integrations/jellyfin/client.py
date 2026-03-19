import asyncio
import aiohttp
import requests
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class JellyfinClient:
    """Cliente unificado para interação com Jellyfin (síncrono e assíncrono)"""

    def __init__(self, url: str, username: str = None, password: str = None, api_key: str = None):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.session = None
        self.access_token = None
        self.user_id = None

    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Optional[Dict]:
        if not self.session:
            self.session = requests.Session()

        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-Emby-Token'] = self.api_key
        elif self.access_token:
            headers['X-Emby-Token'] = self.access_token

        url = f"{self.url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return None

    async def _make_async_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Optional[Dict]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-Emby-Token'] = self.api_key
        elif self.access_token:
            headers['X-Emby-Token'] = self.access_token

        url = f"{self.url}{endpoint}"
        try:
            if method.upper() == 'GET':
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json() if response.content_length else {}
            elif method.upper() == 'POST':
                async with session.post(url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    return await response.json() if response.content_length else {}
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
        except aiohttp.ClientError as e:
            logger.error(f"Erro na requisição assíncrona para {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return None

    def authenticate(self) -> bool:
        if not self.username or not self.password:
            return False
        auth_data = {'Username': self.username, 'Pw': self.password}
        result = self._make_request('/Users/authenticatebyname', 'POST', data=auth_data)
        if result and 'AccessToken' in result:
            self.access_token = result['AccessToken']
            self.user_id = result.get('User', {}).get('Id')
            logger.info("Autenticação no Jellyfin bem-sucedida")
            return True
        logger.error("Falha na autenticação do Jellyfin")
        return False

    async def authenticate_async(self, session: aiohttp.ClientSession) -> bool:
        if not self.username or not self.password:
            return False
        auth_data = {'Username': self.username, 'Pw': self.password}
        result = await self._make_async_request(session, '/Users/authenticatebyname', 'POST', data=auth_data)
        if result and 'AccessToken' in result:
            self.access_token = result['AccessToken']
            self.user_id = result.get('User', {}).get('Id')
            logger.info("Autenticação assíncrona no Jellyfin bem-sucedida")
            return True
        logger.error("Falha na autenticação assíncrona do Jellyfin")
        return False

    def get_system_info(self) -> Optional[Dict]:
        return self._make_request('/System/Info')

    def get_libraries(self) -> List[Dict]:
        result = self._make_request('/Library/VirtualFolders')
        return result if result else []

    def get_recently_added(self, limit: int = 10) -> List[Dict]:
        params = {
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series,Episode',
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending',
        }
        if self.user_id:
            result = self._make_request(f'/Users/{self.user_id}/Items', params=params)
        else:
            result = self._make_request('/Items', params=params)
        return result.get('Items', []) if result else []

    async def get_recent_items_async(self, session: aiohttp.ClientSession, limit: int = 10) -> List[Dict]:
        params = {
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series,Episode',
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending',
        }
        if self.user_id:
            result = await self._make_async_request(session, f'/Users/{self.user_id}/Items', params=params)
        else:
            result = await self._make_async_request(session, '/Items', params=params)
        return result.get('Items', []) if result else []

    def search_items(self, query: str, limit: int = 10) -> List[Dict]:
        params = {
            'searchTerm': query,
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series,Episode',
        }
        if self.user_id:
            result = self._make_request(f'/Users/{self.user_id}/Items', params=params)
        else:
            result = self._make_request('/Items', params=params)
        return result.get('Items', []) if result else []

    def get_item_details(self, item_id: str) -> Optional[Dict]:
        if self.user_id:
            return self._make_request(f'/Users/{self.user_id}/Items/{item_id}')
        return self._make_request(f'/Items/{item_id}')

    def get_web_link(self, item_id: str) -> str:
        return f"{self.url}/web/index.html#!/details?id={item_id}"
