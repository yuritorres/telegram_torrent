"""
Middleware components for enhanced security, error handling, and monitoring
Inspired by Pulse's robust middleware architecture
"""
import time
import uuid
import logging
import traceback
from typing import Callable, Dict, Optional
from datetime import datetime
from collections import defaultdict
from threading import Lock
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check for existing request ID from client
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler with panic recovery
    Catches all unhandled exceptions and returns structured error responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log errors (4xx and 5xx)
            if response.status_code >= 400:
                elapsed = time.time() - start_time
                logger.warning(
                    f"Request failed: {request.method} {request.url.path} "
                    f"status={response.status_code} "
                    f"request_id={request_id} "
                    f"elapsed={elapsed:.3f}s"
                )
            
            return response
            
        except Exception as e:
            # Panic recovery - catch all unhandled exceptions
            elapsed = time.time() - start_time
            error_trace = traceback.format_exc()
            
            logger.error(
                f"Panic recovered in API handler: {request.method} {request.url.path} "
                f"error={str(e)} "
                f"request_id={request_id} "
                f"elapsed={elapsed:.3f}s\n{error_trace}"
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "An unexpected error occurred",
                    "code": "internal_error",
                    "status_code": 500,
                    "timestamp": int(time.time()),
                    "request_id": request_id,
                }
            )


class RateLimiter:
    """
    Token bucket rate limiter for controlling request rates
    """
    
    def __init__(self, limit: int, window_seconds: int):
        """
        Args:
            limit: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.limit = limit
        self.window = window_seconds
        self.attempts: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def allow(self, client_id: str) -> bool:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Unique identifier for the client (usually IP address)
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()
            
            # Clean old attempts outside the window
            if client_id in self.attempts:
                self.attempts[client_id] = [
                    timestamp for timestamp in self.attempts[client_id]
                    if now - timestamp < self.window
                ]
            
            # Check if limit exceeded
            if len(self.attempts[client_id]) >= self.limit:
                return False
            
            # Add new attempt
            self.attempts[client_id].append(now)
            return True
    
    def reset(self, client_id: str):
        """Reset rate limit for a specific client"""
        with self.lock:
            if client_id in self.attempts:
                del self.attempts[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with different limits per endpoint category
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Initialize rate limiters for different endpoint categories
        self.auth_limiter = RateLimiter(10, 60)  # 10 attempts per minute
        self.config_limiter = RateLimiter(30, 60)  # 30 changes per minute
        self.general_limiter = RateLimiter(500, 60)  # 500 requests per minute
        self.public_limiter = RateLimiter(1000, 60)  # 1000 requests per minute
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def get_limiter_for_path(self, path: str, method: str) -> Optional[RateLimiter]:
        """Select appropriate rate limiter based on endpoint"""
        
        # Skip rate limiting for static assets
        if not path.startswith("/api"):
            return None
        
        # Skip rate limiting for real-time endpoints
        skip_paths = ["/api/system/status", "/api/torrents"]
        if any(path.startswith(skip_path) for skip_path in skip_paths) and method == "GET":
            return None
        
        # Authentication endpoints - strict limits
        if any(auth_path in path for auth_path in ["/api/auth/login", "/api/auth/generate-hash"]):
            return self.auth_limiter
        
        # Configuration endpoints - moderate limits
        if "/api/config" in path or "/api/settings" in path:
            return self.config_limiter
        
        # Public endpoints - high limits
        if path in ["/api/health", "/", "/api/auth/verify"]:
            return self.public_limiter
        
        # Default to general API limiter
        return self.general_limiter
    
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        method = request.method
        
        # Get appropriate limiter
        limiter = self.get_limiter_for_path(path, method)
        
        # Skip if no limiter or WebSocket upgrade
        if not limiter or request.headers.get("Upgrade") == "websocket":
            return await call_next(request)
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Skip rate limiting for localhost (direct loopback only)
        if client_ip in ["127.0.0.1", "::1", "localhost"] and not request.headers.get("X-Forwarded-For"):
            return await call_next(request)
        
        # Check rate limit
        if not limiter.allow(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded. Please try again later.",
                    "code": "rate_limit_exceeded",
                    "status_code": 429,
                    "timestamp": int(time.time()),
                },
                headers={
                    "Retry-After": str(limiter.window),
                    "X-RateLimit-Limit": str(limiter.limit),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured logging middleware with request/response details
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"request_id={request_id} "
            f"client={request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        
        # Log response
        log_level = logger.info if response.status_code < 400 else logger.warning
        log_level(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"request_id={request_id} "
            f"elapsed={elapsed:.3f}s"
        )
        
        return response
