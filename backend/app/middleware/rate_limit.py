import time
from fastapi import Request, HTTPException
from collections import defaultdict
from app.config import settings
import structlog

logger = structlog.get_logger()

# Simple in-memory MVP rate limiter based on IP
# Note: For production, Redis or a proper store should be used.
_requests = defaultdict(list)

async def rate_limit_middleware(request: Request):
    """
    Dependency that enforces a basic rate limit per IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean up old requests
    _requests[client_ip] = [
        t for t in _requests[client_ip] 
        if current_time - t < settings.rate_limit_window_seconds
    ]
    
    if len(_requests[client_ip]) >= settings.rate_limit_requests:
        logger.warning("rate_limit_exceeded", ip=client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
        
    _requests[client_ip].append(current_time)
