"""
Módulo completo para integração com Jellyfin
Autor: Assistant
Data: 2025-05-25
"""

import requests
import json
import logging
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import hashlib


class JellyfinError(Exception):
    """Exceção personalizada para erros do Jellyfin"""
    pass


class JellyfinAuth:
    """Classe para gerenciar autenticação do Jellyfin"""
    
    def __init__(self, base_url: str, username: str = None, password: str = None, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.access_token = None
        self.user_id = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """
        Autentica no Jellyfin usando credenciais ou API key
        
        Returns:
            bool: True se autenticação foi bem-sucedida
        """
        if self.api_key:
            # Usar API key diretamente
            self.access_token = self.api_key
            self._set_auth_headers()
            return self._validate_auth()
        
        elif self.username and self.password:
            # Autenticar com usuário e senha
            return self._authenticate_user()
        
        else:
            raise JellyfinError("É necessário fornecer API key ou credenciais de usuário")
    
    def _authenticate_user(self) -> bool:
        """Autentica usuário com credenciais"""
        auth_data = {
            "Username": self.username,
            "Pw": self._get_password_hash(self.password)
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._get_auth_header()
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/Users/authenticatebyname",
                json=auth_data,
                headers=headers
            )
            response.raise_for_status()
            
            auth_result = response.json()
            self.access_token = auth_result["AccessToken"]
            self.user_id = auth_result["User"]["Id"]
            
            self._set_auth_headers()
            return True
            
        except requests.RequestException as e:
            raise JellyfinError(f"Erro na autenticação: {e}")
    
    def _get_password_hash(self, password: str) -> str:
        """Gera hash SHA1 da senha"""
        return hashlib.sha1(password.encode()).hexdigest()
    
    def _get_auth_header(self) -> str:
        """Gera header de autorização"""
        client = "JellyfinPythonModule"
        device = "Python"
        device_id = "python-module-001"
        version = "1.0.0"
        
        return f'MediaBrowser Client="{client}", Device="{device}", DeviceId="{device_id}", Version="{version}"'
    
    def _set_auth_headers(self):
        """Define headers de autenticação para a sessão"""
        auth_header = f'MediaBrowser Token="{self.access_token}"'
        if self.user_id:
            auth_header += f', UserId="{self.user_id}"'
            
        self.session.headers.update({
            "X-Emby-Authorization": auth_header,
            "Content-Type": "application/json"
        })
    
    def _validate_auth(self) -> bool:
        """Valida se a autenticação está funcionando"""
        try:
            response = self.session.get(f"{self.base_url}/System/Info")
            return response.status_code == 200
        except:
            return False


class JellyfinClient:
    """Cliente principal para interação com Jellyfin"""
    
    def __init__(self, base_url: str, username: str = None, password: str = None, api_key: str = None):
        self.auth = JellyfinAuth(base_url, username, password, api_key)
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(__name__)
        self.server_id = None  # Será preenchido quando a conexão for estabelecida
        
        # Configurar a sessão com a API key diretamente
        if api_key:
            self.auth.access_token = api_key
            self.auth._set_auth_headers()
            
            # Verificar se a autenticação está funcionando
            try:
                # Primeiro, verificar se o servidor está acessível
                response = self.auth.session.get(f"{self.base_url}/System/Info", timeout=10)
                if response.status_code == 200:
                    server_info = response.json()
                    self.logger.info(f"Conectado ao servidor Jellyfin versão {server_info.get('Version')}")
                else:
                    raise JellyfinError(f"Falha na autenticação. Código de status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                raise JellyfinError(f"Não foi possível conectar ao servidor Jellyfin em {self.base_url}. Erro: {str(e)}")
            except Exception as e:
                raise JellyfinError(f"Erro ao validar a API key: {str(e)}")
        # Autenticar com usuário/senha se não houver API key
        elif not self.auth.authenticate():
            raise JellyfinError("Falha na autenticação com as credenciais fornecidas")
    
    def check_connection(self) -> Dict:
        """
        Verifica a conexão com o servidor Jellyfin e retorna informações do sistema
        
        Returns:
            Dicionário com informações do servidor ou mensagem de erro
        """
        try:
            # Primeiro, verificar se o servidor está acessível
            response = requests.get(f"{self.base_url}/System/Info", timeout=10)
            
            if response.status_code == 200:
                server_info = response.json()
                # Obter o ID do servidor se disponível
                server_id = server_info.get('Id')
                
                result = {
                    'status': 'success',
                    'server_name': server_info.get('ServerName', 'Desconhecido'),
                    'version': server_info.get('Version', 'Desconhecida'),
                    'operating_system': server_info.get('OperatingSystem', 'Desconhecido'),
                    'server_id': server_id,
                    'message': f"Conexão bem-sucedida com o servidor Jellyfin {server_info.get('Version', '')}"
                }
                
                # Se não tiver server_id, tentar obter de outra forma
                if not server_id:
                    try:
                        # Tentar obter o serverId da resposta de autenticação
                        auth_response = requests.get(
                            f"{self.base_url}/System/Info/Public",
                            timeout=10
                        )
                        if auth_response.status_code == 200:
                            auth_info = auth_response.json()
                            result['server_id'] = auth_info.get('Id')
                    except:
                        pass
                        
                # Armazenar o server_id na instância para uso futuro
                if result.get('server_id'):
                    self.server_id = result['server_id']
                        
                return result
            else:
                return {
                    'status': 'error',
                    'message': f"Falha na conexão. Código de status: {response.status_code}",
                    'response': response.text[:500]  # Mostrar apenas os primeiros 500 caracteres da resposta
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f"Erro ao conectar ao servidor: {str(e)}"
            }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Faz requisição HTTP para o Jellyfin
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (sem a base URL)
            **kwargs: Argumentos adicionais para requests.request()
            
        Returns:
            Resposta da requisição
            
        Raises:
            JellyfinError: Em caso de erro na requisição
        """
        url = f"{self.base_url}{endpoint}"
        
        # Adicionar headers padrão se não fornecidos
        headers = kwargs.pop('headers', {})
        if 'X-Emby-Token' not in headers and 'Authorization' not in headers and self.auth.access_token:
            headers['X-Emby-Token'] = self.auth.access_token
        
        # Adicionar parâmetros de autenticação se necessário
        params = kwargs.pop('params', {})
        if 'api_key' not in params and self.auth.access_token:
            params['api_key'] = self.auth.access_token
            
        try:
            response = self.auth.session.request(
                method,
                url,
                headers=headers,
                params=params,
                **kwargs
            )
            
            # Verificar se houve erro na resposta
            if response.status_code >= 400:
                error_msg = f"Erro {response.status_code} ao acessar {url}"
                try:
                    error_data = response.json()
                    if 'Message' in error_data:
                        error_msg += f": {error_data['Message']}"
                except:
                    error_msg += f": {response.text[:200]}"
                raise JellyfinError(error_msg)
                
            return response
            
        except requests.exceptions.Timeout:
            raise JellyfinError("Tempo limite excedido ao tentar acessar o servidor")
        except requests.exceptions.TooManyRedirects:
            raise JellyfinError("Muitos redirecionamentos ao tentar acessar o servidor")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição {method} {url}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'Message' in error_data:
                        raise JellyfinError(f"Erro no servidor: {error_data['Message']}")
                except:
                    pass
            raise JellyfinError(f"Erro na comunicação com o servidor: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao processar requisição {method} {url}: {str(e)}")
            raise JellyfinError(f"Erro inesperado: {str(e)}")
    
    def get_system_info(self) -> Dict:
        """Obtém informações do sistema Jellyfin"""
        response = self._make_request("GET", "/System/Info")
        return response.json()
    
    def search_media(self, query: str, media_types: List[str] = None, limit: int = 20) -> List[Dict]:
        """
        Busca mídia no Jellyfin
        
        Args:
            query: Termo de busca
            media_types: Tipos de mídia ['Movie', 'Series', 'Episode', 'Audio', etc.]
            limit: Limite de resultados
            
        Returns:
            Lista de itens encontrados
        """
        if media_types is None:
            media_types = ['Movie', 'Series']
        
        params = {
            'searchTerm': query,
            'IncludeItemTypes': ','.join(media_types),
            'Recursive': 'true',
            'Limit': limit,
            'Fields': 'BasicSyncInfo,CanDelete,PrimaryImageAspectRatio,ProductionYear,Status,EndDate'
        }
        
        response = self._make_request("GET", "/Items", params=params)
        return response.json().get('Items', [])
    
    def get_item_details(self, item_id: str) -> Dict:
        """
        Obtém detalhes de um item específico
        
        Args:
            item_id: ID do item
            
        Returns:
            Detalhes do item
        """
        response = self._make_request("GET", f"/Items/{item_id}")
        return response.json()
    
    def get_seasons(self, series_id: str) -> List[Dict]:
        """
        Obtém temporadas de uma série
        
        Args:
            series_id: ID da série
            
        Returns:
            Lista de temporadas
        """
        params = {
            'ParentId': series_id,
            'IncludeItemTypes': 'Season',
            'Fields': 'BasicSyncInfo,PrimaryImageAspectRatio'
        }
        
        response = self._make_request("GET", "/Items", params=params)
        return response.json().get('Items', [])
    
    def get_episodes(self, series_id: str, season_id: str = None) -> List[Dict]:
        """
        Obtém episódios de uma série ou temporada
        
        Args:
            series_id: ID da série
            season_id: ID da temporada (opcional)
            
        Returns:
            Lista de episódios
        """
        params = {
            'ParentId': season_id or series_id,
            'IncludeItemTypes': 'Episode',
            'Fields': 'BasicSyncInfo,PrimaryImageAspectRatio,Overview',
            'SortBy': 'SortName'
        }
        
        response = self._make_request("GET", "/Items", params=params)
        return response.json().get('Items', [])
    
    def get_libraries(self) -> List[Dict]:
        """Obtém todas as bibliotecas do usuário"""
        response = self._make_request("GET", "/Items")
        return response.json().get('Items', [])
    
    def get_recently_added(self, limit: int = 20) -> List[Dict]:
        """
        Obtém itens adicionados recentemente
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de itens recentes
        """
        params = {
            'Limit': limit,
            'Fields': 'BasicSyncInfo,PrimaryImageAspectRatio,ProductionYear',
            'IncludeItemTypes': 'Movie,Series',
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending',
            'Recursive': 'true'
        }
        
        response = self._make_request("GET", "/Items", params=params)
        return response.json().get('Items', [])
    
    def get_continue_watching(self, limit: int = 10) -> List[Dict]:
        """
        Obtém itens para continuar assistindo
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de itens para continuar
        """
        if not self.auth.user_id:
            return []
        
        params = {
            'Limit': limit,
            'Fields': 'BasicSyncInfo,PrimaryImageAspectRatio',
            'MediaTypes': 'Video',
            'IsResumable': 'true'
        }
        
        response = self._make_request("GET", f"/Users/{self.auth.user_id}/Items/Resume", params=params)
        return response.json().get('Items', [])

    def get_resumable_items(self, limit: int = 10) -> list:
        """Obtém itens que podem ser retomados"""
        params = {
            'UserId': self.auth.user_id,
            'Limit': limit,
            'Fields': 'PrimaryImageAspectRatio,BasicSyncInfo',
            'EnableTotalRecordCount': 'false',
            'MediaTypes': 'Video',
            'IsResumable': 'true'
        }
        
        response = self._make_request("GET", f"/Users/{self.auth.user_id}/Items/Resume", params=params)
        return response.json().get('Items', [])


class JellyfinLinks:
    """Classe para gerenciar links do Jellyfin"""
    
    def __init__(self, base_url: str, api_key: str = None, server_id: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.server_id = server_id
        
        # Se não tiver server_id, tentar obter do servidor
        if not self.server_id:
            try:
                client = JellyfinClient(base_url, api_key=api_key)
                connection_info = client.check_connection()
                if connection_info.get('status') == 'success' and 'server_id' in connection_info:
                    self.server_id = connection_info['server_id']
            except:
                pass  # Se não conseguir obter o server_id, continua sem ele
    
    def get_web_link(self, item_id: str, item_type: str = None, server_id: str = None) -> str:
        """
        Gera link para interface web do Jellyfin
        
        Args:
            item_id: ID do item
            item_type: Tipo do item (Movie, Series, Episode) - Não utilizado, mantido para compatibilidade
            server_id: ID do servidor (opcional, usa o armazenado na instância se não fornecido)
            
        Returns:
            URL para interface web
        """
        # Usar o server_id fornecido ou o armazenado na instância
        effective_server_id = server_id or self.server_id
        
        # Formato de URL padrão para o Jellyfin Web
        # Exemplo: http://192.168.1.30:8097/web/index.html#/details?id=ITEM_ID&serverId=SERVER_ID
        server_param = f"&serverId={effective_server_id}" if effective_server_id else ""
        return f"{self.base_url}/web/index.html#/details?id={item_id}{server_param}"
    
    def check_connection(self) -> Dict:
        """
        Verifica a conexão com o servidor Jellyfin e retorna informações do sistema
        
        Returns:
            Dicionário com informações do servidor ou mensagem de erro
        """
        try:
            # Primeiro, verificar se o servidor está acessível
            response = requests.get(f"{self.base_url}/System/Info", timeout=10)
            
            if response.status_code == 200:
                server_info = response.json()
                # Obter o ID do servidor se disponível
                server_id = server_info.get('Id')
                
                result = {
                    'status': 'success',
                    'server_name': server_info.get('ServerName', 'Desconhecido'),
                    'version': server_info.get('Version', 'Desconhecida'),
                    'operating_system': server_info.get('OperatingSystem', 'Desconhecido'),
                    'server_id': server_id,
                    'message': f"Conexão bem-sucedida com o servidor Jellyfin {server_info.get('Version', '')}"
                }
                
                # Se não tiver server_id, tentar obter de outra forma
                if not server_id:
                    try:
                        # Tentar obter o serverId da resposta de autenticação
                        auth_response = requests.get(
                            f"{self.base_url}/System/Info/Public",
                            timeout=10
                        )
                        if auth_response.status_code == 200:
                            auth_info = auth_response.json()
                            result['server_id'] = auth_info.get('Id')
                    except:
                        pass
                        
                return result
            else:
                return {
                    'status': 'error',
                    'message': f"Falha na conexão. Código de status: {response.status_code}",
                    'response': response.text[:500]  # Mostrar apenas os primeiros 500 caracteres da resposta
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f"Erro ao conectar ao servidor: {str(e)}"
            }
    
    def get_stream_link(self, item_id: str, **params) -> str:
        """
        Gera link direto para stream
        
        Args:
            item_id: ID do item
            **params: Parâmetros adicionais (quality, bitrate, etc.)
            
        Returns:
            URL para stream direto
        """
        base_params = {
            'Static': 'true',
            'MediaSourceId': item_id,
            'api_key': self.api_key
        }
        base_params.update(params)
        
        param_string = '&'.join([f"{k}={v}" for k, v in base_params.items() if v is not None])
        return f"{self.base_url}/Items/{item_id}/Download?{param_string}"
    
    def get_download_link(self, item_id: str) -> str:
        """
        Gera link para download do item
        
        Args:
            item_id: ID do item
            
        Returns:
            URL para download
        """
        params = f"api_key={self.api_key}" if self.api_key else ""
        return f"{self.base_url}/Items/{item_id}/Download?{params}"
    
    def get_image_link(self, item_id: str, image_type: str = 'Primary', max_width: int = None, max_height: int = None) -> str:
        """
        Gera link para imagem do item
        
        Args:
            item_id: ID do item
            image_type: Tipo da imagem (Primary, Backdrop, Logo, etc.)
            max_width: Largura máxima
            max_height: Altura máxima
            
        Returns:
            URL da imagem
        """
        params = []
        if max_width:
            params.append(f"maxWidth={max_width}")
        if max_height:
            params.append(f"maxHeight={max_height}")
        if self.api_key:
            params.append(f"api_key={self.api_key}")
        
        param_string = '&'.join(params)
        base_url = f"{self.base_url}/Items/{item_id}/Images/{image_type}"
        
        return f"{base_url}?{param_string}" if param_string else base_url
    
    def get_mobile_deep_links(self, item_id: str, server_id: str = "default") -> Dict[str, str]:
        """
        Gera deep links para apps móveis
        
        Args:
            item_id: ID do item
            server_id: ID do servidor
            
        Returns:
            Dicionário com links para diferentes plataformas
        """
        return {
            'android': f"intent://details?id={item_id}&serverId={server_id}#Intent;scheme=jellyfin;package=org.jellyfin.mobile;end",
            'ios': f"jellyfin://details?id={item_id}&serverId={server_id}",
            'universal': self.get_web_link(item_id)
        }


class JellyfinFormatter:
    """Classe para formatar dados do Jellyfin"""
    
    @staticmethod
    def format_item_info(item: Dict) -> Dict[str, str]:
        """
        Formata informações de um item para exibição
        
        Args:
            item: Dados do item do Jellyfin
            
        Returns:
            Dicionário com informações formatadas
        """
        name = item.get('Name', 'Sem título')
        year = item.get('ProductionYear', '')
        item_type = item.get('Type', '')
        overview = item.get('Overview', 'Sem descrição disponível')
        
        # Truncar overview se muito longa
        if len(overview) > 200:
            overview = overview[:197] + "..."
        
        # Formatação específica por tipo
        if item_type == 'Movie':
            title = f"🎬 {name}"
            if year:
                title += f" ({year})"
        elif item_type == 'Series':
            title = f"📺 {name}"
            if year:
                title += f" ({year})"
        elif item_type == 'Episode':
            season = item.get('ParentIndexNumber', '')
            episode = item.get('IndexNumber', '')
            series_name = item.get('SeriesName', '')
            
            title = f"📺 {series_name}"
            if season and episode:
                title += f" - S{season:02d}E{episode:02d}"
            title += f" - {name}"
        else:
            title = f"📁 {name}"
        
        return {
            'title': title,
            'overview': overview,
            'type': item_type,
            'year': str(year) if year else '',
            'id': item.get('Id', ''),
            'name': name
        }
    
    @staticmethod
    def format_duration(ticks: int) -> str:
        """
        Converte ticks do Jellyfin para formato de duração legível
        
        Args:
            ticks: Ticks do Jellyfin (100 nanosegundos)
            
        Returns:
            String formatada (ex: "1h 30m")
        """
        if not ticks:
            return "Duração desconhecida"
        
        # Converter ticks para segundos
        seconds = ticks / 10000000
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @staticmethod
    def format_file_size(size: int) -> str:
        """
        Formata tamanho de arquivo
        
        Args:
            size: Tamanho em bytes
            
        Returns:
            String formatada (ex: "1.5 GB")
        """
        if not size:
            return "Tamanho desconhecido"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        
        return f"{size:.1f} PB"


# Exemplo de uso
if __name__ == "__main__":
    # Configuração
    JELLYFIN_URL = "http://localhost:8096"
    API_KEY = "sua_api_key_aqui"
    # ou use credenciais
    # USERNAME = "seu_usuario"
    # PASSWORD = "sua_senha"
    
    try:
        # Inicializar cliente
        print(f"Conectando ao servidor Jellyfin em {JELLYFIN_URL}...")
        client = JellyfinClient(JELLYFIN_URL, api_key=API_KEY)
        
        # Verificar conexão e obter server_id
        print("Verificando conexão com o servidor...")
        connection_info = client.check_connection()
        server_id = connection_info.get('server_id') if connection_info.get('status') == 'success' else None
        print(f"Conectado ao servidor {connection_info.get('server_name', 'Desconhecido')} (ID: {server_id or 'N/A'})")
        
        # Inicializar links com o server_id
        links = JellyfinLinks(JELLYFIN_URL, API_KEY, server_id=server_id)
        
        # Buscar filmes
        print("\nBuscando filmes...")
        resultados = client.search_media("Matrix", ["Movie"])
        
        if not resultados:
            print("Nenhum resultado encontrado.")
        else:
            print(f"Encontrados {len(resultados)} resultados. Exibindo os 3 primeiros...")
        
        for item in resultados[:3]:
            # Formatar informações
            info = JellyfinFormatter.format_item_info(item)
            
            # Gerar links
            web_link = links.get_web_link(item['Id'])
            download_link = links.get_download_link(item['Id'])
            mobile_links = links.get_mobile_deep_links(item['Id'], server_id=server_id or "default")
            
            print("\n" + "="*50)
            print(f"Título: {info.get('title', 'N/A')}")
            print(f"Ano: {info.get('year', 'N/A')}")
            print(f"Duração: {info.get('runtime', 'N/A')}")
            print(f"Avaliação: {info.get('rating', 'N/A')}")
            print(f"Gêneros: {', '.join(info.get('genres', [])) or 'N/A'}")
            print(f"\nDescrição: {info.get('overview', 'Nenhuma descrição disponível.')}")
            print("\nLinks:")
            print(f"- Web: {web_link}")
            print(f"- Download: {download_link}")
            
            if mobile_links:
                print("\nLinks móveis:")
                for platform, link in mobile_links.items():
                    if link:  # Só mostrar links não vazios
                        print(f"- {platform}: {link}")
        
        print("\n" + "="*50 + "\n")
        print("Exemplo concluído com sucesso!")
            
    except JellyfinError as e:
        print(f"\n❌ Erro do Jellyfin: {e}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro de conexão: Não foi possível conectar ao servidor em {JELLYFIN_URL}")
        print(f"Verifique se o endereço está correto e se o servidor está em execução.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
