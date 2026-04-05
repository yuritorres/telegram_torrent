"""
Graceful shutdown handler for the application
Ensures clean shutdown of all services and connections
"""
import signal
import asyncio
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """
    Handles graceful shutdown of the application
    Registers signal handlers and cleanup functions
    """
    
    def __init__(self):
        self.shutdown_handlers: List[Callable] = []
        self.is_shutting_down = False
    
    def register_handler(self, handler: Callable):
        """
        Register a cleanup handler to be called on shutdown
        
        Args:
            handler: Async or sync function to call during shutdown
        """
        self.shutdown_handlers.append(handler)
    
    async def shutdown(self):
        """Execute all registered shutdown handlers"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("Initiating graceful shutdown...")
        
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error during shutdown handler: {e}")
        
        logger.info("Graceful shutdown completed")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)


# Global shutdown manager
shutdown_manager = GracefulShutdown()
