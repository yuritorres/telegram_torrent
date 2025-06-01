import os
import asyncio
import aiohttp
import requests
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
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
        """Faz requisição síncrona para a API do Jellyfin"""
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
        """Faz requisição assíncrona para a API do Jellyfin"""
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
        """Autentica com o servidor Jellyfin usando username/password"""
        if not self.username or not self.password:
            return False
            
        auth_data = {
            'Username': self.username,
            'Pw': self.password
        }
        
        result = self._make_request('/Users/authenticatebyname', 'POST', data=auth_data)
        if result and 'AccessToken' in result:
            self.access_token = result['AccessToken']
            self.user_id = result.get('User', {}).get('Id')
            logger.info("Autenticação no Jellyfin bem-sucedida")
            return True
            
        logger.error("Falha na autenticação do Jellyfin")
        return False
    
    async def authenticate_async(self, session: aiohttp.ClientSession) -> bool:
        """Autentica assincronamente com o servidor Jellyfin"""
        if not self.username or not self.password:
            return False
            
        auth_data = {
            'Username': self.username,
            'Pw': self.password
        }
        
        result = await self._make_async_request(session, '/Users/authenticatebyname', 'POST', data=auth_data)
        if result and 'AccessToken' in result:
            self.access_token = result['AccessToken']
            self.user_id = result.get('User', {}).get('Id')
            logger.info("Autenticação assíncrona no Jellyfin bem-sucedida")
            return True
            
        logger.error("Falha na autenticação assíncrona do Jellyfin")
        return False
    
    def get_system_info(self) -> Optional[Dict]:
        """Obtém informações do sistema Jellyfin"""
        return self._make_request('/System/Info')
    
    def get_libraries(self) -> List[Dict]:
        """Obtém lista de bibliotecas"""
        result = self._make_request('/Library/VirtualFolders')
        return result if result else []
    
    def get_recently_added(self, limit: int = 10) -> List[Dict]:
        """Obtém itens recentemente adicionados"""
        params = {
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series,Episode',
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending'
        }
        
        if self.user_id:
            result = self._make_request(f'/Users/{self.user_id}/Items', params=params)
        else:
            result = self._make_request('/Items', params=params)
            
        return result.get('Items', []) if result else []
    
    async def get_recent_items_async(self, session: aiohttp.ClientSession, limit: int = 10) -> List[Dict]:
        """Obtém itens recentes assincronamente"""
        params = {
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series,Episode',
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending'
        }
        
        if self.user_id:
            result = await self._make_async_request(session, f'/Users/{self.user_id}/Items', params=params)
        else:
            result = await self._make_async_request(session, '/Items', params=params)
            
        return result.get('Items', []) if result else []
    
    def search_items(self, query: str, limit: int = 10) -> List[Dict]:
        """Busca itens por termo"""
        params = {
            'searchTerm': query,
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series,Episode'
        }
        
        if self.user_id:
            result = self._make_request(f'/Users/{self.user_id}/Items', params=params)
        else:
            result = self._make_request('/Items', params=params)
            
        return result.get('Items', []) if result else []
    
    def get_item_details(self, item_id: str) -> Optional[Dict]:
        """Obtém detalhes de um item específico"""
        if self.user_id:
            return self._make_request(f'/Users/{self.user_id}/Items/{item_id}')
        else:
            return self._make_request(f'/Items/{item_id}')
    
    def get_web_link(self, item_id: str) -> str:
        """Gera link web para um item"""
        return f"{self.url}/web/index.html#!/details?id={item_id}"

class JellyfinFormatter:
    """Classe para formatação de dados do Jellyfin"""
    
    @staticmethod
    def format_item_info(item: Dict) -> Dict[str, Any]:
        """Formata informações de um item do Jellyfin"""
        return {
            'title': item.get('Name', 'Sem título'),
            'type': item.get('Type', 'Desconhecido'),
            'year': item.get('ProductionYear'),
            'rating': item.get('CommunityRating'),
            'genres': item.get('Genres', []),
            'overview': item.get('Overview', ''),
            'id': item.get('Id')
        }
    
    @staticmethod
    def format_telegram_message(item: Dict, web_link: str = None) -> str:
        """Formata item para mensagem do Telegram"""
        info = JellyfinFormatter.format_item_info(item)
        
        message = f"📺 **{info['title']}**\n"
        message += f"▶️ Tipo: {info['type']}\n"
        
        if info['rating']:
            message += f"⭐ Avaliação: {info['rating']}\n"
        
        if info['year']:
            message += f"📅 Ano: {info['year']}\n"
        
        if info['genres']:
            message += f"🎭 Gêneros: {', '.join(info['genres'][:3])}\n"
        
        if info['overview']:
            overview = info['overview']
            if len(overview) > 200:
                overview = overview[:200] + "..."
            message += f"\n{overview}"
        
        return message.strip()

class JellyfinManager:
    """Gerenciador principal do Jellyfin para integração com Telegram"""
    
    def __init__(self):
        self.url = os.getenv('JELLYFIN_URL')
        self.username = os.getenv('JELLYFIN_USERNAME')
        self.password = os.getenv('JELLYFIN_PASSWORD')
        self.api_key = os.getenv('JELLYFIN_API_KEY')
        self.client = None
        self.known_items = set()
        
        if self.url:
            self.client = JellyfinClient(self.url, self.username, self.password, self.api_key)
            if self.username and self.password:
                self.client.authenticate()
    
    def is_available(self) -> bool:
        """Verifica se o Jellyfin está disponível"""
        return self.client is not None and (self.api_key or self.client.access_token)
    
    def get_recent_items_text(self, limit: int = 10) -> str:
        """Obtém texto formatado dos itens recentes"""
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        
        try:
            items = self.client.get_recently_added(limit)
            if not items:
                return "📥 Nenhum item recente encontrado."
            
            messages = []
            for item in items:
                web_link = self.client.get_web_link(item['Id'])
                message = JellyfinFormatter.format_telegram_message(item, web_link)
                messages.append(message)
            
            return "🎬 **Itens recentemente adicionados:**\n\n" + "\n\n".join(messages)
            
        except Exception as e:
            logger.error(f"Erro ao obter itens recentes: {e}")
            return f"❌ Erro ao buscar itens recentes: {str(e)}"
    
    def get_libraries_text(self) -> str:
        """Obtém texto formatado das bibliotecas"""
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        
        try:
            libraries = self.client.get_libraries()
            if not libraries:
                return "❌ Nenhuma biblioteca encontrada."
            
            text = "📚 **Bibliotecas Disponíveis:**\n\n"
            for lib in libraries:
                name = lib.get('Name', 'N/A')
                lib_type = lib.get('CollectionType', 'N/A')
                text += f"• {name} ({lib_type})\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Erro ao obter bibliotecas: {e}")
            return f"❌ Erro ao buscar bibliotecas: {str(e)}"
    
    def get_status_text(self) -> str:
        """Obtém texto de status do servidor"""
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        
        try:
            system_info = self.client.get_system_info()
            libraries = self.client.get_libraries()
            recent_items = self.client.get_recently_added(1)
            
            status_text = f"""🟢 **Status do Servidor Jellyfin**

🌐 Servidor: {self.url}
👤 Usuário: {self.username}
📚 Bibliotecas: {len(libraries)}
🆕 Último item: {recent_items[0].get('Name', 'N/A') if recent_items else 'N/A'}

✅ Conexão OK"""
            
            return status_text
            
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return f"❌ Erro de conexão: {str(e)}"