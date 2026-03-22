"""
Testes para o módulo magnet_parser.
"""
import pytest
from src.utils.magnet_parser import (
    MagnetLink,
    extract_magnet_links,
    validate_magnet_link,
    format_magnet_info
)


def test_magnet_link_parsing():
    """Testa parsing de magnet link completo."""
    magnet = "magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb&dn=Detetive.Alex.Cross.S02E01-02-03.WEB-DL.1080p.x264.DUAL.5.1-SF&xl=5079773278"
    
    magnet_obj = MagnetLink(magnet)
    
    assert magnet_obj.is_valid()
    assert magnet_obj.info_hash == "FAECD4F63FC45B2ADD695413F828ECB3148D64FB"
    assert magnet_obj.display_name == "Detetive.Alex.Cross.S02E01-02-03.WEB-DL.1080p.x264.DUAL.5.1-SF"
    assert magnet_obj.size == 5079773278
    assert "4.73 GB" in magnet_obj.get_size_formatted()


def test_magnet_link_without_name():
    """Testa magnet link sem nome de exibição."""
    magnet = "magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb"
    
    magnet_obj = MagnetLink(magnet)
    
    assert magnet_obj.is_valid()
    assert magnet_obj.info_hash == "FAECD4F63FC45B2ADD695413F828ECB3148D64FB"
    assert magnet_obj.display_name is None
    assert "Torrent FAECD4F6..." in magnet_obj.get_display_name()


def test_magnet_link_with_trackers():
    """Testa magnet link com trackers."""
    magnet = "magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb&tr=udp://tracker.example.com:80&tr=http://tracker2.example.com:8080"
    
    magnet_obj = MagnetLink(magnet)
    
    assert magnet_obj.is_valid()
    assert len(magnet_obj.trackers) == 2
    assert "udp://tracker.example.com:80" in magnet_obj.trackers


def test_extract_multiple_magnets():
    """Testa extração de múltiplos magnet links de um texto."""
    text = """
    Aqui estão alguns torrents:
    magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb&dn=Torrent1
    E outro aqui:
    magnet:?xt=urn:btih:1234567890abcdef1234567890abcdef12345678&dn=Torrent2
    """
    
    magnets = extract_magnet_links(text)
    
    assert len(magnets) == 2
    assert magnets[0].display_name == "Torrent1"
    assert magnets[1].display_name == "Torrent2"


def test_validate_magnet_link():
    """Testa validação de magnet links."""
    # Link válido
    valid_magnet = "magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb"
    is_valid, error = validate_magnet_link(valid_magnet)
    assert is_valid
    assert error is None
    
    # Link inválido - sem magnet:
    invalid_magnet = "http://example.com/torrent"
    is_valid, error = validate_magnet_link(invalid_magnet)
    assert not is_valid
    assert "magnet:" in error
    
    # Link vazio
    is_valid, error = validate_magnet_link("")
    assert not is_valid
    assert "vazio" in error.lower()


def test_format_magnet_info():
    """Testa formatação de informações do magnet."""
    magnet = "magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb&dn=Test.Torrent&xl=1073741824"
    magnet_obj = MagnetLink(magnet)
    
    formatted = format_magnet_info(magnet_obj)
    
    assert "Test.Torrent" in formatted
    assert "1.00 GB" in formatted
    assert "FAECD4F6" in formatted


def test_magnet_to_dict():
    """Testa conversão de magnet para dicionário."""
    magnet = "magnet:?xt=urn:btih:faecd4f63fc45b2add695413f828ecb3148d64fb&dn=Test&xl=1024"
    magnet_obj = MagnetLink(magnet)
    
    data = magnet_obj.to_dict()
    
    assert data['info_hash'] == "FAECD4F63FC45B2ADD695413F828ECB3148D64FB"
    assert data['display_name'] == "Test"
    assert data['size'] == 1024
    assert data['is_valid'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
