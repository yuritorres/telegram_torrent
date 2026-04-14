"""
Streaming API REST

API para controle e monitoramento do GoStream,
similar à GoStorm Web API do GoStream (porta 8090).
"""

import json
import logging
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify
from threading import Thread, Event

logger = logging.getLogger(__name__)


class StreamingAPI:
    """API REST para controle do streaming"""
    
    def __init__(self, bt_engine, native_bridge, cache, fuse_manager, config):
        """
        Inicializa a API
        
        Args:
            bt_engine: Instância do BTEngine
            native_bridge: Instância do NativeBridge
            cache: Instância do ReadAheadCache
            fuse_manager: Instância do FUSEManager
            config: GoStreamConfig
        """
        self.bt_engine = bt_engine
        self.native_bridge = native_bridge
        self.cache = cache
        self.fuse_manager = fuse_manager
        self.config = config
        
        self.app = Flask(__name__)
        self._setup_routes()
        
        self._api_thread: Optional[Thread] = None
        self._shutdown_event = Event()
    
    def _setup_routes(self):
        """Configura rotas da API"""
        
        # === Torrent Management ===
        
        @self.app.route('/api/torrents', methods=['GET'])
        def list_torrents():
            """Lista todos os torrents"""
            torrents = self.bt_engine.list_torrents()
            return jsonify({
                'success': True,
                'torrents': [
                    {
                        'info_hash': t.info_hash,
                        'name': t.name,
                        'total_size': t.total_size,
                        'progress': t.progress,
                        'state': t.state.value,
                        'download_rate': t.download_rate,
                        'upload_rate': t.upload_rate,
                        'num_peers': t.num_peers,
                        'num_seeds': t.num_seeds,
                        'is_priority': t.is_priority,
                    }
                    for t in torrents
                ]
            })
        
        @self.app.route('/api/torrents/<info_hash>', methods=['GET'])
        def get_torrent(info_hash: str):
            """Obtém detalhes de um torrent"""
            info = self.bt_engine.get_torrent_info(info_hash)
            if not info:
                return jsonify({'success': False, 'error': 'Torrent not found'}), 404
            
            return jsonify({
                'success': True,
                'torrent': {
                    'info_hash': info.info_hash,
                    'name': info.name,
                    'total_size': info.total_size,
                    'num_pieces': info.num_pieces,
                    'piece_length': info.piece_length,
                    'progress': info.progress,
                    'state': info.state.value,
                    'download_rate': info.download_rate,
                    'upload_rate': info.upload_rate,
                    'num_peers': info.num_peers,
                    'num_seeds': info.num_seeds,
                    'files': info.files,
                    'is_priority': info.is_priority,
                }
            })
        
        @self.app.route('/api/torrents/<info_hash>/files', methods=['GET'])
        def get_torrent_files(info_hash: str):
            """Retorna lista de arquivos de um torrent"""
            info = self.bt_engine.get_torrent_info(info_hash)
            
            if not info:
                return jsonify({'success': False, 'error': 'Torrent not found'}), 404
            
            # Retorna lista de arquivos
            files = info.files if info.files else []
            
            return jsonify({
                'success': True,
                'info_hash': info_hash,
                'files': files,
                'total_size': info.total_size,
                'has_metadata': len(files) > 0
            })
        
        @self.app.route('/api/torrents/add', methods=['POST'])
        def add_torrent():
            """Adiciona um torrent via magnet link"""
            data = request.get_json()
            
            if not data or 'magnet' not in data:
                return jsonify({'success': False, 'error': 'Missing magnet link'}), 400
            
            magnet = data['magnet']
            save_path = data.get('save_path')
            
            info_hash = self.bt_engine.add_torrent(magnet, save_path)
            
            if info_hash:
                return jsonify({
                    'success': True,
                    'info_hash': info_hash,
                    'message': 'Torrent added successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to add torrent'}), 500
        
        @self.app.route('/api/torrents/<info_hash>/remove', methods=['POST'])
        def remove_torrent(info_hash: str):
            """Remove um torrent"""
            data = request.get_json() or {}
            delete_files = data.get('delete_files', False)
            
            success = self.bt_engine.remove_torrent(info_hash, delete_files)
            
            if success:
                # Remove do cache também
                self.cache.remove_torrent(info_hash)
                return jsonify({'success': True, 'message': 'Torrent removed'})
            else:
                return jsonify({'success': False, 'error': 'Torrent not found'}), 404
        
        @self.app.route('/api/torrents/<info_hash>/priority', methods=['POST'])
        def set_priority(info_hash: str):
            """Ativa/desativa modo prioridade"""
            data = request.get_json() or {}
            enabled = data.get('enabled', True)
            
            self.bt_engine.set_priority_mode(info_hash, enabled)
            
            return jsonify({
                'success': True,
                'info_hash': info_hash,
                'priority_mode': enabled
            })
        
        # === Stream Handles ===
        
        @self.app.route('/api/streams', methods=['GET'])
        def list_streams():
            """Lista streams ativos"""
            handles = self.native_bridge.list_handles()
            return jsonify({
                'success': True,
                'streams': handles
            })
        
        @self.app.route('/api/streams/<handle_id>/stats', methods=['GET'])
        def get_stream_stats(handle_id: str):
            """Obtém estatísticas de um stream"""
            stats = self.native_bridge.get_stats(handle_id)
            if stats:
                return jsonify({'success': True, 'stats': stats})
            else:
                return jsonify({'success': False, 'error': 'Stream not found'}), 404
        
        # === Cache ===
        
        @self.app.route('/api/cache/stats', methods=['GET'])
        def get_cache_stats():
            """Obtém estatísticas do cache"""
            stats = self.cache.get_stats()
            return jsonify({'success': True, 'stats': stats})
        
        @self.app.route('/api/cache/clear', methods=['POST'])
        def clear_cache():
            """Limpa o cache"""
            self.cache.clear()
            return jsonify({'success': True, 'message': 'Cache cleared'})
        
        # === Session ===
        
        @self.app.route('/api/session/stats', methods=['GET'])
        def get_session_stats():
            """Obtém estatísticas da sessão BitTorrent"""
            stats = self.bt_engine.get_session_stats()
            return jsonify({'success': True, 'stats': stats})
        
        # === Config ===
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Obtém configurações atuais"""
            return jsonify({
                'success': True,
                'config': self.config.to_dict()
            })
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Atualiza configurações (algumas requerem restart)"""
            data = request.get_json()
            
            # Atualiza configurações que não requerem restart
            if 'master_concurrency_limit' in data:
                self.config.master_concurrency_limit = int(data['master_concurrency_limit'])
            
            return jsonify({
                'success': True,
                'message': 'Config updated (some changes may require restart)',
                'config': self.config.to_dict()
            })
        
        # === Health ===
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'success': True,
                'status': 'healthy',
                'timestamp': __import__('time').time(),
                'components': {
                    'bt_engine': self.bt_engine.session is not None,
                    'fuse': self.fuse_manager is not None,
                    'cache': True,
                }
            })
        
        # === Webhook for Jellyfin/Plex ===
        
        @self.app.route('/webhook/media', methods=['POST'])
        def media_webhook():
            """
            Webhook para notificações de media player (Jellyfin/Plex)
            
            Ativa Priority Mode quando um arquivo começa a ser reproduzido.
            """
            data = request.get_json() or {}
            
            # Extrai info_hash do path ou do evento
            event = data.get('event', '')
            path = data.get('path', '')
            
            # Tenta extrair info_hash do path
            info_hash = None
            if '/mnt/gostream/' in path or self.config.fuse_mount_path in path:
                # Extrai do path do arquivo montado
                parts = path.split('/')
                if len(parts) >= 3:
                    # Procura no bt_engine
                    torrents = self.bt_engine.list_torrents()
                    for t in torrents:
                        if t.name in path:
                            info_hash = t.info_hash
                            break
            
            if info_hash:
                if event in ('media.play', 'media.resume'):
                    self.bt_engine.set_priority_mode(info_hash, True)
                    return jsonify({
                        'success': True,
                        'action': 'priority_enabled',
                        'info_hash': info_hash
                    })
                elif event in ('media.stop', 'media.pause', 'media.scrobble'):
                    self.bt_engine.set_priority_mode(info_hash, False)
                    return jsonify({
                        'success': True,
                        'action': 'priority_disabled',
                        'info_hash': info_hash
                    })
            
            return jsonify({
                'success': True,
                'action': 'no_action',
                'message': 'No matching torrent found'
            })
    
    def start(self) -> bool:
        """Inicia a API REST"""
        try:
            self._api_thread = Thread(
                target=self._run_api,
                daemon=True
            )
            self._api_thread.start()
            
            logger.info(f"Streaming API iniciada em {self.config.api_host}:{self.config.api_port}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar API: {e}")
            return False
    
    def _run_api(self):
        """Thread que executa a API"""
        try:
            self.app.run(
                host=self.config.api_host,
                port=self.config.api_port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Erro na API: {e}")
    
    def stop(self):
        """Para a API"""
        self._shutdown_event.set()
        
        if self._api_thread:
            self._api_thread.join(timeout=5)
        
        logger.info("Streaming API parada")


def create_api_app(bt_engine, native_bridge, cache, fuse_manager, config):
    """
    Cria e inicia a API REST
    
    Returns:
        Instância da StreamingAPI
    """
    api = StreamingAPI(bt_engine, native_bridge, cache, fuse_manager, config)
    return api
