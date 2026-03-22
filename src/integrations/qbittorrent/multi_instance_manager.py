import requests
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from threading import Lock
import time

logger = logging.getLogger(__name__)


@dataclass
class QBInstance:
    name: str
    url: str
    username: str
    password: str
    storage_path: str
    session: Optional[requests.Session] = None
    last_check: float = 0
    available_space: int = 0
    total_space: int = 0
    is_active: bool = False
    priority: int = 0


class MultiInstanceManager:
    def __init__(self):
        self.instances: Dict[str, QBInstance] = {}
        self.lock = Lock()
        self.storage_check_interval = 60
        
    def add_instance(
        self,
        name: str,
        url: str,
        username: str,
        password: str,
        storage_path: str = "/",
        priority: int = 0
    ) -> bool:
        with self.lock:
            if name in self.instances:
                logger.warning(f"Instância '{name}' já existe. Atualizando configuração.")
            
            instance = QBInstance(
                name=name,
                url=url,
                username=username,
                password=password,
                storage_path=storage_path,
                priority=priority
            )
            
            if self._connect_instance(instance):
                self.instances[name] = instance
                logger.info(f"Instância '{name}' adicionada com sucesso.")
                return True
            else:
                logger.error(f"Falha ao conectar à instância '{name}'.")
                return False
    
    def remove_instance(self, name: str) -> bool:
        with self.lock:
            if name in self.instances:
                instance = self.instances[name]
                if instance.session:
                    try:
                        instance.session.close()
                    except:
                        pass
                del self.instances[name]
                logger.info(f"Instância '{name}' removida.")
                return True
            logger.warning(f"Instância '{name}' não encontrada.")
            return False
    
    def _connect_instance(self, instance: QBInstance) -> bool:
        session = requests.Session()
        try:
            resp = session.post(
                f"{instance.url}/api/v2/auth/login",
                data={"username": instance.username, "password": instance.password},
                timeout=10,
            )
            resp.raise_for_status()
            if resp.text == "Ok.":
                instance.session = session
                instance.is_active = True
                self._update_storage_info(instance)
                logger.info(f"Conectado à instância '{instance.name}' em {instance.url}")
                return True
            logger.error(f"Falha no login da instância '{instance.name}': {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Erro ao conectar à instância '{instance.name}': {e}")
            return False
    
    def _update_storage_info(self, instance: QBInstance) -> bool:
        if not instance.session:
            return False
        
        try:
            # Obter informações do servidor via sync/maindata
            resp = instance.session.get(
                f"{instance.url}/api/v2/sync/maindata",
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            server_state = data.get("server_state", {})
            free_space = server_state.get("free_space_on_disk", 0)
            
            # Calcular espaço usado pelos torrents
            try:
                torrents_resp = instance.session.get(
                    f"{instance.url}/api/v2/torrents/info",
                    timeout=10
                )
                torrents_resp.raise_for_status()
                torrents = torrents_resp.json()
                
                # Somar o tamanho de todos os torrents
                used_space = sum(torrent.get("size", 0) for torrent in torrents)
                total_space = free_space + used_space
                
                logger.debug(
                    f"Instância '{instance.name}': "
                    f"Usado: {self._format_bytes(used_space)}, "
                    f"Livre: {self._format_bytes(free_space)}, "
                    f"Total calculado: {self._format_bytes(total_space)}"
                )
            except Exception as torrent_err:
                logger.debug(f"Erro ao obter torrents para calcular espaço usado em '{instance.name}': {torrent_err}")
                # Fallback: usar apenas espaço livre como total (não ideal, mas funcional)
                total_space = free_space
            
            instance.available_space = free_space
            instance.total_space = total_space if total_space > 0 else free_space
            instance.last_check = time.time()
            
            logger.debug(
                f"Instância '{instance.name}': "
                f"{self._format_bytes(instance.available_space)} livres de "
                f"{self._format_bytes(instance.total_space)}"
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao obter informações de armazenamento da instância '{instance.name}': {e}")
            instance.is_active = False
            return False
    
    def update_all_storage_info(self) -> None:
        with self.lock:
            for instance in self.instances.values():
                if instance.is_active:
                    self._update_storage_info(instance)
    
    def get_best_instance_for_download(self, estimated_size: int = 0) -> Optional[QBInstance]:
        with self.lock:
            current_time = time.time()
            
            for instance in self.instances.values():
                if instance.is_active and (current_time - instance.last_check) > self.storage_check_interval:
                    self._update_storage_info(instance)
            
            active_instances = [
                inst for inst in self.instances.values()
                if inst.is_active and inst.available_space > estimated_size
            ]
            
            if not active_instances:
                logger.warning("Nenhuma instância ativa com espaço suficiente disponível.")
                return None
            
            active_instances.sort(
                key=lambda x: (x.priority, x.available_space),
                reverse=True
            )
            
            best = active_instances[0]
            logger.info(
                f"Instância selecionada: '{best.name}' com "
                f"{self._format_bytes(best.available_space)} disponíveis"
            )
            return best
    
    def get_instance(self, name: str) -> Optional[QBInstance]:
        with self.lock:
            return self.instances.get(name)
    
    def get_all_instances(self) -> List[QBInstance]:
        with self.lock:
            return list(self.instances.values())
    
    def get_instances_summary(self) -> str:
        with self.lock:
            if not self.instances:
                return "Nenhuma instância configurada."
            
            lines = ["📊 **Instâncias qBittorrent:**\n"]
            for instance in sorted(self.instances.values(), key=lambda x: x.name):
                status = "✅ Ativa" if instance.is_active else "❌ Inativa"
                space_info = ""
                if instance.is_active and instance.available_space > 0:
                    space_info = (
                        f"\n   💾 Espaço: {self._format_bytes(instance.available_space)} livres / "
                        f"{self._format_bytes(instance.total_space)} total"
                    )
                priority_info = f"\n   ⭐ Prioridade: {instance.priority}" if instance.priority > 0 else ""
                
                lines.append(
                    f"• **{instance.name}** ({status})\n"
                    f"   🔗 {instance.url}"
                    f"{space_info}"
                    f"{priority_info}\n"
                )
            
            return "\n".join(lines)
    
    def add_magnet_smart(
        self,
        magnet: str,
        estimated_size: int = 0,
        preferred_instance: Optional[str] = None
    ) -> Tuple[bool, str]:
        instance = None
        
        if preferred_instance:
            instance = self.get_instance(preferred_instance)
            if not instance or not instance.is_active:
                return False, f"Instância '{preferred_instance}' não está disponível."
        else:
            instance = self.get_best_instance_for_download(estimated_size)
        
        if not instance:
            return False, "Nenhuma instância disponível para adicionar o download."
        
        try:
            resp = instance.session.post(
                f"{instance.url}/api/v2/torrents/add",
                data={"urls": magnet},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info(f"Magnet adicionado à instância '{instance.name}'.")
            return True, f"Download adicionado à instância '{instance.name}' ({self._format_bytes(instance.available_space)} disponíveis)"
        except Exception as e:
            logger.error(f"Erro ao adicionar magnet à instância '{instance.name}': {e}")
            return False, f"Erro ao adicionar download: {str(e)}"
    
    def get_all_torrents(self) -> Dict[str, List[Dict]]:
        result = {}
        with self.lock:
            for instance in self.instances.values():
                if instance.is_active and instance.session:
                    try:
                        resp = instance.session.get(
                            f"{instance.url}/api/v2/torrents/info",
                            timeout=10
                        )
                        resp.raise_for_status()
                        result[instance.name] = resp.json()
                    except Exception as e:
                        logger.error(f"Erro ao buscar torrents da instância '{instance.name}': {e}")
                        result[instance.name] = []
        return result
    
    def reconnect_all(self) -> Dict[str, bool]:
        results = {}
        with self.lock:
            for name, instance in self.instances.items():
                if instance.session:
                    try:
                        instance.session.close()
                    except:
                        pass
                results[name] = self._connect_instance(instance)
        return results
    
    @staticmethod
    def _format_bytes(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


_manager_instance: Optional[MultiInstanceManager] = None


def get_manager() -> MultiInstanceManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MultiInstanceManager()
    return _manager_instance
