"""
Prometheus Metrics for Mudrex API Copilot
Tracks query performance, cache efficiency, and system health

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import time
from functools import wraps
from typing import Callable, Any

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)

# Create a custom registry to avoid conflicts
REGISTRY = CollectorRegistry()

# ==================== Counters ====================

# Query counters
QUERIES_TOTAL = Counter(
    'mudrex_bot_queries_total',
    'Total number of queries processed',
    ['status', 'domain'],
    registry=REGISTRY,
)

# Cache counters
CACHE_OPERATIONS = Counter(
    'mudrex_bot_cache_operations_total',
    'Total cache operations',
    ['operation', 'result'],  # operation: get/set, result: hit/miss
    registry=REGISTRY,
)

# Error counters
ERRORS_TOTAL = Counter(
    'mudrex_bot_errors_total',
    'Total errors encountered',
    ['component', 'error_type'],
    registry=REGISTRY,
)

# Embedding counters
EMBEDDINGS_TOTAL = Counter(
    'mudrex_bot_embeddings_total',
    'Total embedding operations',
    ['source'],  # source: cache/api
    registry=REGISTRY,
)


# ==================== Histograms ====================

# Query latency
QUERY_LATENCY = Histogram(
    'mudrex_bot_query_latency_seconds',
    'Query processing latency in seconds',
    ['domain'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=REGISTRY,
)

# Embedding latency
EMBEDDING_LATENCY = Histogram(
    'mudrex_bot_embedding_latency_seconds',
    'Embedding generation latency in seconds',
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=REGISTRY,
)

# LLM call latency
LLM_LATENCY = Histogram(
    'mudrex_bot_llm_latency_seconds',
    'LLM API call latency in seconds',
    ['operation'],  # operation: generate/validate/rerank/transform
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=REGISTRY,
)

# Document retrieval
RETRIEVAL_LATENCY = Histogram(
    'mudrex_bot_retrieval_latency_seconds',
    'Document retrieval latency in seconds',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY,
)


# ==================== Gauges ====================

# Document count
DOCUMENTS_COUNT = Gauge(
    'mudrex_bot_documents_total',
    'Total documents in vector store',
    registry=REGISTRY,
)

# Active queries
ACTIVE_QUERIES = Gauge(
    'mudrex_bot_active_queries',
    'Number of queries currently being processed',
    registry=REGISTRY,
)

# Cache hit rate
CACHE_HIT_RATE = Gauge(
    'mudrex_bot_cache_hit_rate',
    'Current cache hit rate percentage',
    registry=REGISTRY,
)


# ==================== Info ====================

# Service info
SERVICE_INFO = Info(
    'mudrex_bot',
    'Information about the Mudrex API Copilot service',
    registry=REGISTRY,
)


# ==================== Helper Functions ====================

def init_service_info(version: str, model: str, environment: str = "production"):
    """Initialize service info metric"""
    SERVICE_INFO.info({
        'version': version,
        'model': model,
        'environment': environment,
    })


def track_query(domain: str = "unknown"):
    """Decorator to track query metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ACTIVE_QUERIES.inc()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                ERRORS_TOTAL.labels(component="query", error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                QUERY_LATENCY.labels(domain=domain).observe(duration)
                QUERIES_TOTAL.labels(status=status, domain=domain).inc()
                ACTIVE_QUERIES.dec()
        
        return wrapper
    return decorator


def track_llm_call(operation: str):
    """Decorator to track LLM call metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                ERRORS_TOTAL.labels(component="llm", error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                LLM_LATENCY.labels(operation=operation).observe(duration)
        
        return wrapper
    return decorator


def track_embedding():
    """Decorator to track embedding metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                EMBEDDING_LATENCY.observe(duration)
        
        return wrapper
    return decorator


def record_cache_hit():
    """Record a cache hit"""
    CACHE_OPERATIONS.labels(operation="get", result="hit").inc()


def record_cache_miss():
    """Record a cache miss"""
    CACHE_OPERATIONS.labels(operation="get", result="miss").inc()


def record_cache_set():
    """Record a cache set operation"""
    CACHE_OPERATIONS.labels(operation="set", result="success").inc()


def record_embedding(source: str = "api"):
    """Record an embedding operation"""
    EMBEDDINGS_TOTAL.labels(source=source).inc()


def update_documents_count(count: int):
    """Update document count gauge"""
    DOCUMENTS_COUNT.set(count)


def update_cache_hit_rate(hit_rate: float):
    """Update cache hit rate gauge"""
    CACHE_HIT_RATE.set(hit_rate)


def record_error(component: str, error_type: str):
    """Record an error"""
    ERRORS_TOTAL.labels(component=component, error_type=error_type).inc()


def generate_metrics() -> str:
    """Generate Prometheus metrics output"""
    return generate_latest(REGISTRY).decode('utf-8')


# ==================== Context Managers ====================

class QueryTimer:
    """Context manager for timing queries"""
    
    def __init__(self, domain: str = "unknown"):
        self.domain = domain
        self.start_time = None
    
    def __enter__(self):
        ACTIVE_QUERIES.inc()
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        QUERY_LATENCY.labels(domain=self.domain).observe(duration)
        
        status = "error" if exc_type else "success"
        QUERIES_TOTAL.labels(status=status, domain=self.domain).inc()
        
        if exc_type:
            ERRORS_TOTAL.labels(
                component="query",
                error_type=exc_type.__name__
            ).inc()
        
        ACTIVE_QUERIES.dec()
        return False  # Don't suppress exceptions


class LLMTimer:
    """Context manager for timing LLM calls"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        LLM_LATENCY.labels(operation=self.operation).observe(duration)
        
        if exc_type:
            ERRORS_TOTAL.labels(
                component="llm",
                error_type=exc_type.__name__
            ).inc()
        
        return False
