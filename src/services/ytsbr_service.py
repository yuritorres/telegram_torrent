import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class YTSBRApi:
    """Cliente para interagir com o site YTS Brasil"""

    BASE_URL = "https://ytsbr.com"

    MOVIE_GENRES = {
        'acao': 28, 'ação': 28, 'aventura': 12, 'animacao': 16, 'animação': 16,
        'comedia': 35, 'comédia': 35, 'crime': 80, 'documentario': 99, 'documentário': 99,
        'drama': 18, 'familia': 10751, 'família': 10751, 'fantasia': 14,
        'historia': 36, 'história': 36, 'terror': 27, 'musica': 10402, 'música': 10402,
        'misterio': 9648, 'mistério': 9648, 'romance': 10749, 'ficcao': 878, 'ficção': 878,
        'sci-fi': 878, 'thriller': 53, 'guerra': 10752, 'faroeste': 37,
    }

    SERIES_GENRES = {
        'acao': 'Ação & Aventura', 'ação': 'Ação & Aventura', 'aventura': 'Ação & Aventura',
        'animacao': 'Animação', 'animação': 'Animação', 'comedia': 'Comédia', 'comédia': 'Comédia',
        'crime': 'Crime', 'documentario': 'Documentário', 'documentário': 'Documentário',
        'drama': 'Drama', 'familia': 'Família', 'família': 'Família', 'kids': 'Kids',
        'misterio': 'Mistério', 'mistério': 'Mistério', 'reality': 'Reality',
        'sci-fi': 'Sci-Fi & Fantasia', 'ficcao': 'Sci-Fi & Fantasia', 'ficção': 'Sci-Fi & Fantasia',
        'fantasia': 'Sci-Fi & Fantasia', 'guerra': 'War & Politics', 'faroeste': 'Faroeste',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    def search(self, query: str, media_type: str = "all", limit: int = 10) -> List[Dict]:
        try:
            results = []
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
                media_cards = soup.find_all('a', href=True)

                for card in media_cards:
                    href = card.get('href', '')
                    if not any(x in href for x in ['/filme/', '/serie/', '/anime/']):
                        continue
                    title_elem = card.find(text=True, recursive=False)
                    if not title_elem:
                        continue
                    title = title_elem.strip()
                    if query.lower() not in title.lower():
                        continue
                    rating = None
                    rating_elem = card.find(string=re.compile(r'\d+\s*%'))
                    if rating_elem:
                        rating = rating_elem.strip()
                    item_type = 'movie' if '/filme/' in href else ('series' if '/serie/' in href else 'anime')
                    img_elem = card.find('img')
                    image_url = img_elem.get('src', '') if img_elem else ''
                    results.append({
                        'title': title, 'url': urljoin(self.BASE_URL, href),
                        'type': item_type, 'rating': rating,
                        'image': urljoin(self.BASE_URL, image_url) if image_url else None,
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
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Título desconhecido"
            rating_elem = soup.find(string=re.compile(r'★\s*\d+\.?\d*'))
            rating = rating_elem.strip() if rating_elem else None
            year_elem = soup.find(string=re.compile(r'\b(19|20)\d{2}\b'))
            year = year_elem.strip() if year_elem else None
            duration_elem = soup.find(string=re.compile(r'\d+h\s*\d*min'))
            duration = duration_elem.strip() if duration_elem else None
            genre_elem = soup.find(string=re.compile(r'•'))
            genres = genre_elem.strip() if genre_elem else None
            synopsis = None
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 100:
                    synopsis = text
                    break
            img_elem = soup.find('img', src=re.compile(r'poster'))
            image_url = img_elem.get('src', '') if img_elem else None
            quality_info = self._extract_quality_info(soup)
            item_type = 'movie' if '/filme/' in url else ('series' if '/serie/' in url else ('anime' if '/anime/' in url else 'unknown'))

            return {
                'title': title, 'url': url, 'type': item_type, 'rating': rating,
                'year': year, 'duration': duration, 'genres': genres, 'synopsis': synopsis,
                'image': urljoin(self.BASE_URL, image_url) if image_url else None,
                'quality': quality_info,
            }
        except Exception as e:
            logger.error(f"Erro ao obter detalhes de {url}: {e}")
            return None

    def _extract_quality_info(self, soup: BeautifulSoup) -> List[Dict]:
        quality_list = []
        try:
            quality_indicators = ['IMAGEM DE CINEMA', 'QUALIDADE BAIXA', 'QUALIDADE MÉDIA', 'QUALIDADE ALTA',
                                   'HD', '4K', 'FULL HD', 'CAM', 'HDCAM', 'WEBRIP', 'BLURAY']
            all_text = soup.get_text()
            for indicator in quality_indicators:
                if indicator in all_text.upper():
                    quality_entry = {'type': indicator, 'video_audio': None, 'resolution': None,
                                     'language': None, 'size': None, 'format': None, 'codec': None}
                    va_match = re.search(r'Vídeo\s*(\d+)\s*•\s*Áudio\s*(\d+)', all_text, re.IGNORECASE)
                    if va_match:
                        quality_entry['video_audio'] = f"Vídeo {va_match.group(1)} • Áudio {va_match.group(2)}"
                    for pattern in [r'\b(4K|2160p)\b', r'\b(FULL\s*HD|1080p)\b', r'\b(HD|720p)\b', r'\b(480p)\b']:
                        res_match = re.search(pattern, all_text, re.IGNORECASE)
                        if res_match:
                            quality_entry['resolution'] = res_match.group(1)
                            break
                    lang_match = re.search(r'(Original|Dublado|Legendado)', all_text, re.IGNORECASE)
                    if lang_match:
                        quality_entry['language'] = lang_match.group(1)
                    fmt_match = re.search(r'\b(MKV|MP4|AVI)\b', all_text, re.IGNORECASE)
                    if fmt_match:
                        quality_entry['format'] = fmt_match.group(1)
                    codec_match = re.search(r'\b(H\.264|H\.265|x264|x265|HEVC)\b', all_text, re.IGNORECASE)
                    if codec_match:
                        quality_entry['codec'] = codec_match.group(1)
                    quality_list.append(quality_entry)
            if not quality_list and re.search(r'\bHD\b', all_text, re.IGNORECASE):
                quality_list.append({'type': 'HD', 'video_audio': None})
        except Exception as e:
            logger.error(f"Erro ao extrair informações de qualidade: {e}")
        return quality_list if quality_list else [{'type': 'Qualidade não especificada', 'video_audio': None}]

    def get_magnet_link(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            magnet_pattern = r'magnet:\?xt=urn:btih:[a-fA-F0-9]{40}[^\s\'"<>]*'
            magnet_matches = re.findall(magnet_pattern, html_content)
            if magnet_matches:
                magnet_link = magnet_matches[0].replace('&amp;', '&')
                logger.info(f"Link magnet encontrado: {magnet_link[:100]}...")
                return magnet_link
            soup = BeautifulSoup(response.content, 'html.parser')
            magnet_links = soup.find_all('a', href=re.compile(r'^magnet:\?'))
            if magnet_links:
                return magnet_links[0].get('href')
            logger.warning(f"Link magnet não encontrado em {url}")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter link magnet de {url}: {e}")
            return None

    def search_by_genre(self, genre: str, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        try:
            genre_lower = genre.lower()
            if media_type == "movie":
                genre_id = self.MOVIE_GENRES.get(genre_lower)
                if not genre_id:
                    return []
                url = f"{self.BASE_URL}/filmes-torrent/?genre={genre_id}"
            elif media_type == "series":
                url = f"{self.BASE_URL}/series-torrent/"
            elif media_type == "anime":
                url = f"{self.BASE_URL}/animes-torrent/"
            else:
                return []

            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            main_content = soup.find('main') or soup.find('region')
            if not main_content:
                return []
            media_links = main_content.find_all('a', href=re.compile(r'/(filme|serie|anime)/'))
            for link in media_links:
                if len(results) >= limit:
                    break
                href = link.get('href', '')
                if not href or href == '#':
                    continue
                title = None
                for text in link.find_all(string=True):
                    text_clean = text.strip()
                    if text_clean and not re.match(r'^\d+\s*%?$', text_clean) and not re.match(r'^\d{2}\s+de\s+\w+', text_clean):
                        if len(text_clean) > 3:
                            title = text_clean
                            break
                if not title:
                    continue
                rating_texts = link.find_all(string=re.compile(r'^\d+$'))
                rating = f"{rating_texts[0].strip()} %" if len(rating_texts) >= 2 else 'N/A'
                img_elem = link.find('img')
                image_url = img_elem.get('src', '') if img_elem else ''
                results.append({
                    'title': title, 'url': urljoin(self.BASE_URL, href), 'type': media_type,
                    'rating': rating, 'image': urljoin(self.BASE_URL, image_url) if image_url else None, 'genre': genre,
                })
            return results
        except Exception as e:
            logger.error(f"Erro ao buscar por gênero '{genre}': {e}")
            return []

    def get_available_genres(self, media_type: str = "movie") -> List[str]:
        if media_type == "movie":
            return sorted(set(self.MOVIE_GENRES.keys()))
        elif media_type in ["series", "anime"]:
            return sorted(set(self.SERIES_GENRES.keys()))
        return []

    def get_popular(self, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        try:
            url_map = {'movie': f"{self.BASE_URL}/filmes-torrent/", 'series': f"{self.BASE_URL}/series-torrent/",
                       'anime': f"{self.BASE_URL}/animes-torrent/"}
            url = url_map.get(media_type, self.BASE_URL)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            for card in soup.find_all('a', href=True, limit=limit * 2):
                href = card.get('href', '')
                if not any(x in href for x in ['/filme/', '/serie/', '/anime/']):
                    continue
                title_elem = card.find(text=True, recursive=False)
                if not title_elem:
                    continue
                title = title_elem.strip()
                rating = None
                rating_elem = card.find(string=re.compile(r'\d+\s*%'))
                if rating_elem:
                    rating = rating_elem.strip()
                img_elem = card.find('img')
                image_url = img_elem.get('src', '') if img_elem else ''
                results.append({
                    'title': title, 'url': urljoin(self.BASE_URL, href),
                    'type': media_type, 'rating': rating,
                    'image': urljoin(self.BASE_URL, image_url) if image_url else None,
                })
                if len(results) >= limit:
                    break
            return results
        except Exception as e:
            logger.error(f"Erro ao obter itens populares: {e}")
            return []


def search_ytsbr(query: str, media_type: str = "all", limit: int = 10) -> List[Dict]:
    return YTSBRApi().search(query, media_type, limit)


def get_ytsbr_details(url: str) -> Optional[Dict]:
    return YTSBRApi().get_details(url)


def get_ytsbr_magnet(url: str) -> Optional[str]:
    return YTSBRApi().get_magnet_link(url)


def get_ytsbr_popular(media_type: str = "movie", limit: int = 10) -> List[Dict]:
    return YTSBRApi().get_popular(media_type, limit)
