"""
Advanced Docker Management System
Inspired by Pulse's robust Docker monitoring and management architecture
Provides comprehensive container monitoring, stats collection, and management
"""
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class DockerStats:
    """Collects and processes Docker container statistics"""
    
    @staticmethod
    def calculate_cpu_percent(stats: Dict) -> float:
        """
        Calculate CPU usage percentage from Docker stats
        Based on Pulse's CPU calculation algorithm
        """
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            
            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          precpu_stats.get('system_cpu_usage', 0)
            
            online_cpus = cpu_stats.get('online_cpus', 0)
            if online_cpus == 0:
                online_cpus = len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', []))
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                return round(cpu_percent, 2)
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating CPU percent: {e}")
            return 0.0
    
    @staticmethod
    def calculate_memory_stats(stats: Dict) -> Dict[str, int]:
        """Calculate memory usage statistics"""
        try:
            mem_stats = stats.get('memory_stats', {})
            usage = mem_stats.get('usage', 0)
            limit = mem_stats.get('limit', 0)
            cache = mem_stats.get('stats', {}).get('cache', 0)
            
            # Active memory (excluding cache)
            active_memory = usage - cache if usage > cache else usage
            
            percent = (active_memory / limit * 100) if limit > 0 else 0
            
            return {
                'usage': usage,
                'limit': limit,
                'cache': cache,
                'active': active_memory,
                'percent': round(percent, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating memory stats: {e}")
            return {'usage': 0, 'limit': 0, 'cache': 0, 'active': 0, 'percent': 0}
    
    @staticmethod
    def calculate_network_stats(stats: Dict) -> Dict[str, int]:
        """Calculate network I/O statistics"""
        try:
            networks = stats.get('networks', {})
            total_rx = 0
            total_tx = 0
            
            for interface, data in networks.items():
                total_rx += data.get('rx_bytes', 0)
                total_tx += data.get('tx_bytes', 0)
            
            return {
                'rx_bytes': total_rx,
                'tx_bytes': total_tx,
                'total_bytes': total_rx + total_tx
            }
        except Exception as e:
            logger.error(f"Error calculating network stats: {e}")
            return {'rx_bytes': 0, 'tx_bytes': 0, 'total_bytes': 0}
    
    @staticmethod
    def calculate_block_io_stats(stats: Dict) -> Dict[str, int]:
        """Calculate block I/O statistics"""
        try:
            blkio_stats = stats.get('blkio_stats', {})
            io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
            
            total_read = 0
            total_write = 0
            
            for entry in io_service_bytes:
                op = entry.get('op', '')
                value = entry.get('value', 0)
                
                if op == 'Read':
                    total_read += value
                elif op == 'Write':
                    total_write += value
            
            return {
                'read_bytes': total_read,
                'write_bytes': total_write,
                'total_bytes': total_read + total_write
            }
        except Exception as e:
            logger.error(f"Error calculating block I/O stats: {e}")
            return {'read_bytes': 0, 'write_bytes': 0, 'total_bytes': 0}


class DockerManager:
    """
    Advanced Docker management system
    Provides comprehensive container monitoring and management capabilities
    """
    
    def __init__(self, docker_client=None):
        self.client = docker_client
        self._available = docker_client is not None
        self.stats_cache = {}
        self.stats_cache_ttl = 5  # seconds
        
    def is_available(self) -> bool:
        """Check if Docker is available"""
        return self._available and self.client is not None
    
    def list_containers(self, all: bool = True, filters: Dict = None) -> List[Dict]:
        """
        List containers with enhanced information
        
        Args:
            all: Include stopped containers
            filters: Docker filters (e.g., {'status': 'running'})
            
        Returns:
            List of container dictionaries with enhanced metadata
        """
        if not self.is_available():
            return []
        
        try:
            containers = self.client.containers.list(all=all, filters=filters)
            result = []
            
            for c in containers:
                labels = c.labels or {}
                
                # Extract Docker Compose information
                compose_project = labels.get('com.docker.compose.project')
                compose_service = labels.get('com.docker.compose.service')
                compose_number = labels.get('com.docker.compose.container-number')
                
                # Get network information
                networks = []
                for net_name, net_config in c.attrs.get('NetworkSettings', {}).get('Networks', {}).items():
                    networks.append({
                        'name': net_name,
                        'ip_address': net_config.get('IPAddress', ''),
                        'gateway': net_config.get('Gateway', ''),
                        'mac_address': net_config.get('MacAddress', '')
                    })
                
                # Get port bindings
                ports = []
                port_bindings = c.attrs.get('NetworkSettings', {}).get('Ports', {})
                for container_port, host_bindings in (port_bindings or {}).items():
                    if host_bindings:
                        for binding in host_bindings:
                            ports.append({
                                'container_port': container_port,
                                'host_ip': binding.get('HostIp', '0.0.0.0'),
                                'host_port': binding.get('HostPort', '')
                            })
                
                # Get mounts/volumes
                mounts = []
                for mount in c.attrs.get('Mounts', []):
                    mounts.append({
                        'type': mount.get('Type'),
                        'source': mount.get('Source'),
                        'destination': mount.get('Destination'),
                        'mode': mount.get('Mode'),
                        'rw': mount.get('RW', True)
                    })
                
                container_info = {
                    'id': c.id,
                    'short_id': c.short_id,
                    'name': c.name,
                    'status': c.status,
                    'state': c.attrs.get('State', {}).get('Status', 'unknown'),
                    'image': c.image.tags[0] if c.image.tags else c.image.short_id,
                    'image_id': c.image.short_id,
                    'created': c.attrs.get('Created'),
                    'started_at': c.attrs.get('State', {}).get('StartedAt'),
                    'finished_at': c.attrs.get('State', {}).get('FinishedAt'),
                    'restart_count': c.attrs.get('RestartCount', 0),
                    'labels': labels,
                    'networks': networks,
                    'ports': ports,
                    'mounts': mounts,
                    # Docker Compose metadata
                    'compose': {
                        'project': compose_project,
                        'service': compose_service,
                        'number': compose_number,
                        'is_compose': compose_project is not None
                    } if compose_project else None,
                }
                
                result.append(container_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []
    
    def get_container_stats(self, container_id: str, stream: bool = False) -> Optional[Dict]:
        """
        Get container statistics with caching
        
        Args:
            container_id: Container ID or name
            stream: Whether to stream stats (not implemented for single call)
            
        Returns:
            Container statistics dictionary
        """
        if not self.is_available():
            return None
        
        # Check cache
        cache_key = container_id
        if cache_key in self.stats_cache:
            cached_stats, cached_time = self.stats_cache[cache_key]
            if time.time() - cached_time < self.stats_cache_ttl:
                return cached_stats
        
        try:
            container = self.client.containers.get(container_id)
            raw_stats = container.stats(stream=False)
            
            # Process stats
            processed_stats = {
                'container_id': container_id,
                'container_name': container.name,
                'timestamp': datetime.now().isoformat(),
                'cpu': DockerStats.calculate_cpu_percent(raw_stats),
                'memory': DockerStats.calculate_memory_stats(raw_stats),
                'network': DockerStats.calculate_network_stats(raw_stats),
                'block_io': DockerStats.calculate_block_io_stats(raw_stats),
                'pids': raw_stats.get('pids_stats', {}).get('current', 0),
                'raw': raw_stats  # Include raw stats for advanced use
            }
            
            # Cache the result
            self.stats_cache[cache_key] = (processed_stats, time.time())
            
            return processed_stats
            
        except Exception as e:
            logger.error(f"Error getting container stats for {container_id}: {e}")
            return None
    
    def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: Optional[str] = None,
        until: Optional[str] = None,
        timestamps: bool = True
    ) -> Optional[str]:
        """
        Get container logs
        
        Args:
            container_id: Container ID or name
            tail: Number of lines to return from the end
            since: Show logs since timestamp or relative (e.g., '1h')
            until: Show logs until timestamp
            timestamps: Include timestamps in output
            
        Returns:
            Container logs as string
        """
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(
                tail=tail,
                since=since,
                until=until,
                timestamps=timestamps
            )
            return logs.decode('utf-8', errors='replace')
            
        except Exception as e:
            logger.error(f"Error getting logs for {container_id}: {e}")
            return None
    
    def inspect_container(self, container_id: str) -> Optional[Dict]:
        """
        Get detailed container inspection data
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Full container inspection dictionary
        """
        if not self.is_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            return container.attrs
            
        except Exception as e:
            logger.error(f"Error inspecting container {container_id}: {e}")
            return None
    
    def start_container(self, container_id: str) -> tuple[bool, str]:
        """Start a container"""
        if not self.is_available():
            return False, "Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Container started: {container.name}")
            return True, f"Container '{container.name}' started successfully"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error starting container {container_id}: {error_msg}")
            return False, error_msg
    
    def stop_container(self, container_id: str, timeout: int = 10) -> tuple[bool, str]:
        """Stop a container with timeout"""
        if not self.is_available():
            return False, "Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Container stopped: {container.name}")
            return True, f"Container '{container.name}' stopped successfully"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error stopping container {container_id}: {error_msg}")
            return False, error_msg
    
    def restart_container(self, container_id: str, timeout: int = 10) -> tuple[bool, str]:
        """Restart a container"""
        if not self.is_available():
            return False, "Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            logger.info(f"Container restarted: {container.name}")
            return True, f"Container '{container.name}' restarted successfully"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error restarting container {container_id}: {error_msg}")
            return False, error_msg
    
    def pause_container(self, container_id: str) -> tuple[bool, str]:
        """Pause a container"""
        if not self.is_available():
            return False, "Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            container.pause()
            logger.info(f"Container paused: {container.name}")
            return True, f"Container '{container.name}' paused successfully"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error pausing container {container_id}: {error_msg}")
            return False, error_msg
    
    def unpause_container(self, container_id: str) -> tuple[bool, str]:
        """Unpause a container"""
        if not self.is_available():
            return False, "Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            container.unpause()
            logger.info(f"Container unpaused: {container.name}")
            return True, f"Container '{container.name}' unpaused successfully"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error unpausing container {container_id}: {error_msg}")
            return False, error_msg
    
    def remove_container(self, container_id: str, force: bool = False, volumes: bool = False) -> tuple[bool, str]:
        """
        Remove a container
        
        Args:
            container_id: Container ID or name
            force: Force removal of running container
            volumes: Remove associated volumes
        """
        if not self.is_available():
            return False, "Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            container_name = container.name
            container.remove(force=force, v=volumes)
            logger.info(f"Container removed: {container_name}")
            return True, f"Container '{container_name}' removed successfully"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error removing container {container_id}: {error_msg}")
            return False, error_msg
    
    def get_compose_stacks(self) -> List[Dict]:
        """
        Get all Docker Compose stacks (projects)
        Groups containers by compose project
        
        Returns:
            List of stack dictionaries with containers
        """
        if not self.is_available():
            return []
        
        try:
            containers = self.list_containers(all=True)
            stacks = defaultdict(lambda: {
                'name': '',
                'containers': [],
                'services': set(),
                'running': 0,
                'stopped': 0,
                'total': 0
            })
            
            for container in containers:
                compose_info = container.get('compose')
                if compose_info and compose_info.get('project'):
                    project = compose_info['project']
                    service = compose_info.get('service', 'unknown')
                    
                    stacks[project]['name'] = project
                    stacks[project]['containers'].append(container)
                    stacks[project]['services'].add(service)
                    stacks[project]['total'] += 1
                    
                    if container['state'] == 'running':
                        stacks[project]['running'] += 1
                    else:
                        stacks[project]['stopped'] += 1
            
            # Convert to list and clean up
            result = []
            for project, data in stacks.items():
                data['services'] = list(data['services'])
                result.append(data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting compose stacks: {e}")
            return []
    
    def get_system_info(self) -> Optional[Dict]:
        """Get Docker system information"""
        if not self.is_available():
            return None
        
        try:
            info = self.client.info()
            return {
                'containers': info.get('Containers', 0),
                'containers_running': info.get('ContainersRunning', 0),
                'containers_paused': info.get('ContainersPaused', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0),
                'driver': info.get('Driver', 'unknown'),
                'docker_version': info.get('ServerVersion', 'unknown'),
                'operating_system': info.get('OperatingSystem', 'unknown'),
                'architecture': info.get('Architecture', 'unknown'),
                'cpus': info.get('NCPU', 0),
                'memory_total': info.get('MemTotal', 0),
                'name': info.get('Name', 'unknown'),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return None
    
    async def stream_container_stats(self, container_id: str, callback):
        """
        Stream container stats asynchronously
        
        Args:
            container_id: Container ID or name
            callback: Async function to call with each stat update
        """
        if not self.is_available():
            return
        
        try:
            container = self.client.containers.get(container_id)
            
            for raw_stats in container.stats(stream=True, decode=True):
                processed_stats = {
                    'container_id': container_id,
                    'container_name': container.name,
                    'timestamp': datetime.now().isoformat(),
                    'cpu': DockerStats.calculate_cpu_percent(raw_stats),
                    'memory': DockerStats.calculate_memory_stats(raw_stats),
                    'network': DockerStats.calculate_network_stats(raw_stats),
                    'block_io': DockerStats.calculate_block_io_stats(raw_stats),
                }
                
                await callback(processed_stats)
                
        except Exception as e:
            logger.error(f"Error streaming stats for {container_id}: {e}")
