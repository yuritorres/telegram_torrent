import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)


class RedeTorrentApi:
    """Cliente para interagir com o site Rede Torrent"""

    BASE_URL = "https://redetorrent.com"

    FILMES_GENRES = {
        'acao': 'acao', 'ação': 'acao', 'animacao': 'animacao', 'animação': 'animacao',
        'aventura': 'aventura', 'bluray': 'bluray', 'classico': 'classico', 'clássico': 'classico',
        'comedia': 'comedia', 'comédia': 'comedia', 'documentario': 'documentario',
        'documentário': 'documentario', 'drama': 'drama', 'ficcao': 'ficcao', 'ficção': 'ficcao',
        'guerra': 'guerra', 'herois': 'herois', 'heróis': 'herois', 'super herois': 'herois',
        'nacional': 'nacional', 'romance': 'romance', 'suspense': 'suspense', 'terror': 'terror',
    }

    SERIES_GENRES = {
        'acao': 'acao', 'ação': 'acao', 'aventura': 'aventura', 'bluray': 'bluray',
        'classico': 'classico', 'clássico': 'classico', 'comedia': 'comedia', 'comédia': 'comedia',
        'documentario': 'documentario', 'documentário': 'documentario', 'drama': 'drama',
        'familia': 'familia', 'família': 'familia', 'ficcao': 'ficcao', 'ficção': 'ficcao',
        'herois': 'herois', 'heróis': 'herois', 'romance': 'romance', 'terror': 'terror',
    }

    DESENHOS_GENRES = {
        'acao': 'acao', 'ação': 'acao', 'anime': 'anime', 'animes': 'anime',
        'aventura': 'aventura', 'classico': 'classico', 'clássico': 'classico',
        'comedia': 'comedia', 'comédia': 'comedia', 'familia': 'familia', 'família': 'familia',
        'herois': 'herois', 'heróis': 'herois',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _parse_card(self, card_link, next_siblings) -> Optional[Dict]:
        """Extrai informações de um card de mídia da listagem."""
        try:
            href = card_link.get('href', '')
            if not href or href == '#':
                return None

            # Título vem do atributo alt da imagem ou do texto do link
            img_elem = card_link.find('img')
            title = None
            image_url = None

            if img_elem:
                alt = img_elem.get('alt', '').strip()
                # Limpa sufixos como "via Torrent"
                title = re.sub(r'\s*via\s+Torrent\s*$', '', alt, flags=re.IGNORECASE).strip()
                image_url = img_elem.get('src', '')

            if not title:
                # Tenta pelo atributo title do link
                title = card_link.get('title', '').strip()
                title = re.sub(r'\s*Torrent\s*$', '', title, flags=re.IGNORECASE).strip()

            if not title:
                return None

            # Detecta tipo pela URL do poster ou pelo texto de categoria
            item_type = 'movie'
            if image_url:
                if '_series_' in image_url or 'series' in image_url:
                    item_type = 'series'
                elif '_desenhos_' in image_url or 'desenho' in image_url:
                    item_type = 'desenho'

            # Categoria e qualidade vêm de elementos irmãos (StaticText após o card link)
            category = None
            quality = None
            rating = None
            audio_type = None

            for sibling in next_siblings:
                text = ''
                if isinstance(sibling, str):
                    text = sibling.strip()
                elif hasattr(sibling, 'get_text'):
                    text = sibling.get_text(strip=True)

                if not text:
                    continue

                if text in ('Filmes', 'Séries', 'Desenhos'):
                    category = text
                    if text == 'Séries':
                        item_type = 'series'
                    elif text == 'Desenhos':
                        item_type = 'desenho'
                    elif text == 'Filmes':
                        item_type = 'movie'
                elif '|' in text and any(q in text.upper() for q in ['1080P', '720P', 'BLURAY', 'WEB-DL', 'CAM', '4K', 'HD']):
                    quality = text.strip()
                elif re.match(r'^\d+\.?\d*$', text):
                    rating = text
                elif text in ('Dublado', 'Dual Áudio', 'Legendado'):
                    audio_type = text

            return {
                'title': title,
                'url': urljoin(self.BASE_URL, href),
                'type': item_type,
                'category': category,
                'quality': quality,
                'rating': rating,
                'audio_type': audio_type,
                'image': urljoin(self.BASE_URL, image_url) if image_url else None,
            }
        except Exception as e:
            logger.debug(f"Erro ao parsear card: {e}")
            return None

    def _parse_listing_page(self, soup: BeautifulSoup, limit: int = 10) -> List[Dict]:
        """Parseia uma página de listagem e retorna os cards de mídia."""
        results = []
        seen_urls = set()

        # Os cards são links <a> com imagens de poster
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            if len(results) >= limit:
                break

            href = link.get('href', '')
            # Filtra apenas links de conteúdo (que terminam com -download/ ou -torrent-)
            if not href or not re.search(r'redetorrent\.com/.+-(?:download|torrent)', href):
                continue

            # Ignora links de navegação, sitemap, etc.
            if '/sitemap' in href or href.endswith('.xml'):
                continue

            # Precisa ter imagem (é um card de mídia)
            img = link.find('img')
            if not img:
                continue

            # Evita duplicados
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Coleta siblings para extrair metadados
            siblings = []
            sibling = link.next_sibling
            sibling_count = 0
            while sibling and sibling_count < 10:
                siblings.append(sibling)
                sibling = sibling.next_sibling
                sibling_count += 1

            item = self._parse_card(link, siblings)
            if item:
                results.append(item)

        return results[:limit]

    def search(self, query: str, media_type: str = "all", limit: int = 10) -> List[Dict]:
        """Busca conteúdo no Rede Torrent."""
        try:
            url = f"{self.BASE_URL}/index.php"
            params = {'s': query}
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            results = self._parse_listing_page(soup, limit=limit * 2)

            # Filtra por tipo de mídia se especificado
            if media_type != "all":
                type_map = {
                    'movie': 'movie', 'filmes': 'movie',
                    'series': 'series', 'séries': 'series',
                    'desenho': 'desenho', 'desenhos': 'desenho',
                }
                target_type = type_map.get(media_type, media_type)
                results = [r for r in results if r.get('type') == target_type]

            return results[:limit]
        except Exception as e:
            logger.error(f"Erro ao buscar em redetorrent.com: {e}")
            return []

    def get_details(self, url: str) -> Optional[Dict]:
        """Obtém detalhes de um filme/série/desenho."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Título
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Título desconhecido"
            # Limpa sufixos comuns do título
            title = re.sub(r'\s*\(\d{4}\)\s*Torrent.*$', '', title, flags=re.IGNORECASE).strip()
            if not title:
                title = title_elem.get_text(strip=True) if title_elem else "Título desconhecido"

            all_text = soup.get_text()

            # Título Original
            original_title = None
            ot_match = re.search(r'Título Original\s*:\s*(.+?)(?:\n|$)', all_text)
            if ot_match:
                original_title = ot_match.group(1).strip()

            # Ano/Lançamento
            year = None
            year_match = re.search(r'Lançamento\s*:\s*(\d{4})', all_text)
            if year_match:
                year = year_match.group(1)

            # Gêneros
            genres = None
            genre_match = re.search(r'Gêneros?\s*:\s*(.+?)(?:\n|$)', all_text)
            if genre_match:
                genres = genre_match.group(1).strip()

            # Idioma
            language = None
            lang_match = re.search(r'Idioma\s*:\s*(.+?)(?:\n|$)', all_text)
            if lang_match:
                language = lang_match.group(1).strip()

            # Qualidade
            quality = None
            qual_match = re.search(r'Qualidade\s*:\s*(.+?)(?:\n|$)', all_text)
            if qual_match:
                quality = qual_match.group(1).strip()

            # Duração
            duration = None
            dur_match = re.search(r'Duração\s*:\s*(.+?)(?:\n|$)', all_text)
            if dur_match:
                duration = dur_match.group(1).strip()

            # Formato
            fmt = None
            fmt_match = re.search(r'Formato\s*:\s*(.+?)(?:\n|$)', all_text)
            if fmt_match:
                fmt = fmt_match.group(1).strip()

            # Vídeo e Áudio scores
            video_audio = None
            va_match = re.search(r'Vídeo\s*:\s*(\d+)\s*e\s*Áudio\s*:\s*(\d+)', all_text)
            if va_match:
                video_audio = f"Vídeo: {va_match.group(1)} / Áudio: {va_match.group(2)}"
            else:
                va_match2 = re.search(r'Vídeo\s*:\s*(\d+).*?Áudio\s*:\s*(\d+)', all_text, re.DOTALL)
                if va_match2:
                    video_audio = f"Vídeo: {va_match2.group(1)} / Áudio: {va_match2.group(2)}"

            # Legendas
            subtitles = None
            sub_match = re.search(r'Legendas?\s*:\s*(.+?)(?:\n|$)', all_text)
            if sub_match:
                subtitles = sub_match.group(1).strip()

            # Nota do IMDB
            imdb_rating = None
            imdb_match = re.search(r'Nota do Imdb\s*:\s*(\d+\.?\d*)', all_text)
            if imdb_match:
                imdb_rating = imdb_match.group(1)

            # Tamanho
            size = None
            size_match = re.search(r'Tamanho\s*:\s*(.+?)(?:\n|$)', all_text)
            if size_match:
                size = size_match.group(1).strip()

            # Sinopse
            synopsis = None
            syn_match = re.search(r'Sinopse\s*:\s*(.+?)(?:Trailer|$)', all_text, re.DOTALL)
            if syn_match:
                synopsis = syn_match.group(1).strip()

            # Imagem/Poster
            img_elem = soup.find('img', src=re.compile(r'/poster/'))
            image_url = img_elem.get('src', '') if img_elem else None

            # Tipo
            item_type = 'movie'
            if image_url:
                if '_series_' in image_url:
                    item_type = 'series'
                elif '_desenhos_' in image_url:
                    item_type = 'desenho'
            # Também verifica URL
            if 'temporada' in url.lower():
                item_type = 'series'

            # Links magnet
            magnets = self._extract_magnet_links(soup, response.text)

            return {
                'title': title,
                'original_title': original_title,
                'url': url,
                'type': item_type,
                'year': year,
                'genres': genres,
                'language': language,
                'quality': quality,
                'duration': duration,
                'format': fmt,
                'video_audio': video_audio,
                'subtitles': subtitles,
                'imdb_rating': imdb_rating,
                'size': size,
                'synopsis': synopsis,
                'image': urljoin(self.BASE_URL, image_url) if image_url else None,
                'magnets': magnets,
            }
        except Exception as e:
            logger.error(f"Erro ao obter detalhes de {url}: {e}")
            return None

    def _extract_magnet_links(self, soup: BeautifulSoup, html_text: str) -> List[Dict]:
        """Extrai todos os links magnet da página com seus labels."""
        magnets = []
        seen = set()

        # Primeiro tenta links <a> com href magnet
        magnet_anchors = soup.find_all('a', href=re.compile(r'^magnet:\?'))
        for anchor in magnet_anchors:
            href = anchor.get('href', '')
            if href and href not in seen:
                seen.add(href)
                label = anchor.get_text(strip=True) or 'DOWNLOAD'
                # Tenta pegar o texto do bloco acima do link (descrição da versão)
                prev = anchor.find_previous(string=re.compile(r'(DUBLADO|LEGENDADO|DUAL|1080P|720P|4K)', re.IGNORECASE))
                version_label = prev.strip() if prev else label
                magnets.append({
                    'url': href.replace('&amp;', '&'),
                    'label': version_label,
                })

        # Fallback: busca no HTML bruto
        if not magnets:
            magnet_pattern = r'magnet:\?xt=urn:btih:[a-fA-F0-9]{40}[^\s\'"<>]*'
            raw_matches = re.findall(magnet_pattern, html_text)
            for m in raw_matches:
                clean = m.replace('&amp;', '&')
                if clean not in seen:
                    seen.add(clean)
                    magnets.append({
                        'url': clean,
                        'label': 'DOWNLOAD',
                    })

        return magnets

    def get_magnet_link(self, url: str) -> Optional[str]:
        """Obtém o primeiro link magnet de uma página."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            magnets = self._extract_magnet_links(soup, response.text)
            if magnets:
                magnet_link = magnets[0]['url']
                logger.info(f"Link magnet encontrado: {magnet_link[:100]}...")
                return magnet_link

            logger.warning(f"Link magnet não encontrado em {url}")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter link magnet de {url}: {e}")
            return None

    def get_all_magnets(self, url: str) -> List[Dict]:
        """Obtém todos os links magnet de uma página (múltiplas versões)."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_magnet_links(soup, response.text)
        except Exception as e:
            logger.error(f"Erro ao obter links magnet de {url}: {e}")
            return []

    def get_popular(self, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        """Obtém os itens populares/recentes por tipo de mídia."""
        try:
            url_map = {
                'movie': f"{self.BASE_URL}/filmes/",
                'series': f"{self.BASE_URL}/series/",
                'desenho': f"{self.BASE_URL}/desenhos/",
                'dublado': f"{self.BASE_URL}/dublados/",
                'legendado': f"{self.BASE_URL}/legendados/",
                'lancamento': f"{self.BASE_URL}/lancamentos/",
            }
            url = url_map.get(media_type, f"{self.BASE_URL}/")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_listing_page(soup, limit)
        except Exception as e:
            logger.error(f"Erro ao obter itens populares: {e}")
            return []

    def search_by_genre(self, genre: str, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        """Busca por gênero."""
        try:
            genre_lower = genre.lower()

            if media_type == "movie":
                genre_slug = self.FILMES_GENRES.get(genre_lower)
                if not genre_slug:
                    return []
                url = f"{self.BASE_URL}/filmes/{genre_slug}/"
            elif media_type == "series":
                genre_slug = self.SERIES_GENRES.get(genre_lower)
                if not genre_slug:
                    return []
                url = f"{self.BASE_URL}/series/{genre_slug}/"
            elif media_type == "desenho":
                genre_slug = self.DESENHOS_GENRES.get(genre_lower)
                if not genre_slug:
                    return []
                url = f"{self.BASE_URL}/desenhos/{genre_slug}/"
            else:
                return []

            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            results = self._parse_listing_page(soup, limit)

            # Adiciona info de gênero nos resultados
            for r in results:
                r['genre'] = genre

            return results
        except Exception as e:
            logger.error(f"Erro ao buscar por gênero '{genre}': {e}")
            return []

    def get_available_genres(self, media_type: str = "movie") -> List[str]:
        """Retorna os gêneros disponíveis para um tipo de mídia."""
        if media_type == "movie":
            return sorted(set(self.FILMES_GENRES.keys()))
        elif media_type == "series":
            return sorted(set(self.SERIES_GENRES.keys()))
        elif media_type == "desenho":
            return sorted(set(self.DESENHOS_GENRES.keys()))
        return []

    def get_by_quality(self, quality: str, media_type: str = "movie", limit: int = 10) -> List[Dict]:
        """Busca por qualidade (1080p, 720p, bluray, hd)."""
        try:
            quality_lower = quality.lower().replace(' ', '')
            valid_qualities = {
                'movie': ['1080p', '720p', '4k', 'bluray', 'hd'],
                'series': ['1080p', '720p', 'bluray', 'hd'],
            }
            type_path = {
                'movie': 'filmes',
                'series': 'series',
            }

            if media_type not in valid_qualities or quality_lower not in valid_qualities[media_type]:
                return []

            path = type_path.get(media_type, 'filmes')
            url = f"{self.BASE_URL}/{path}/{quality_lower}/"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_listing_page(soup, limit)
        except Exception as e:
            logger.error(f"Erro ao buscar por qualidade '{quality}': {e}")
            return []


def search_redetorrent(query: str, media_type: str = "all", limit: int = 10) -> List[Dict]:
    return RedeTorrentApi().search(query, media_type, limit)


def get_redetorrent_details(url: str) -> Optional[Dict]:
    return RedeTorrentApi().get_details(url)


def get_redetorrent_magnet(url: str) -> Optional[str]:
    return RedeTorrentApi().get_magnet_link(url)


def get_redetorrent_popular(media_type: str = "movie", limit: int = 10) -> List[Dict]:
    return RedeTorrentApi().get_popular(media_type, limit)
