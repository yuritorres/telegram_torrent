"""
Módulo para parsing e validação de magnet links.
Suporta extração de informações e validação de links magnéticos.
"""
import re
import urllib.parse
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class MagnetLink:
    """Representa um magnet link com suas propriedades extraídas."""
    
    def __init__(self, raw_link: str):
        self.raw_link = raw_link
        self.info_hash: Optional[str] = None
        self.display_name: Optional[str] = None
        self.size: Optional[int] = None
        self.trackers: List[str] = []
        self.exact_topic: Optional[str] = None
        
        self._parse()
    
    def _parse(self):
        """Extrai informações do magnet link."""
        try:
            # Extrair info hash (btih)
            btih_match = re.search(r'xt=urn:btih:([0-9a-fA-F]{40}|[0-9a-zA-Z]{32})', self.raw_link, re.IGNORECASE)
            if btih_match:
                self.info_hash = btih_match.group(1).upper()
                self.exact_topic = f"urn:btih:{self.info_hash}"
            
            # Parse URL parameters
            parsed = urllib.parse.urlparse(self.raw_link)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Extrair display name (dn)
            if 'dn' in params:
                self.display_name = urllib.parse.unquote(params['dn'][0])
            
            # Extrair tamanho exato (xl)
            if 'xl' in params:
                try:
                    self.size = int(params['xl'][0])
                except (ValueError, IndexError):
                    pass
            
            # Extrair trackers (tr)
            if 'tr' in params:
                self.trackers = [urllib.parse.unquote(tr) for tr in params['tr']]
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse do magnet link: {e}")
    
    def is_valid(self) -> bool:
        """Verifica se o magnet link é válido."""
        return self.info_hash is not None and len(self.info_hash) in [32, 40]
    
    def get_display_name(self) -> str:
        """Retorna o nome de exibição ou um nome padrão."""
        if self.display_name:
            return self.display_name
        if self.info_hash:
            return f"Torrent {self.info_hash[:8]}..."
        return "Torrent desconhecido"
    
    def get_size_formatted(self) -> Optional[str]:
        """Retorna o tamanho formatado em unidades legíveis."""
        if not self.size:
            return None
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(self.size)
        unit_index = 0
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    
    def to_dict(self) -> Dict:
        """Retorna as informações do magnet link como dicionário."""
        return {
            'raw_link': self.raw_link,
            'info_hash': self.info_hash,
            'display_name': self.display_name,
            'size': self.size,
            'size_formatted': self.get_size_formatted(),
            'trackers': self.trackers,
            'exact_topic': self.exact_topic,
            'is_valid': self.is_valid()
        }
    
    def __str__(self) -> str:
        """Representação em string do magnet link."""
        parts = [f"📎 {self.get_display_name()}"]
        
        if self.size:
            parts.append(f"💾 Tamanho: {self.get_size_formatted()}")
        
        if self.info_hash:
            parts.append(f"🔑 Hash: {self.info_hash[:16]}...")
        
        if self.trackers:
            parts.append(f"🌐 Trackers: {len(self.trackers)}")
        
        return "\n".join(parts)


def extract_magnet_links(text: str) -> List[MagnetLink]:
    """
    Extrai todos os magnet links de um texto.
    
    Suporta:
    - Info hash de 40 caracteres (SHA-1)
    - Info hash de 32 caracteres (Base32)
    - Múltiplos parâmetros (dn, xl, tr, etc.)
    
    Args:
        text: Texto contendo possíveis magnet links
        
    Returns:
        Lista de objetos MagnetLink encontrados
    """
    # Regex melhorado para capturar magnet links completos
    # Suporta info hash de 40 (hex) ou 32 (base32) caracteres
    magnet_pattern = r'magnet:\?[^\s<>"]+(?:xt=urn:btih:[0-9a-fA-F]{40}|xt=urn:btih:[0-9a-zA-Z]{32})[^\s<>"]*'
    
    matches = re.findall(magnet_pattern, text, re.IGNORECASE)
    
    magnet_links = []
    for match in matches:
        try:
            magnet = MagnetLink(match)
            if magnet.is_valid():
                magnet_links.append(magnet)
                logger.info(f"Magnet link válido encontrado: {magnet.get_display_name()}")
            else:
                logger.warning(f"Magnet link inválido ignorado: {match[:50]}...")
        except Exception as e:
            logger.error(f"Erro ao processar magnet link: {e}")
    
    return magnet_links


def validate_magnet_link(magnet_link: str) -> tuple[bool, Optional[str]]:
    """
    Valida um magnet link e retorna status e mensagem de erro.
    
    Args:
        magnet_link: String do magnet link a validar
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if not magnet_link or not isinstance(magnet_link, str):
        return False, "Link magnético vazio ou inválido"
    
    if not magnet_link.lower().startswith('magnet:'):
        return False, "Link deve começar com 'magnet:'"
    
    try:
        magnet = MagnetLink(magnet_link)
        
        if not magnet.is_valid():
            return False, "Info hash inválido ou ausente"
        
        return True, None
        
    except Exception as e:
        return False, f"Erro ao validar link: {str(e)}"


def format_magnet_info(magnet: MagnetLink, include_trackers: bool = False) -> str:
    """
    Formata as informações do magnet link para exibição.
    
    Args:
        magnet: Objeto MagnetLink
        include_trackers: Se deve incluir lista de trackers
        
    Returns:
        String formatada com informações do magnet
    """
    lines = [
        "📎 <b>Informações do Torrent:</b>\n",
        f"📝 <b>Nome:</b> {magnet.get_display_name()}"
    ]
    
    if magnet.size:
        lines.append(f"💾 <b>Tamanho:</b> {magnet.get_size_formatted()}")
    
    if magnet.info_hash:
        lines.append(f"🔑 <b>Hash:</b> <code>{magnet.info_hash[:16]}...</code>")
    
    if magnet.trackers:
        lines.append(f"🌐 <b>Trackers:</b> {len(magnet.trackers)}")
        
        if include_trackers and len(magnet.trackers) <= 5:
            lines.append("\n<b>Lista de Trackers:</b>")
            for i, tracker in enumerate(magnet.trackers[:5], 1):
                tracker_short = tracker[:50] + "..." if len(tracker) > 50 else tracker
                lines.append(f"  {i}. {tracker_short}")
    
    return "\n".join(lines)
