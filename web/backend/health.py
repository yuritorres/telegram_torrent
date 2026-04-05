"""
Health check and monitoring utilities
Provides comprehensive health status for the application
"""
import time
import psutil
import platform
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: int
    uptime: float
    version: str = "1.0.0"
    services: Dict[str, bool]
    system: Optional[Dict] = None


class HealthMonitor:
    """
    Monitors application health and provides detailed status information
    Similar to Pulse's health monitoring system
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.version = "1.0.0"
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free,
                "disk_percent": disk.percent,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_service_health(self, service_name: str, check_func) -> bool:
        """
        Check if a service is healthy
        
        Args:
            service_name: Name of the service
            check_func: Function that returns True if service is healthy
            
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            return check_func()
        except Exception:
            return False
    
    def get_health_status(
        self,
        qb_connected: bool = False,
        jellyfin_connected: bool = False,
        docker_available: bool = False,
        telegram_storage_available: bool = False,
        include_system: bool = False
    ) -> HealthResponse:
        """
        Get comprehensive health status
        
        Args:
            qb_connected: Whether qBittorrent is connected
            jellyfin_connected: Whether Jellyfin is connected
            docker_available: Whether Docker is available
            telegram_storage_available: Whether Telegram storage is available
            include_system: Whether to include system information
            
        Returns:
            HealthResponse with current status
        """
        services = {
            "qbittorrent": qb_connected,
            "jellyfin": jellyfin_connected,
            "docker": docker_available,
            "telegram_storage": telegram_storage_available,
        }
        
        # Determine overall status
        # Healthy if at least qBittorrent is connected
        status = "healthy" if qb_connected else "degraded"
        
        response = HealthResponse(
            status=status,
            timestamp=int(time.time()),
            uptime=self.get_uptime(),
            version=self.version,
            services=services,
        )
        
        if include_system:
            response.system = self.get_system_info()
        
        return response


# Global health monitor instance
health_monitor = HealthMonitor()
