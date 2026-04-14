#!/usr/bin/env python3
"""
GoStream Python - Exemplo de Uso Standalone

Este script demonstra como usar o GoStream independentemente
do bot Telegram para streaming de torrents.

Usage:
    python gostream_example.py <magnet_link>

Exemplo:
    python gostream_example.py "magnet:?xt=urn:btih:..."
"""

import sys
import time
import signal
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa GoStream
try:
    from src.integrations.gostream import create_gostream, GoStreamConfig
except ImportError as e:
    print(f"Erro ao importar GoStream: {e}")
    print("Certifique-se de estar no diretório raiz do projeto.")
    sys.exit(1)


class GoStreamStandalone:
    """Wrapper standalone para uso simplificado do GoStream"""
    
    def __init__(self):
        self.manager = None
        self._shutdown = False
        
        # Configura signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de término"""
        logger.info("Sinal de término recebido, encerrando...")
        self._shutdown = True
        if self.manager:
            self.manager.stop()
    
    def start(self, mount_path: str = '/mnt/gostream', 
              cache_mb: int = 512,
              api_port: int = 8090) -> bool:
        """
        Inicializa e inicia o GoStream
        
        Args:
            mount_path: Caminho de montagem FUSE
            cache_mb: Tamanho do cache em RAM (MB)
            api_port: Porta da API REST
            
        Returns:
            True se sucesso
        """
        # Cria configuração
        config = GoStreamConfig(
            fuse_mount_path=mount_path,
            cache_dir='./gostream_cache',
            state_dir='./gostream_state',
            read_ahead_budget_mb=cache_mb,
            num_cache_shards=32,
            api_port=api_port,
            api_enabled=True,
        )
        
        # Cria manager
        self.manager = create_gostream(config)
        
        # Inicializa
        logger.info("Inicializando GoStream...")
        if not self.manager.initialize():
            logger.error("Falha ao inicializar GoStream")
            return False
        
        # Inicia serviços
        logger.info("Iniciando serviços...")
        if not self.manager.start():
            logger.error("Falha ao iniciar serviços")
            return False
        
        logger.info("✅ GoStream operacional!")
        logger.info(f"   📁 FUSE Mount: {mount_path}")
        logger.info(f"   🌐 API REST: http://localhost:{api_port}")
        
        return True
    
    def add_torrent(self, magnet_link: str, wait_metadata: bool = True) -> str:
        """
        Adiciona um torrent via magnet link
        
        Args:
            magnet_link: Link magnet do torrent
            wait_metadata: Aguarda obter metadata antes de retornar
            
        Returns:
            info_hash do torrent
        """
        logger.info(f"Adicionando torrent: {magnet_link[:60]}...")
        
        info_hash = self.manager.add_torrent(magnet_link)
        
        if not info_hash:
            raise RuntimeError("Falha ao adicionar torrent")
        
        logger.info(f"Torrent adicionado: {info_hash}")
        
        if wait_metadata:
            logger.info("Aguardando metadata...")
            timeout = 30
            start = time.time()
            
            while time.time() - start < timeout:
                info = self.manager.bt_engine.get_torrent_info(info_hash)
                if info and info.name:
                    logger.info(f"Metadata recebida: {info.name}")
                    logger.info(f"Tamanho: {info.total_size / 1024 / 1024:.1f} MB")
                    logger.info(f"Peças: {info.num_pieces}")
                    break
                time.sleep(0.5)
        
        # Atualiza FUSE
        if self.manager.fuse_manager:
            self.manager.fuse_manager.refresh()
        
        return info_hash
    
    def get_streaming_path(self, info_hash: str) -> str:
        """
        Retorna o caminho FUSE para streaming
        
        Args:
            info_hash: Hash do torrent
            
        Returns:
            Caminho completo para o arquivo
        """
        info = self.manager.bt_engine.get_torrent_info(info_hash)
        if not info:
            raise ValueError(f"Torrent não encontrado: {info_hash}")
        
        # Monta caminho
        mount_path = self.manager.config.fuse_mount_path
        safe_name = self._sanitize_filename(info.name)
        
        # Pega primeiro arquivo de vídeo
        for file_info in info.files:
            path = file_info['path']
            if any(path.endswith(ext) for ext in ['.mkv', '.mp4', '.avi', '.mov']):
                file_name = Path(path).name
                full_path = f"{mount_path}/{safe_name}/{self._sanitize_filename(file_name)}"
                return full_path
        
        # Fallback: primeiro arquivo
        if info.files:
            file_name = Path(info.files[0]['path']).name
            return f"{mount_path}/{safe_name}/{self._sanitize_filename(file_name)}"
        
        raise ValueError("Nenhum arquivo encontrado no torrent")
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitiza nome de arquivo"""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        return name[:255]
    
    def list_files(self, info_hash: str) -> list:
        """Lista arquivos disponíveis no torrent"""
        info = self.manager.bt_engine.get_torrent_info(info_hash)
        if not info:
            return []
        
        return [
            {
                'path': f['path'],
                'size': f['size'],
                'size_mb': f['size'] / 1024 / 1024
            }
            for f in info.files
        ]
    
    def monitor(self, info_hash: str, interval: int = 5):
        """
        Monitora progresso do torrent
        
        Args:
            info_hash: Hash do torrent
            interval: Intervalo de atualização (segundos)
        """
        logger.info(f"Monitorando torrent {info_hash[:8]}...")
        logger.info("Pressione Ctrl+C para parar")
        
        try:
            while not self._shutdown:
                info = self.manager.bt_engine.get_torrent_info(info_hash)
                if not info:
                    logger.warning("Torrent não encontrado")
                    break
                
                progress = info.progress * 100
                down_speed = info.download_rate / 1024  # KB/s
                peers = info.num_peers
                
                logger.info(
                    f"Progresso: {progress:.1f}% | "
                    f"Download: {down_speed:.1f} KB/s | "
                    f"Peers: {peers} | "
                    f"Estado: {info.state.value}"
                )
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoramento interrompido")
    
    def stop(self):
        """Para o GoStream"""
        if self.manager:
            self.manager.stop()
        logger.info("GoStream encerrado")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python gostream_example.py <magnet_link>")
        print("\nExemplo:")
        print('  python gostream_example.py "magnet:?xt=urn:btih:..."')
        sys.exit(1)
    
    magnet_link = sys.argv[1]
    
    # Cria instância
    gostream = GoStreamStandalone()
    
    try:
        # Inicia
        if not gostream.start():
            sys.exit(1)
        
        # Adiciona torrent
        info_hash = gostream.add_torrent(magnet_link)
        
        # Lista arquivos
        files = gostream.list_files(info_hash)
        logger.info(f"Arquivos no torrent:")
        for f in files:
            logger.info(f"  - {f['path']} ({f['size_mb']:.1f} MB)")
        
        # Obtém caminho para streaming
        stream_path = gostream.get_streaming_path(info_hash)
        logger.info(f"\n🎬 Caminho para streaming:")
        logger.info(f"   {stream_path}")
        logger.info(f"\n   Você pode abrir este arquivo em qualquer player!")
        
        if gostream.manager.fuse_manager:
            logger.info(f"\n   Ou navegue em: {gostream.manager.config.fuse_mount_path}")
        
        # Monitora progresso
        logger.info("\n" + "="*50)
        gostream.monitor(info_hash)
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        raise
    finally:
        gostream.stop()


if __name__ == "__main__":
    main()
