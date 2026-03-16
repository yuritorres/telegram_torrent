#!/usr/bin/env python3
"""
API de integração com YTS Brasil (ytsbr.com)
Permite buscar e baixar filmes, séries e animes via torrent
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urljoin, quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YTSBRApi:
    """Cliente para interagir com o site YTS Brasil"""
    
    BASE_URL = "https://ytsbr.com"
    
    # Mapeamento de gêneros para filmes (IDs do TMDB)
    MOVIE_GENRES = {
        'acao': 28,
        'ação': 28,
        'aventura': 12,
        'animacao': 16,
        'animação': 16,
        'comedia': 35,
        'comédia': 35,
        'crime': 80,
        'documentario': 99,
        'documentário': 99,
        'drama': 18,
        'familia': 10751,
        'família': 10751,
        'fantasia': 14,
        'historia': 36,
        'história': 36,
        'terror': 27,
        'musica': 10402,
        'música': 10402,
        'misterio': 9648,
        'mistério': 9648,
        'romance': 10749,
        'ficcao': 878,
        'ficção': 878,
        'sci-fi': 878,
        'thriller': 53,
        'guerra': 10752,
        'faroeste': 37
    }
    
    # Gêneros para séries
    SERIES_GENRES = {
        'acao': 'Ação & Aventura',
        'ação': 'Ação & Aventura',
        'aventura': 'Ação & Aventura',
        'animacao': 'Animação',
        'animação': 'Animação',
        'comedia': 'Comédia',
        'comédia': 'Comédia',
        'crime': 'Crime',
        'documentario': 'Documentário',
        'documentário': 'Documentário',
        'drama': 'Drama',
        'familia': 'Família',
        'família': 'Família',
        'kids': 'Kids',
        'misterio': 'Mistério',
        'mistério': 'Mistério',
        'reality': 'Reality',
        'sci-fi': 'Sci-Fi & Fantasia',
        'ficcao': 'Sci-Fi & Fantasia',
        'ficção': 'Sci-Fi & Fantasia',
        'fantasia': 'Sci-Fi & Fantasia',
        'guerra': 'War & Politics',
        'faroeste': 'Faroeste'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, query: str, media_type: str = "all", limit: int = 10) -> List[Dict]:
        """
        Busca por filmes, séries ou animes
        
        Args:
            query: Termo de busca
            media_type: Tipo de mídia ('movie', 'series', 'anime', 'all')
            limit: Número máximo de resultados
            
        Returns:
            Lista de dicionários com informações dos resultados
        """
        try:
            results = []
            
            # Define as URLs de busca baseado no tipo
            search_urls = []
            if media_type in ["all", "movie"]:
                search_urls.append(f"{self.BASE_URL}/filmes-torrent/")
            if media_type in ["all", "series"]:
                search_urls.append(f"{self.BASE_URL}/series-torrent/")
            if media_type in ["all", "anime"]:
                search_urls.append(f"{self.BASE_URL}/animes-torrent/")
            
            for url in search_urls:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por cards de mídia
                media_cards = soup.find_all('a', href=True)
                
                for card in media_cards:
                    href = card.get('href', '')
                    
                    # Verifica se é um link de filme/série/anime
                    if not any(x in href for x in ['/filme/', '/serie/', '/anime/']):
                        continue
                    
                    # Extrai informações do card
                    title_elem = card.find(text=True, recursive=False)
                    if not title_elem:
                        continue
                    
                    title = title_elem.strip()
                    
                    # Filtra por query
                    if query.lower() not in title.lower():
                        continue
                    
                    # Extrai rating se disponível
                    rating = None
                    rating_elem = card.find(string=re.compile(r'\d+\s*%'))
                    if rating_elem:
                        rating = rating_elem.strip()
                    
                    # Determina o tipo
                    if '/filme/' in href:
                        item_type = 'movie'
                    elif '/serie/' in href:
                        item_type = 'series'
                    elif '/anime/' in href:
                        item_type = 'anime'
                    else:
                        continue
                    
                    # Extrai imagem
                    img_elem = card.find('img')
                    image_url = img_elem.get('src', '') if img_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': urljoin(self.BASE_URL, href),
                        'type': item_type,
                        'rating': rating,
                        'image': urljoin(self.BASE_URL, image_url) if image_url else None
                    })
                    
                    if len(results) >= limit:
                        break
                
                if len(results) >= limit:
                    break
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao buscar em ytsbr.com: {e}")
            return []
    
    def get_details(self, url: str) -> Optional[Dict]:
        """
        Obtém detalhes de um filme, série ou anime
        
        Args:
            url: URL da página do item
            
        Returns:
            Dicionário com informações detalhadas
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrai título
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Título desconhecido"
            
            # Extrai rating
            rating_elem = soup.find(string=re.compile(r'★\s*\d+\.?\d*'))
            rating = rating_elem.strip() if rating_elem else None
            
            # Extrai ano
            year_elem = soup.find(string=re.compile(r'\b(19|20)\d{2}\b'))
            year = year_elem.strip() if year_elem else None
            
            # Extrai duração
            duration_elem = soup.find(string=re.compile(r'\d+h\s*\d*min'))
            duration = duration_elem.strip() if duration_elem else None
            
            # Extrai gêneros
            genre_elem = soup.find(string=re.compile(r'•'))
            genres = genre_elem.strip() if genre_elem else None
            
            # Extrai sinopse
            synopsis = None
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 100:  # Provavelmente é a sinopse
                    synopsis = text
                    break
            
            # Extrai imagem
            img_elem = soup.find('img', src=re.compile(r'poster'))
            image_url = img_elem.get('src', '') if img_elem else None
            
            # Extrai informações de qualidade
            quality_info = self._extract_quality_info(soup)
            
            # Determina o tipo
            if '/filme/' in url:
                item_type = 'movie'
            elif '/serie/' in url:
                item_type = 'series'
            elif '/anime/' in url:
                item_type = 'anime'
            else:
                item_type = 'unknown'
            
            return {
                'title': title,
                'url': url,
                'type': item_type,
                'rating': rating,
                'year': year,
                'duration': duration,
                'genres': genres,
                'synopsis': synopsis,
                'image': urljoin(self.BASE_URL, image_url) if image_url else None,
                'quality': quality_info
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes de {url}: {e}")
            return None
    
    def _extract_quality_info(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extrai informações de qualidade dos torrents disponíveis
        
        Args:
            soup: BeautifulSoup object da página
            
        Returns:
            Lista de dicionários com informações de qualidade
        """
        quality_list = []
        
        try:
            # Procura por seções de download
            # Baseado na estrutura observada: IMAGEM DE CINEMA, QUALIDADE BAIXA, etc.
            
            # Procura por textos que indicam qualidade
            quality_indicators = [
                'IMAGEM DE CINEMA',
                'QUALIDADE BAIXA',
                'QUALIDADE MÉDIA',
                'QUALIDADE ALTA',
                'HD',
                '4K',
                'FULL HD',
                'CAM',
                'HDCAM',
                'WEBRIP',
                'BLURAY'
            ]
            
            # Busca por elementos que contenham essas informações
            all_text = soup.get_text()
            
            for indicator in quality_indicators:
                if indicator in all_text.upper():
                    # Tenta extrair informações adicionais próximas
                    quality_entry = {
                        'type': indicator,
                        'video_audio': None,
                        'resolution': None,
                        'language': None,
                        'size': None,
                        'format': None,
                        'codec': None
                    }
                    
                    # Procura por padrões de vídeo/áudio (ex: "Vídeo 9 • Áudio 9")
                    video_audio_match = re.search(r'Vídeo\s*(\d+)\s*•\s*Áudio\s*(\d+)', all_text, re.IGNORECASE)
                    if video_audio_match:
                        quality_entry['video_audio'] = f"Vídeo {video_audio_match.group(1)} • Áudio {video_audio_match.group(2)}"
                    
                    # Procura por resolução (HD, 1080p, 720p, etc.)
                    resolution_patterns = [
                        r'\b(4K|2160p)\b',
                        r'\b(FULL\s*HD|1080p)\b',
                        r'\b(HD|720p)\b',
                        r'\b(480p)\b'
                    ]
                    for pattern in resolution_patterns:
                        res_match = re.search(pattern, all_text, re.IGNORECASE)
                        if res_match:
                            quality_entry['resolution'] = res_match.group(1)
                            break
                    
                    # Procura por idioma
                    lang_match = re.search(r'(Original|Dublado|Legendado)', all_text, re.IGNORECASE)
                    if lang_match:
                        quality_entry['language'] = lang_match.group(1)
                    
                    # Procura por formato (MKV, MP4, AVI)
                    format_match = re.search(r'\b(MKV|MP4|AVI)\b', all_text, re.IGNORECASE)
                    if format_match:
                        quality_entry['format'] = format_match.group(1)
                    
                    # Procura por codec (H.264, H.265, x264, x265)
                    codec_match = re.search(r'\b(H\.264|H\.265|x264|x265|HEVC)\b', all_text, re.IGNORECASE)
                    if codec_match:
                        quality_entry['codec'] = codec_match.group(1)
                    
                    quality_list.append(quality_entry)
            
            # Se não encontrou nenhuma qualidade específica, tenta extrair informações gerais
            if not quality_list:
                # Procura por qualquer menção de HD, qualidade, etc.
                if re.search(r'\bHD\b', all_text, re.IGNORECASE):
                    quality_list.append({'type': 'HD', 'video_audio': None})
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações de qualidade: {e}")
        
        return quality_list if quality_list else [{'type': 'Qualidade não especificada', 'video_audio': None}]
    
    def get_magnet_link(self, url: str) -> Optional[str]:
        """
        Obtém o link magnet de um filme, série ou anime
        
        Args:
            url: URL da página do item
            
        Returns:
            Link magnet ou None se não encontrado
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procura por links magnet
            magnet_links = soup.find_all('a', href=re.compile(r'^magnet:\?'))
            
            if magnet_links:
                return magnet_links[0].get('href')
            
            # Se não encontrou diretamente, pode estar em um modal/popup
            # Procura por botões de download
            download_buttons = soup.find_all('a', string=re.compile(r'Baixar|Download', re.I))
            
            for button in download_buttons:
                # Tenta clicar no botão (simula)
                onclick = button.get('onclick', '')
                href = button.get('href', '')
                
                if 'magnet:?' in href:
                    return href
                
                # Se o botão abre um modal, precisamos fazer outra requisição
                if href and href != '#':
                    try:
                        modal_response = self.session.get(urljoin(url, href), timeout=10)
                        modal_soup = BeautifulSoup(modal_response.content, 'html.parser')
                        modal_magnet = modal_soup.find('a', href=re.compile(r'^magnet:\?'))
                        if modal_magnet:
                            return modal_magnet.get('href')
                    except:
                        pass
            
            logger.warning(f"Link magnet não encontrado em {url}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter link magnet de {url}: {e}")
            return None
    
    def search_by_genre(self, genre: str, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        """
        Busca por gênero/categoria
        
        Args:
            genre: Nome do gênero (ex: 'acao', 'drama', 'comedia')
            media_type: Tipo de mídia ('movie', 'series', 'anime')
            limit: Número máximo de resultados
            
        Returns:
            Lista de dicionários com informações dos itens
        """
        try:
            genre_lower = genre.lower()
            
            # Define a URL baseado no tipo e gênero
            if media_type == "movie":
                genre_id = self.MOVIE_GENRES.get(genre_lower)
                if not genre_id:
                    logger.warning(f"Gênero '{genre}' não encontrado para filmes")
                    return []
                url = f"{self.BASE_URL}/filmes-torrent/?genre={genre_id}"
            elif media_type == "series":
                genre_name = self.SERIES_GENRES.get(genre_lower)
                if not genre_name:
                    logger.warning(f"Gênero '{genre}' não encontrado para séries")
                    return []
                # Para séries, usa o nome do gênero na URL
                url = f"{self.BASE_URL}/series-torrent/"
            elif media_type == "anime":
                # Animes usam a mesma estrutura de séries
                url = f"{self.BASE_URL}/animes-torrent/"
            else:
                return []
            
            logger.info(f"Buscando gênero '{genre}' em {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Procura pela região de filmes (region com aria-label ou role)
            # ou pelo elemento main que contém os cards
            main_content = soup.find('main') or soup.find('region')
            
            if not main_content:
                logger.warning("Não foi possível encontrar o conteúdo principal da página")
                return []
            
            # Busca todos os links que apontam para filmes/séries/animes
            media_links = main_content.find_all('a', href=re.compile(r'/(filme|serie|anime)/'))
            
            for link in media_links:
                if len(results) >= limit:
                    break
                
                href = link.get('href', '')
                
                # Pula se não for um link válido
                if not href or href == '#':
                    continue
                
                # Extrai título - procura por texto dentro do link
                title = None
                # Tenta pegar o texto do link (geralmente o título está em um StaticText)
                text_elements = link.find_all(string=True)
                for text in text_elements:
                    text_clean = text.strip()
                    # Ignora porcentagens e anos
                    if text_clean and not re.match(r'^\d+\s*%?$', text_clean) and not re.match(r'^\d{2}\s+de\s+\w+', text_clean):
                        if len(text_clean) > 3:  # Título deve ter mais de 3 caracteres
                            title = text_clean
                            break
                
                if not title:
                    continue
                
                # Extrai rating (porcentagem)
                rating = None
                rating_texts = link.find_all(string=re.compile(r'^\d+$'))
                if len(rating_texts) >= 2:
                    # Geralmente o primeiro número seguido de % é o rating
                    rating = f"{rating_texts[0].strip()} %"
                
                # Extrai imagem
                img_elem = link.find('img')
                image_url = img_elem.get('src', '') if img_elem else ''
                
                # Adiciona aos resultados
                results.append({
                    'title': title,
                    'url': urljoin(self.BASE_URL, href),
                    'type': media_type,
                    'rating': rating if rating else 'N/A',
                    'image': urljoin(self.BASE_URL, image_url) if image_url else None,
                    'genre': genre
                })
            
            logger.info(f"Encontrados {len(results)} resultados para gênero '{genre}'")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar por gênero '{genre}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_available_genres(self, media_type: str = "movie") -> List[str]:
        """
        Retorna lista de gêneros disponíveis
        
        Args:
            media_type: Tipo de mídia ('movie', 'series', 'anime')
            
        Returns:
            Lista de nomes de gêneros
        """
        if media_type == "movie":
            return sorted(set(self.MOVIE_GENRES.keys()))
        elif media_type in ["series", "anime"]:
            return sorted(set(self.SERIES_GENRES.keys()))
        return []
    
    def get_popular(self, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        """
        Obtém lista de itens populares
        
        Args:
            media_type: Tipo de mídia ('movie', 'series', 'anime')
            limit: Número máximo de resultados
            
        Returns:
            Lista de dicionários com informações dos itens
        """
        try:
            # Define a URL baseado no tipo
            if media_type == "movie":
                url = f"{self.BASE_URL}/filmes-torrent/"
            elif media_type == "series":
                url = f"{self.BASE_URL}/series-torrent/"
            elif media_type == "anime":
                url = f"{self.BASE_URL}/animes-torrent/"
            else:
                url = self.BASE_URL
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            media_cards = soup.find_all('a', href=True, limit=limit * 2)
            
            for card in media_cards:
                href = card.get('href', '')
                
                # Verifica se é um link válido
                if not any(x in href for x in ['/filme/', '/serie/', '/anime/']):
                    continue
                
                # Extrai título
                title_elem = card.find(text=True, recursive=False)
                if not title_elem:
                    continue
                
                title = title_elem.strip()
                
                # Extrai rating
                rating = None
                rating_elem = card.find(string=re.compile(r'\d+\s*%'))
                if rating_elem:
                    rating = rating_elem.strip()
                
                # Extrai imagem
                img_elem = card.find('img')
                image_url = img_elem.get('src', '') if img_elem else ''
                
                results.append({
                    'title': title,
                    'url': urljoin(self.BASE_URL, href),
                    'type': media_type,
                    'rating': rating,
                    'image': urljoin(self.BASE_URL, image_url) if image_url else None
                })
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao obter itens populares: {e}")
            return []


# Funções auxiliares para uso direto
def search_ytsbr(query: str, media_type: str = "all", limit: int = 10) -> List[Dict]:
    """Busca por filmes, séries ou animes no YTS Brasil"""
    api = YTSBRApi()
    return api.search(query, media_type, limit)


def get_ytsbr_details(url: str) -> Optional[Dict]:
    """Obtém detalhes de um item do YTS Brasil"""
    api = YTSBRApi()
    return api.get_details(url)


def get_ytsbr_magnet(url: str) -> Optional[str]:
    """Obtém link magnet de um item do YTS Brasil"""
    api = YTSBRApi()
    return api.get_magnet_link(url)


def get_ytsbr_popular(media_type: str = "movie", limit: int = 10) -> List[Dict]:
    """Obtém lista de itens populares do YTS Brasil"""
    api = YTSBRApi()
    return api.get_popular(media_type, limit)


if __name__ == "__main__":
    # Testes
    api = YTSBRApi()
    
    print("=== Testando busca ===")
    results = api.search("peaky blinders", limit=3)
    for r in results:
        print(f"- {r['title']} ({r['type']}) - {r['url']}")
    
    if results:
        print("\n=== Testando detalhes ===")
        details = api.get_details(results[0]['url'])
        if details:
            print(f"Título: {details['title']}")
            print(f"Rating: {details['rating']}")
            print(f"Sinopse: {details['synopsis'][:100]}..." if details['synopsis'] else "Sem sinopse")
        
        print("\n=== Testando link magnet ===")
        magnet = api.get_magnet_link(results[0]['url'])
        if magnet:
            print(f"Magnet: {magnet[:80]}...")
        else:
            print("Link magnet não encontrado")
    
    print("\n=== Testando populares ===")
    popular = api.get_popular("movie", limit=5)
    for p in popular:
        print(f"- {p['title']} - {p['rating']}")
