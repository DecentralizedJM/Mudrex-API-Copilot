"""
Health Check Server and Endpoints
Provides /health and /metrics endpoints for monitoring

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from .config import config

logger = logging.getLogger(__name__)


# Version info
__version__ = "2.0.0"

# Global references to components (set by main.py)
_rag_pipeline = None
_mcp_client = None
_bot = None


def set_components(rag_pipeline=None, mcp_client=None, bot=None):
    """Set component references for health checks"""
    global _rag_pipeline, _mcp_client, _bot
    _rag_pipeline = rag_pipeline
    _mcp_client = mcp_client
    _bot = bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    logger.info("Health server starting up")
    yield
    logger.info("Health server shutting down")


# Create FastAPI app
app = FastAPI(
    title="Mudrex API Copilot Health",
    description="Health and metrics endpoints for the Mudrex API Copilot",
    version=__version__,
    lifespan=lifespan,
)


async def check_redis() -> Dict[str, Any]:
    """Check Redis connection health"""
    try:
        if _rag_pipeline and _rag_pipeline.cache and _rag_pipeline.cache.connected:
            _rag_pipeline.cache.redis_client.ping()
            stats = _rag_pipeline.cache.get_stats()
            return {
                "healthy": True,
                "hit_rate": stats.get("hit_rate", 0),
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
            }
        elif config.REDIS_ENABLED:
            return {"healthy": False, "error": "Redis enabled but not connected"}
        else:
            return {"healthy": True, "status": "disabled"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_vector_store() -> Dict[str, Any]:
    """Check vector store health"""
    try:
        if _rag_pipeline and _rag_pipeline.vector_store:
            health = _rag_pipeline.vector_store.health_check()
            return health
        return {"healthy": False, "error": "Vector store not initialized"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_gemini() -> Dict[str, Any]:
    """Check Gemini API connectivity"""
    try:
        if _rag_pipeline and _rag_pipeline.gemini_client:
            # Just check if client is initialized (don't make API call)
            return {
                "healthy": True,
                "model": _rag_pipeline.gemini_client.model_name,
            }
        return {"healthy": False, "error": "Gemini client not initialized"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_mcp() -> Dict[str, Any]:
    """Check MCP client health"""
    try:
        if _mcp_client:
            return {
                "healthy": _mcp_client.is_connected(),
                "authenticated": _mcp_client.is_authenticated(),
                "tools_available": len(_mcp_client.get_available_tools()),
            }
        elif config.MCP_ENABLED:
            return {"healthy": False, "error": "MCP enabled but not connected"}
        else:
            return {"healthy": True, "status": "disabled"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def check_telegram() -> Dict[str, Any]:
    """Check Telegram bot health"""
    try:
        if _bot:
            return {
                "healthy": True,
                "status": "running",
            }
        return {"healthy": False, "error": "Bot not initialized"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mudrex API Copilot",
        "version": __version__,
        "status": "running",
        "endpoints": ["/health", "/health/live", "/health/ready", "/metrics"],
    }


@app.get("/health")
async def health():
    """
    Comprehensive health check endpoint.
    Returns status of all components.
    """
    start_time = time.time()
    
    # Run all checks in parallel
    redis_check, vector_check, gemini_check, mcp_check, telegram_check = await asyncio.gather(
        check_redis(),
        check_vector_store(),
        check_gemini(),
        check_mcp(),
        check_telegram(),
        return_exceptions=True,
    )
    
    # Handle exceptions
    def safe_result(result):
        if isinstance(result, Exception):
            return {"healthy": False, "error": str(result)}
        return result
    
    checks = {
        "redis": safe_result(redis_check),
        "vector_store": safe_result(vector_check),
        "gemini": safe_result(gemini_check),
        "mcp": safe_result(mcp_check),
        "telegram": safe_result(telegram_check),
    }
    
    # Determine overall health
    # Core components: vector_store, gemini, telegram
    core_healthy = all(
        checks[c].get("healthy", False)
        for c in ["vector_store", "gemini", "telegram"]
    )
    
    # Optional components: redis, mcp (can be disabled)
    optional_healthy = all(
        checks[c].get("healthy", False) or checks[c].get("status") == "disabled"
        for c in ["redis", "mcp"]
    )
    
    overall_healthy = core_healthy and optional_healthy
    status = "healthy" if overall_healthy else "degraded" if core_healthy else "unhealthy"
    
    response = {
        "status": status,
        "version": __version__,
        "checks": checks,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
    }
    
    status_code = 200 if status in ["healthy", "degraded"] else 503
    return JSONResponse(content=response, status_code=status_code)


@app.get("/health/live")
async def liveness():
    """
    Liveness probe - is the service running?
    Used by Kubernetes/Railway for restart decisions.
    """
    return {"status": "alive", "version": __version__}


@app.get("/health/ready")
async def readiness():
    """
    Readiness probe - is the service ready to accept traffic?
    Used by Kubernetes/Railway for traffic routing.
    """
    # Check core components
    vector_check = await check_vector_store()
    gemini_check = await check_gemini()
    
    ready = (
        vector_check.get("healthy", False) and
        gemini_check.get("healthy", False)
    )
    
    response = {
        "ready": ready,
        "checks": {
            "vector_store": vector_check.get("healthy", False),
            "gemini": gemini_check.get("healthy", False),
        }
    }
    
    status_code = 200 if ready else 503
    return JSONResponse(content=response, status_code=status_code)


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    try:
        from .lib.metrics import generate_metrics
        metrics_output = generate_metrics()
        return Response(content=metrics_output, media_type="text/plain")
    except ImportError:
        # Fallback if metrics module not available
        return Response(
            content="# Metrics not available\n",
            media_type="text/plain"
        )


@app.get("/stats")
async def stats():
    """
    Get service statistics.
    """
    stats = {}
    
    # RAG stats
    if _rag_pipeline:
        try:
            rag_stats = _rag_pipeline.get_stats()
            stats["rag"] = rag_stats
        except Exception as e:
            stats["rag"] = {"error": str(e)}
    
    # Cache stats
    if _rag_pipeline and _rag_pipeline.cache:
        try:
            cache_stats = _rag_pipeline.cache.get_stats()
            stats["cache"] = cache_stats
        except Exception as e:
            stats["cache"] = {"error": str(e)}
    
    return stats


async def start_health_server(host: str = "0.0.0.0", port: int = 8080):
    """Start the health check server"""
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(f"Starting health server on {host}:{port}")
    await server.serve()


def run_health_server(host: str = "0.0.0.0", port: int = 8080):
    """Run health server (blocking)"""
    uvicorn.run(app, host=host, port=port, log_level="warning")
