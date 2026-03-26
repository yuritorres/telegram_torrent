import time
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Set

logger = logging.getLogger(__name__)


class JellyfinNotifier:
    """Monitora o Jellyfin e envia notificações quando novos conteúdos são adicionados."""

    def __init__(self, jellyfin_manager, interval: int = 1800, state_file: str = "jellyfin_notifier_state.json"):
        self.jellyfin_manager = jellyfin_manager
        self.interval = interval
        self.state_file = state_file
        self.known_items: Dict[str, Set[str]] = {}  # {url: set(item_ids)}
        self.last_check_time: Optional[float] = None
        self.enabled = True
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # Suporta formato antigo (set) e novo (dict)
                    known_items_data = state.get('known_items', [])
                    if isinstance(known_items_data, list):
                        # Formato antigo: migra para o primeiro servidor
                        if self.jellyfin_manager.clients:
                            first_url = self.jellyfin_manager.clients[0].url
                            self.known_items = {first_url: set(known_items_data)}
                        else:
                            self.known_items = {}
                    elif isinstance(known_items_data, dict):
                        # Formato novo: dict de {url: [item_ids]}
                        self.known_items = {url: set(items) for url, items in known_items_data.items()}
                    else:
                        self.known_items = {}
                    
                    self.last_check_time = state.get('last_check_time')
                    total_items = sum(len(items) for items in self.known_items.values())
                    logger.info(f"Estado carregado: {total_items} itens conhecidos em {len(self.known_items)} servidor(es)")
        except Exception as e:
            logger.error(f"Erro ao carregar estado: {e}")
            self.known_items = {}
            self.last_check_time = None

    def _save_state(self):
        try:
            state = {
                'known_items': {url: list(items) for url, items in self.known_items.items()},
                'last_check_time': self.last_check_time,
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar estado: {e}")

    def _format_item_notification(self, item: Dict) -> str:
        name = item.get('Name', 'Sem título')
        item_type = item.get('Type', 'Desconhecido')
        year = item.get('ProductionYear', '')
        jellyfin_url = item.get('_jellyfin_url', '')
        
        type_icons = {
            'Movie': '🎬', 'Series': '📺', 'Season': '📺',
            'Episode': '📺', 'Audio': '🎵', 'MusicAlbum': '💿', 'Book': '📚',
        }
        icon = type_icons.get(item_type, '🎁')
        msg_parts = [f"{icon} <b>Novo conteúdo adicionado!</b>\n"]
        msg_parts.append(f"<b>{name}</b>")
        if year:
            msg_parts.append(f" ({year})")
        msg_parts.append(f"\n📂 Tipo: {item_type}")
        
        # Adiciona informação do servidor se houver múltiplas contas
        if self.jellyfin_manager.multi_account_enabled and jellyfin_url:
            msg_parts.append(f"\n🌐 Servidor: {jellyfin_url}")
        
        genres = item.get('Genres', [])
        if genres:
            msg_parts.append(f"\n🎭 Gêneros: {', '.join(genres[:3])}")
        rating = item.get('CommunityRating')
        if rating:
            msg_parts.append(f"\n⭐ Avaliação: {rating:.1f}/10")
        overview = item.get('Overview', '')
        if overview:
            if len(overview) > 200:
                overview = overview[:200] + "..."
            msg_parts.append(f"\n\n<i>{overview}</i>")
        return ''.join(msg_parts)

    def check_new_items(self, limit: int = 20) -> List[Dict]:
        if not self.jellyfin_manager or not self.jellyfin_manager.is_available():
            logger.warning("Jellyfin não disponível para verificação")
            return []
        
        try:
            all_new_items = []
            
            # Verifica cada cliente Jellyfin
            for client in self.jellyfin_manager.clients:
                try:
                    items = client.get_recently_added(limit)
                    if not items:
                        continue
                    
                    # Inicializa set de itens conhecidos para este servidor se não existir
                    if client.url not in self.known_items:
                        self.known_items[client.url] = set()
                    
                    # Verifica novos itens para este servidor
                    for item in items:
                        item_id = item.get('Id')
                        if item_id and item_id not in self.known_items[client.url]:
                            item['_jellyfin_url'] = client.url
                            all_new_items.append(item)
                            self.known_items[client.url].add(item_id)
                except Exception as e:
                    logger.error(f"Erro ao verificar itens de {client.url}: {e}")
            
            self.last_check_time = time.time()
            if all_new_items:
                self._save_state()
            
            return all_new_items
        except Exception as e:
            logger.error(f"Erro ao verificar novos itens: {e}")
            return []

    def send_notifications(self, new_items: List[Dict]):
        from src.integrations.telegram.client import send_telegram
        for item in new_items:
            try:
                message = self._format_item_notification(item)
                send_telegram(message, parse_mode="HTML", use_keyboard=True)
                logger.info(f"Notificação enviada: {item.get('Name', 'Sem nome')}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erro ao enviar notificação: {e}")

    def run_check(self):
        if not self.enabled:
            return
        logger.info("Verificando novos conteúdos no Jellyfin...")
        new_items = self.check_new_items()
        if new_items:
            logger.info(f"Encontrados {len(new_items)} novos itens")
            self.send_notifications(new_items)
        else:
            logger.debug("Nenhum novo item encontrado")

    def start_monitoring(self):
        logger.info(f"Iniciando monitoramento do Jellyfin (intervalo: {self.interval}s)")
        
        # Inicializa itens conhecidos para cada servidor na primeira execução
        if not self.known_items and self.jellyfin_manager.is_available():
            logger.info("Primeira execução: populando itens conhecidos...")
            for client in self.jellyfin_manager.clients:
                try:
                    items = client.get_recently_added(50)
                    self.known_items[client.url] = set()
                    for item in items:
                        item_id = item.get('Id')
                        if item_id:
                            self.known_items[client.url].add(item_id)
                    logger.info(f"Servidor {client.url}: {len(self.known_items[client.url])} itens conhecidos")
                except Exception as e:
                    logger.error(f"Erro ao inicializar itens de {client.url}: {e}")
            self._save_state()
            total_items = sum(len(items) for items in self.known_items.values())
            logger.info(f"Itens conhecidos inicializados: {total_items} em {len(self.known_items)} servidor(es)")

        last_check = 0
        while True:
            try:
                current_time = time.time()
                if current_time - last_check >= self.interval:
                    self.run_check()
                    last_check = current_time
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                time.sleep(60)

    def enable(self):
        self.enabled = True
        logger.info("Notificações do Jellyfin habilitadas")

    def disable(self):
        self.enabled = False
        logger.info("Notificações do Jellyfin desabilitadas")

    def reset_state(self):
        self.known_items = {}
        self.last_check_time = None
        self._save_state()
        logger.info("Estado do notificador resetado")
