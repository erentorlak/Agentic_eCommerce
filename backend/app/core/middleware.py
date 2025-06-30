"""
Middleware for the Migration System

Following best practices:
- Request/Response logging with correlation IDs
- Security headers (CORS, CSP, HSTS)
- Rate limiting and request validation
- Performance monitoring
- Error handling and recovery
"""

import time
import uuid
import json
from typing import Callable, Dict, Any
from datetime import datetime, timezone

import structlog
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

from ..core.config import get_settings
from ..core.exceptions import RateLimitError, create_http_exception

logger = structlog.get_logger(__name__)
settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging
    
    Features:
    - Correlation ID generation
    - Request/response timing
    - Error context preservation
    - Performance metrics
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, correlation_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, correlation_id, duration)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as exc:
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                correlation_id=correlation_id,
                method=request.method,
                url=str(request.url),
                duration=duration,
                error=str(exc),
                error_type=type(exc).__name__
            )
            
            # Re-raise for error handlers
            raise
    
    async def _log_request(self, request: Request, correlation_id: str):
        """Log incoming request details"""
        
        # Extract client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract request body for non-GET requests (with size limit)
        body = None
        if request.method != "GET":
            try:
                body_bytes = await request.body()
                if len(body_bytes) < 1024:  # Only log small bodies
                    body = body_bytes.decode("utf-8")
                else:
                    body = f"<body too large: {len(body_bytes)} bytes>"
            except Exception:
                body = "<body read error>"
            
            # Reset body for actual handler
            request._body = body_bytes
        
        logger.info(
            "Request received",
            correlation_id=correlation_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=dict(request.headers),
            client_ip=client_ip,
            user_agent=user_agent,
            body=body,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    async def _log_response(self, request: Request, response: Response, correlation_id: str, duration: float):
        """Log response details"""
        
        logger.info(
            "Request completed",
            correlation_id=correlation_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration,
            response_size=response.headers.get("content-length", "unknown"),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP considering proxies"""
        
        # Check forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security headers
    
    Implements OWASP recommendations:
    - Content Security Policy
    - Strict Transport Security
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer Policy
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.csp_policy = self._build_csp_policy()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": self.csp_policy,
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        # Add HSTS for HTTPS
        if request.url.scheme == "https" or settings.ENVIRONMENT == "production":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _build_csp_policy(self) -> str:
        """Build Content Security Policy"""
        
        if settings.ENVIRONMENT == "development":
            # More relaxed CSP for development
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' data:;"
            )
        else:
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "font-src 'self';"
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    
    Features:
    - Per-IP rate limiting
    - Different limits for different endpoints
    - Sliding window implementation
    - Rate limit headers
    """
    
    def __init__(self, app, default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/v1/migrations": {"limit": 10, "window": 60},
            "/api/v1/auth/login": {"limit": 5, "window": 300},
            "/docs": {"limit": 20, "window": 60},
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id, request.url.path):
            # Add rate limit headers
            response = Response(
                content=json.dumps({
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded for {client_id}",
                    "retry_after": self.window_seconds
                }),
                status_code=429,
                media_type="application/json"
            )
            
            self._add_rate_limit_headers(response, client_id, request.url.path)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        self._add_rate_limit_headers(response, client_id, request.url.path)
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Use API key if available
        api_key = request.headers.get("x-api-key")
        if api_key:
            return f"api_key:{api_key[:8]}..."
        
        # Use JWT subject if available
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fallback to IP
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip and hasattr(request, "client"):
            client_ip = request.client.host
        
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str, path: str) -> bool:
        """Check if request is within rate limit"""
        
        now = time.time()
        
        # Get limits for this endpoint
        limit_config = self._get_limit_config(path)
        limit = limit_config["limit"]
        window = limit_config["window"]
        
        # Initialize or clean old requests
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside window
        cutoff = now - window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= limit:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def _get_limit_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for path"""
        
        # Check for exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for prefix matches
        for endpoint_path, config in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return config
        
        # Default limits
        return {"limit": self.default_limit, "window": self.window_seconds}
    
    def _add_rate_limit_headers(self, response: Response, client_id: str, path: str):
        """Add rate limit headers to response"""
        
        limit_config = self._get_limit_config(path)
        limit = limit_config["limit"]
        window = limit_config["window"]
        
        current_requests = len(self.requests.get(client_id, []))
        remaining = max(0, limit - current_requests)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)
        
        if remaining == 0:
            response.headers["Retry-After"] = str(window)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware
    
    Features:
    - Structured error responses
    - Error logging with context
    - Development vs production error details
    - Error recovery and fallbacks
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except Exception as exc:
            return await self._handle_exception(request, exc)
    
    async def _handle_exception(self, request: Request, exc: Exception) -> Response:
        """Handle exceptions and return appropriate responses"""
        
        # Get correlation ID if available
        correlation_id = getattr(request.state, "correlation_id", None)
        
        # Import here to avoid circular imports
        from ..core.exceptions import BaseCustomException, create_http_exception
        
        # Handle custom exceptions
        if isinstance(exc, BaseCustomException):
            logger.warning(
                "Custom exception occurred",
                correlation_id=correlation_id,
                error_code=exc.error_code,
                message=exc.message,
                context=exc.context,
                path=request.url.path,
                method=request.method
            )
            
            http_exc = create_http_exception(exc)
            return self._create_error_response(
                status_code=http_exc.status_code,
                error_detail=http_exc.detail,
                correlation_id=correlation_id
            )
        
        # Handle unexpected exceptions
        logger.error(
            "Unexpected exception occurred",
            correlation_id=correlation_id,
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
            exc_info=True
        )
        
        # Return generic error for production
        if settings.ENVIRONMENT == "production":
            error_detail = {
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again later.",
                "type": "InternalServerError"
            }
        else:
            # Detailed error for development
            error_detail = {
                "error_code": "INTERNAL_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
                "traceback": self._get_traceback() if settings.DEBUG else None
            }
        
        return self._create_error_response(
            status_code=500,
            error_detail=error_detail,
            correlation_id=correlation_id
        )
    
    def _create_error_response(self, status_code: int, error_detail: Dict[str, Any], correlation_id: str = None) -> Response:
        """Create standardized error response"""
        
        response_data = {
            "success": False,
            "error": error_detail,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if correlation_id:
            response_data["correlation_id"] = correlation_id
        
        response = Response(
            content=json.dumps(response_data, default=str),
            status_code=status_code,
            media_type="application/json"
        )
        
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    def _get_traceback(self) -> str:
        """Get formatted traceback for debugging"""
        import traceback
        return traceback.format_exc()


def setup_middleware(app):
    """Setup all middleware for the application"""
    
    # Error handling (should be first)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, default_limit=100, window_seconds=60)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS (should be last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS if settings.ALLOWED_HOSTS else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Response-Time", "X-RateLimit-*"]
    )
    
    # Trusted hosts (for production)
    if settings.ENVIRONMENT == "production" and settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    logger.info("Middleware setup completed", middleware_count=len(app.middleware_stack))