import logging
import docker
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.available = True
            logger.info("Docker client inicializado com sucesso")
        except Exception as e:
            logger.warning(f"Docker não disponível: {e}")
            self.client = None
            self.available = False

    def is_available(self) -> bool:
        return self.available and self.client is not None

    def list_containers(self, all_containers: bool = True) -> List[Dict]:
        if not self.is_available():
            return []
        
        try:
            containers = self.client.containers.list(all=all_containers)
            result = []
            
            for container in containers:
                result.append({
                    'id': container.short_id,
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created'],
                })
            
            return result
        except Exception as e:
            logger.error(f"Erro ao listar containers: {e}")
            return []

    def start_container(self, container_name_or_id: str) -> tuple[bool, str]:
        if not self.is_available():
            return False, "Docker não disponível"
        
        try:
            container = self.client.containers.get(container_name_or_id)
            container.start()
            logger.info(f"Container {container_name_or_id} iniciado com sucesso")
            return True, f"Container '{container.name}' iniciado com sucesso"
        except docker.errors.NotFound:
            return False, f"Container '{container_name_or_id}' não encontrado"
        except docker.errors.APIError as e:
            logger.error(f"Erro ao iniciar container {container_name_or_id}: {e}")
            return False, f"Erro ao iniciar container: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado ao iniciar container: {e}")
            return False, f"Erro inesperado: {str(e)}"

    def stop_container(self, container_name_or_id: str, timeout: int = 10) -> tuple[bool, str]:
        if not self.is_available():
            return False, "Docker não disponível"
        
        try:
            container = self.client.containers.get(container_name_or_id)
            container.stop(timeout=timeout)
            logger.info(f"Container {container_name_or_id} parado com sucesso")
            return True, f"Container '{container.name}' parado com sucesso"
        except docker.errors.NotFound:
            return False, f"Container '{container_name_or_id}' não encontrado"
        except docker.errors.APIError as e:
            logger.error(f"Erro ao parar container {container_name_or_id}: {e}")
            return False, f"Erro ao parar container: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado ao parar container: {e}")
            return False, f"Erro inesperado: {str(e)}"

    def restart_container(self, container_name_or_id: str, timeout: int = 10) -> tuple[bool, str]:
        if not self.is_available():
            return False, "Docker não disponível"
        
        try:
            container = self.client.containers.get(container_name_or_id)
            container.restart(timeout=timeout)
            logger.info(f"Container {container_name_or_id} reiniciado com sucesso")
            return True, f"Container '{container.name}' reiniciado com sucesso"
        except docker.errors.NotFound:
            return False, f"Container '{container_name_or_id}' não encontrado"
        except docker.errors.APIError as e:
            logger.error(f"Erro ao reiniciar container {container_name_or_id}: {e}")
            return False, f"Erro ao reiniciar container: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado ao reiniciar container: {e}")
            return False, f"Erro inesperado: {str(e)}"

    def get_container_stats(self, container_name_or_id: str) -> Optional[Dict]:
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_name_or_id)
            stats = container.stats(stream=False)
            
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
            
            mem_usage = stats['memory_stats']['usage']
            mem_limit = stats['memory_stats']['limit']
            mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0
            
            return {
                'name': container.name,
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage': mem_usage,
                'memory_limit': mem_limit,
                'memory_percent': round(mem_percent, 2),
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do container: {e}")
            return None

    def get_container_logs(self, container_name_or_id: str, tail: int = 50) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_name_or_id)
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs
        except Exception as e:
            logger.error(f"Erro ao obter logs do container: {e}")
            return None
