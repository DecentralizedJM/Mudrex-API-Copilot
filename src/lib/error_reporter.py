"""
Error reporting to Station Master - centralized error analysis service

Copyright (c) 2025 DecentralizedJM
Licensed under MIT License
"""
import os
import logging
import traceback
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import httpx for async requests, fallback to requests
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    try:
        import requests
        HAS_REQUESTS = True
        HAS_HTTPX = False
    except ImportError:
        HAS_HTTPX = False
        HAS_REQUESTS = False


async def report_error(
    error: Exception,
    error_type: str = "exception",
    context: Optional[dict] = None
) -> None:
    """
    Report an error to Station Master.
    
    Args:
        error: The exception that occurred
        error_type: Type of error ("exception", "timeout", "crash", "deploy")
        context: Optional additional context dictionary
        
    This function never raises exceptions - it silently fails if Station Master
    is unreachable to prevent cascading failures.
    """
    url = os.getenv("STATION_MASTER_URL")
    secret = os.getenv("STATION_SECRET")
    
    if not url or not secret:
        return  # Silently skip if not configured
    
    try:
        # Prepare error payload
        payload = {
            "project_name": (
                os.getenv("RAILWAY_PROJECT_NAME") or
                os.getenv("npm_package_name") or
                "mudrex-api-bot"
            ),
            "service_name": (
                os.getenv("RAILWAY_SERVICE_NAME") or
                "telegram-bot"
            ),
            "environment": (
                os.getenv("RAILWAY_ENVIRONMENT") or
                os.getenv("NODE_ENV") or
                os.getenv("ENVIRONMENT") or
                "dev"
            ),
            "error_type": error_type,
            "message": str(error) or type(error).__name__,
            "stack_trace": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        # Add optional context
        if context:
            payload["context"] = context
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Station-Secret": secret,
        }
        
        # Send request (async if httpx available, sync otherwise)
        if HAS_HTTPX:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{url}/ingest/error",
                    json=payload,
                    headers=headers
                )
        elif HAS_REQUESTS:
            requests.post(
                f"{url}/ingest/error",
                json=payload,
                headers=headers,
                timeout=5.0
            )
        else:
            logger.warning("No HTTP client available for error reporting")
            
    except Exception as e:
        # Silent fail - don't crash if Station Master is unreachable
        logger.debug(f"Failed to report error to Station Master: {e}")


def report_error_sync(
    error: Exception,
    error_type: str = "exception",
    context: Optional[dict] = None
) -> None:
    """
    Synchronous version of report_error for use in non-async contexts.
    
    Args:
        error: The exception that occurred
        error_type: Type of error ("exception", "timeout", "crash", "deploy")
        context: Optional additional context dictionary
    """
    url = os.getenv("STATION_MASTER_URL")
    secret = os.getenv("STATION_SECRET")
    
    if not url or not secret:
        return
    
    try:
        payload = {
            "project_name": (
                os.getenv("RAILWAY_PROJECT_NAME") or
                os.getenv("npm_package_name") or
                "mudrex-api-bot"
            ),
            "service_name": (
                os.getenv("RAILWAY_SERVICE_NAME") or
                "telegram-bot"
            ),
            "environment": (
                os.getenv("RAILWAY_ENVIRONMENT") or
                os.getenv("NODE_ENV") or
                os.getenv("ENVIRONMENT") or
                "dev"
            ),
            "error_type": error_type,
            "message": str(error) or type(error).__name__,
            "stack_trace": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        if context:
            payload["context"] = context
        
        headers = {
            "Content-Type": "application/json",
            "X-Station-Secret": secret,
        }
        
        if HAS_REQUESTS:
            requests.post(
                f"{url}/ingest/error",
                json=payload,
                headers=headers,
                timeout=5.0
            )
        else:
            logger.debug("No HTTP client available for error reporting")
            
    except Exception as e:
        logger.debug(f"Failed to report error to Station Master: {e}")


async def fetch_with_timeout(
    url: str,
    timeout_ms: int = 30000,
    **kwargs
):
    """
    Wrapper for fetch/httpx requests with timeout error reporting.
    
    Args:
        url: URL to fetch
        timeout_ms: Timeout in milliseconds
        **kwargs: Additional arguments to pass to httpx/requests
        
    Returns:
        Response object
        
    Raises:
        TimeoutError: If request times out (reported to Station Master)
        Other exceptions: Passed through
    """
    import asyncio
    
    timeout_seconds = timeout_ms / 1000.0
    
    try:
        if HAS_HTTPX:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                return await client.get(url, **kwargs)
        elif HAS_REQUESTS:
            return requests.get(url, timeout=timeout_seconds, **kwargs)
        else:
            raise RuntimeError("No HTTP client available")
            
    except asyncio.TimeoutError:
        error = TimeoutError(f"Request to {url} timed out after {timeout_ms}ms")
        await report_error(error, "timeout", context={"url": url, "timeout_ms": timeout_ms})
        raise
    except Exception as e:
        # Check if it's a timeout error from httpx/requests
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            error = TimeoutError(f"Request to {url} timed out: {e}")
            await report_error(error, "timeout", context={"url": url, "timeout_ms": timeout_ms})
        raise
