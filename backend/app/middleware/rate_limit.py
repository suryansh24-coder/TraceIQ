"""
TraceIQ - Rate Limiting

Request-level rate limiting for TraceIQ API endpoints.

This implementation provides a lightweight in-memory limiter suitable for:
- Local development
- Hackathon deployments
- Single-instance deployments

For multi-instance production deployments, the limiter should eventually
use Redis or another shared distributed store.

Important:
This function is intentionally implemented as a FastAPI dependency rather
than ASGI middleware because individual routes can selectively opt into
rate limiting using:

    Depends(rate_limit_middleware)
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Final

import structlog
from fastapi import HTTPException, Request, status

from app.config import settings


logger = structlog.get_logger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================


_MIN_WINDOW_SECONDS: Final[float] = 1.0
_MIN_REQUESTS: Final[int] = 1

# Prevent the local limiter from retaining unlimited client identifiers.
_MAX_TRACKED_CLIENTS: Final[int] = 10_000


# ============================================================================
# STATE
# ============================================================================


@dataclass(slots=True)
class _ClientBucket:
    """
    Sliding-window state for a single client.

    deque is used instead of a normal list because expired timestamps are
    always removed from the left side.
    """

    timestamps: deque[float]


_requests: dict[str, _ClientBucket] = {}

# Asyncio lock prevents concurrent requests from modifying the same shared
# in-memory state simultaneously.
_lock = asyncio.Lock()


# ============================================================================
# CLIENT IDENTIFICATION
# ============================================================================


def _get_client_identifier(
    request: Request,
) -> str:
    """
    Return the identifier used for rate limiting.

    Currently this is the direct client IP.

    We intentionally do not blindly trust X-Forwarded-For here. In production,
    trusted proxy configuration should be handled at the ASGI/server layer
    before forwarded headers are accepted as authoritative.
    """

    if request.client is None:
        return "unknown"

    host = request.client.host.strip()

    return host or "unknown"


# ============================================================================
# CONFIGURATION
# ============================================================================


def _get_rate_limit_config() -> tuple[int, float]:
    """
    Read and sanitize rate-limit configuration.

    Returns:
        (maximum requests, window duration in seconds)
    """

    requests_limit = max(
        int(settings.rate_limit_requests),
        _MIN_REQUESTS,
    )

    window_seconds = max(
        float(settings.rate_limit_window_seconds),
        _MIN_WINDOW_SECONDS,
    )

    return requests_limit, window_seconds


# ============================================================================
# CLEANUP
# ============================================================================


def _cleanup_empty_clients() -> None:
    """
    Remove inactive client buckets.

    This is primarily a safety mechanism for long-running development/demo
    instances.
    """

    if len(_requests) <= _MAX_TRACKED_CLIENTS:
        return

    inactive_clients = [
        client_id
        for client_id, bucket in _requests.items()
        if not bucket.timestamps
    ]

    for client_id in inactive_clients:
        _requests.pop(client_id, None)

        if len(_requests) <= _MAX_TRACKED_CLIENTS:
            break


# ============================================================================
# RATE LIMIT DEPENDENCY
# ============================================================================


async def rate_limit_middleware(
    request: Request,
) -> None:
    """
    Enforce a sliding-window rate limit per client IP.

    Example configuration:

        RATE_LIMIT_REQUESTS=30
        RATE_LIMIT_WINDOW_SECONDS=60

    This means a client can make at most 30 requests within any rolling
    60-second window.

    Raises:
        HTTPException(429): when the configured limit is exceeded.
    """

    client_id = _get_client_identifier(request)

    max_requests, window_seconds = _get_rate_limit_config()

    now = time.monotonic()

    async with _lock:
        bucket = _requests.get(client_id)

        if bucket is None:
            bucket = _ClientBucket(
                timestamps=deque(),
            )

            _requests[client_id] = bucket

        timestamps = bucket.timestamps

        # ------------------------------------------------------------
        # Remove timestamps outside the current sliding window.
        # ------------------------------------------------------------

        cutoff = now - window_seconds

        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        # ------------------------------------------------------------
        # Check limit.
        # ------------------------------------------------------------

        if len(timestamps) >= max_requests:
            retry_after = (
                max(
                    timestamps[0] + window_seconds - now,
                    0.0,
                )
                if timestamps
                else window_seconds
            )

            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                limit=max_requests,
                window_seconds=window_seconds,
                retry_after_seconds=round(retry_after, 2),
                path=request.url.path,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={
                    "Retry-After": str(
                        max(
                            1,
                            int(retry_after + 0.999),
                        )
                    ),
                },
            )

        # ------------------------------------------------------------
        # Record current request.
        # ------------------------------------------------------------

        timestamps.append(now)

        # ------------------------------------------------------------
        # Avoid unbounded client-state growth.
        # ------------------------------------------------------------

        _cleanup_empty_clients()


# ============================================================================
# ADMIN / TEST HELPERS
# ============================================================================


async def reset_rate_limiter() -> None:
    """
    Clear all in-memory rate-limit state.

    Primarily useful for:
    - Automated tests
    - Development
    - Controlled application lifecycle events

    This should never be exposed as a public API endpoint.
    """

    async with _lock:
        _requests.clear()


async def reset_client_rate_limit(
    client_id: str,
) -> None:
    """
    Clear rate-limit state for a single client.

    Useful for tests and controlled internal operations.
    """

    if not client_id:
        return

    async with _lock:
        _requests.pop(client_id, None)


# ============================================================================
# OBSERVABILITY
# ============================================================================


async def get_rate_limiter_stats() -> dict[str, int]:
    """
    Return lightweight internal limiter statistics.

    This function is intended for internal diagnostics and tests.
    """

    async with _lock:
        active_clients = sum(
            1
            for bucket in _requests.values()
            if bucket.timestamps
        )

        tracked_clients = len(_requests)

        active_requests = sum(
            len(bucket.timestamps)
            for bucket in _requests.values()
        )

    return {
        "tracked_clients": tracked_clients,
        "active_clients": active_clients,
        "active_requests": active_requests,
    }


__all__ = [
    "rate_limit_middleware",
    "reset_rate_limiter",
    "reset_client_rate_limit",
    "get_rate_limiter_stats",
]