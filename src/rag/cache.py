"""
Resilient Redis Cache Client for reducing Gemini API token usage
Includes circuit breaker, retry with backoff, connection pooling, and in-memory fallback

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import logging
import hashlib
import json
import time
from typing import Optional, Dict, Any, List
import re

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from circuitbreaker import circuit, CircuitBreakerError
from cachetools import TTLCache

from ..config import config

logger = logging.getLogger(__name__)

# Import metrics (optional)
try:
    from ..lib.metrics import record_cache_hit, record_cache_miss, record_cache_set, record_error
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False


class RedisCache:
    """
    Production-grade Redis cache client with resilience patterns.
    
    Features:
    - Connection pooling (max 10 connections)
    - Circuit breaker (5 failures = open, 30s recovery)
    - Retry with exponential backoff (3 attempts)
    - In-memory fallback cache when Redis unavailable
    - Graceful degradation
    """
    
    # Circuit breaker settings
    CIRCUIT_FAILURE_THRESHOLD = 5
    CIRCUIT_RECOVERY_TIMEOUT = 30
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_MIN_WAIT = 0.1  # seconds
    RETRY_MAX_WAIT = 2.0  # seconds
    
    # Connection pool settings
    POOL_MAX_CONNECTIONS = 10
    SOCKET_TIMEOUT = 2
    SOCKET_CONNECT_TIMEOUT = 2
    
    # Fallback cache settings
    FALLBACK_MAXSIZE = 1000
    FALLBACK_TTL = 300  # 5 minutes
    
    def __init__(self):
        """Initialize Redis cache client with connection pooling and fallback"""
        self.redis_client = None
        self.pool = None
        self.connected = False
        self.stats = {'hits': 0, 'misses': 0, 'fallback_hits': 0, 'errors': 0}
        
        # In-memory fallback cache (TTL cache)
        self.fallback_cache = TTLCache(
            maxsize=self.FALLBACK_MAXSIZE,
            ttl=self.FALLBACK_TTL
        )
        
        if not config.REDIS_ENABLED:
            logger.info("Redis caching disabled - using in-memory fallback only")
            return
        
        if not config.REDIS_URL:
            logger.warning("REDIS_ENABLED=true but REDIS_URL not set. Using in-memory fallback.")
            return
        
        self._init_redis_connection()
    
    def _init_redis_connection(self):
        """Initialize Redis connection with connection pooling"""
        try:
            import redis
            
            # Create connection pool
            self.pool = redis.ConnectionPool.from_url(
                config.REDIS_URL,
                max_connections=self.POOL_MAX_CONNECTIONS,
                decode_responses=True,
                socket_timeout=self.SOCKET_TIMEOUT,
                socket_connect_timeout=self.SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Create Redis client with pool
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info("Redis cache connected successfully with connection pooling")
            
        except ImportError:
            logger.error("redis package not installed. Install with: pip install redis>=5.0.0")
            self.redis_client = None
            self.connected = False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")
            self.redis_client = None
            self.connected = False
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent hashing"""
        if not text:
            return ""
        normalized = text.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized
    
    def _hash_text(self, text: str) -> str:
        """Generate SHA256 hash of normalized text"""
        normalized = self._normalize_text(text)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _hash_doc(self, doc: Dict[str, Any]) -> str:
        """Generate hash for a document"""
        doc_text = doc.get('document', '')[:500]
        return self._hash_text(doc_text)
    
    def _hash_docs(self, docs: List[Dict[str, Any]]) -> str:
        """Generate hash for a list of documents"""
        doc_hashes = [self._hash_doc(doc) for doc in docs]
        combined = "|".join(sorted(doc_hashes))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _hash_context(self, chat_history: Optional[List[Dict[str, str]]] = None,
                      mcp_context: Optional[str] = None) -> str:
        """Generate hash for context"""
        parts = []
        if chat_history:
            recent = chat_history[-2:] if len(chat_history) > 2 else chat_history
            for msg in recent:
                parts.append(f"{msg.get('role', '')}:{msg.get('content', '')[:100]}")
        if mcp_context:
            parts.append(self._hash_text(mcp_context[:200]))
        combined = "|".join(parts) if parts else "no_context"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    @circuit(
        failure_threshold=CIRCUIT_FAILURE_THRESHOLD,
        recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT,
        expected_exception=Exception,
    )
    def _redis_get(self, key: str) -> Optional[str]:
        """Get value from Redis with circuit breaker"""
        if not self.redis_client:
            raise Exception("Redis client not initialized")
        return self.redis_client.get(key)
    
    @circuit(
        failure_threshold=CIRCUIT_FAILURE_THRESHOLD,
        recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT,
        expected_exception=Exception,
    )
    def _redis_setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value in Redis with circuit breaker"""
        if not self.redis_client:
            raise Exception("Redis client not initialized")
        self.redis_client.setex(key, ttl, value)
        return True
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=0.5, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _get_with_retry(self, key: str) -> Optional[str]:
        """Get value with retry logic"""
        return self._redis_get(key)
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=0.5, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _set_with_retry(self, key: str, ttl: int, value: str) -> bool:
        """Set value with retry logic"""
        return self._redis_setex(key, ttl, value)
    
    def _get(self, key: str) -> Optional[str]:
        """Get value with full resilience (circuit breaker + retry + fallback)"""
        # Try fallback cache first for speed
        fallback_value = self.fallback_cache.get(key)
        if fallback_value is not None:
            self.stats['fallback_hits'] += 1
            return fallback_value
        
        if not self.connected or not self.redis_client:
            self.stats['misses'] += 1
            return None
        
        try:
            value = self._get_with_retry(key)
            if value is not None:
                self.stats['hits'] += 1
                # Populate fallback cache
                self.fallback_cache[key] = value
                if HAS_METRICS:
                    record_cache_hit()
            else:
                self.stats['misses'] += 1
                if HAS_METRICS:
                    record_cache_miss()
            return value
            
        except CircuitBreakerError:
            logger.warning("Redis circuit breaker is OPEN - using fallback cache")
            self.stats['errors'] += 1
            if HAS_METRICS:
                record_error("cache", "circuit_breaker_open")
            return None
            
        except Exception as e:
            logger.warning(f"Redis get error for key {key[:50]}: {e}")
            self.stats['errors'] += 1
            self.stats['misses'] += 1
            if HAS_METRICS:
                record_error("cache", type(e).__name__)
            return None
    
    def _set(self, key: str, value: str, ttl: int) -> bool:
        """Set value with full resilience"""
        # Always set in fallback cache
        try:
            self.fallback_cache[key] = value
        except Exception:
            pass  # Fallback cache full
        
        if not self.connected or not self.redis_client:
            return False
        
        try:
            result = self._set_with_retry(key, ttl, value)
            if HAS_METRICS:
                record_cache_set()
            return result
            
        except CircuitBreakerError:
            logger.debug("Redis circuit breaker is OPEN - value stored in fallback only")
            return False
            
        except Exception as e:
            logger.warning(f"Redis set error for key {key[:50]}: {e}")
            self.stats['errors'] += 1
            if HAS_METRICS:
                record_error("cache", type(e).__name__)
            return False
    
    # ==================== Response Caching ====================
    
    def get_response(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None,
                     mcp_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached response for query"""
        query_hash = self._hash_text(query)
        context_hash = self._hash_context(chat_history, mcp_context)
        key = f"response:{query_hash}:{context_hash}"
        
        cached = self._get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse cached response for {key}")
        return None
    
    def set_response(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None,
                     mcp_context: Optional[str] = None, result: Dict[str, Any] = None,
                     ttl: Optional[int] = None):
        """Cache response for query"""
        if not result:
            return
        
        query_hash = self._hash_text(query)
        context_hash = self._hash_context(chat_history, mcp_context)
        key = f"response:{query_hash}:{context_hash}"
        
        try:
            value = json.dumps(result)
            ttl = ttl or config.REDIS_TTL_RESPONSE
            self._set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")
    
    # ==================== Validation Caching ====================
    
    def get_validation(self, query: str, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached validation result"""
        query_hash = self._hash_text(query)
        doc_hash = self._hash_doc(doc)
        key = f"relevancy:{query_hash}:{doc_hash}"
        
        cached = self._get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_validation(self, query: str, doc: Dict[str, Any], result: Dict[str, Any],
                       ttl: Optional[int] = None):
        """Cache validation result"""
        query_hash = self._hash_text(query)
        doc_hash = self._hash_doc(doc)
        key = f"relevancy:{query_hash}:{doc_hash}"
        
        try:
            value = json.dumps(result)
            ttl = ttl or config.REDIS_TTL_VALIDATION
            self._set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Failed to cache validation: {e}")
    
    # ==================== Reranking Caching ====================
    
    def get_rerank(self, query: str, documents: List[Dict[str, Any]]) -> Optional[List[int]]:
        """Get cached reranking indices"""
        query_hash = self._hash_text(query)
        docs_hash = self._hash_docs(documents)
        key = f"rerank:{query_hash}:{docs_hash}"
        
        cached = self._get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_rerank(self, query: str, documents: List[Dict[str, Any]], indices: List[int],
                   ttl: Optional[int] = None):
        """Cache reranking indices"""
        query_hash = self._hash_text(query)
        docs_hash = self._hash_docs(documents)
        key = f"rerank:{query_hash}:{docs_hash}"
        
        try:
            value = json.dumps(indices)
            ttl = ttl or config.REDIS_TTL_RERANK
            self._set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Failed to cache rerank: {e}")
    
    # ==================== Query Transform Caching ====================
    
    def get_transform(self, query: str) -> Optional[str]:
        """Get cached transformed query"""
        query_hash = self._hash_text(query)
        key = f"transform:{query_hash}"
        return self._get(key)
    
    def set_transform(self, query: str, transformed: str, ttl: Optional[int] = None):
        """Cache transformed query"""
        query_hash = self._hash_text(query)
        key = f"transform:{query_hash}"
        ttl = ttl or config.REDIS_TTL_TRANSFORM
        self._set(key, transformed, ttl)
    
    # ==================== Embedding Caching ====================
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        text_hash = self._hash_text(text)
        key = f"embedding:{text_hash}"
        
        cached = self._get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None):
        """Cache embedding"""
        text_hash = self._hash_text(text)
        key = f"embedding:{text_hash}"
        
        try:
            value = json.dumps(embedding)
            ttl = ttl or config.REDIS_TTL_EMBEDDING
            self._set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0.0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'fallback_hits': self.stats['fallback_hits'],
            'errors': self.stats['errors'],
            'hit_rate': hit_rate,
            'connected': self.connected,
            'enabled': config.REDIS_ENABLED,
            'fallback_size': len(self.fallback_cache),
            'fallback_maxsize': self.FALLBACK_MAXSIZE,
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health"""
        if not config.REDIS_ENABLED:
            return {"healthy": True, "status": "disabled", "fallback_active": True}
        
        if not self.connected:
            return {
                "healthy": True,  # Degraded but functional
                "status": "fallback_only",
                "fallback_active": True,
                "fallback_size": len(self.fallback_cache),
            }
        
        try:
            self.redis_client.ping()
            return {
                "healthy": True,
                "status": "connected",
                "fallback_active": False,
                **self.get_stats(),
            }
        except Exception as e:
            return {
                "healthy": True,  # Degraded but functional
                "status": "degraded",
                "error": str(e),
                "fallback_active": True,
            }
