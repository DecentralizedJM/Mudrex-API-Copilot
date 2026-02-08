"""
Semantic Cache - Cache responses for semantically similar queries
Reduces LLM costs by returning cached responses for similar questions

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import hashlib
import json
import logging
import time
from typing import Optional, Dict, Any, List, Tuple

from google import genai
from google.genai.errors import ClientError
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..config import config

logger = logging.getLogger(__name__)

# Import cache (avoid circular import)
try:
    from .cache import RedisCache
except ImportError:
    RedisCache = None


class SemanticCache:
    """
    Query-level semantic cache that returns cached responses for similar queries.
    
    Features:
    - Embeds queries and stores in Redis
    - Finds semantically similar past queries (>95% similarity)
    - Returns cached response if similar query exists
    - Dramatically reduces repeat/similar queries
    
    Cost savings:
    - Queries like "how to authenticate" and "authentication guide" can share a response
    - Typo variations ("authnetication" vs "authentication") can share a response
    """
    
    # Similarity threshold for considering queries equivalent
    SIMILARITY_THRESHOLD = 0.95
    
    # Maximum cached queries to search through
    MAX_CACHED_QUERIES = 1000
    
    # Cache TTL (24 hours default)
    CACHE_TTL = 86400
    
    def __init__(self):
        """Initialize semantic cache"""
        # Set API key
        if config.GEMINI_API_KEY:
            import os
            os.environ['GEMINI_API_KEY'] = config.GEMINI_API_KEY
        
        self.client = genai.Client()
        self.embedding_model = config.EMBEDDING_MODEL
        
        # Initialize Redis cache
        self.cache = RedisCache() if (config.REDIS_ENABLED and RedisCache) else None
        
        # In-memory fallback
        self.memory_cache: Dict[str, Dict[str, Any]] = {}  # query_hash -> {embedding, response, timestamp}
        
        # Stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'semantic_hits': 0,  # Similar but not exact
        }
        
        logger.info("SemanticCache initialized")
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text"""
        if not text:
            return None
        
        # Check embedding cache first
        if self.cache:
            cached = self.cache.get_embedding(text)
            if cached:
                return cached
        
        try:
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
            )
            embedding = result.embeddings[0].values
            if self.cache:
                self.cache.set_embedding(text, embedding)
            return embedding
        except ClientError as e:
            if (getattr(e, "status_code", None) == 404 or "NOT_FOUND" in str(e)) and self.embedding_model != "models/gemini-embedding-001":
                logger.warning(
                    "Embedding model %s not found. Using fallback models/gemini-embedding-001.",
                    self.embedding_model,
                )
                result = self.client.models.embed_content(
                    model="models/gemini-embedding-001",
                    contents=text,
                )
                embedding = result.embeddings[0].values
                if self.cache:
                    self.cache.set_embedding(text, embedding)
                return embedding
            raise
        except Exception as e:
            logger.warning(f"Error getting embedding: {e}")
            return None
    
    def _query_hash(self, query: str) -> str:
        """Generate hash for a query"""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            vec1 = np.array(emb1).reshape(1, -1)
            vec2 = np.array(emb2).reshape(1, -1)
            return float(cosine_similarity(vec1, vec2)[0][0])
        except Exception:
            return 0.0
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if a semantically similar query exists in cache.
        
        Args:
            query: The user's query
            
        Returns:
            Cached response if found, None otherwise
        """
        query_hash = self._query_hash(query)
        
        # 1. Check exact match first (fast path)
        exact_match = self._get_exact(query_hash)
        if exact_match:
            self.stats['hits'] += 1
            logger.info(f"Semantic cache exact hit for query: {query[:50]}...")
            return exact_match
        
        # 2. Get embedding for semantic search
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            self.stats['misses'] += 1
            return None
        
        # 3. Search for semantically similar queries
        similar = self._find_similar(query_embedding)
        if similar:
            self.stats['semantic_hits'] += 1
            logger.info(f"Semantic cache similarity hit ({similar['similarity']:.2%}) for query: {query[:50]}...")
            return similar['response']
        
        self.stats['misses'] += 1
        return None
    
    def _get_exact(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get exact match from cache"""
        # Check Redis
        if self.cache and self.cache.connected:
            try:
                key = f"semantic_cache:{query_hash}"
                cached = self.cache._get(key)
                if cached:
                    data = json.loads(cached)
                    return data.get('response')
            except Exception:
                pass
        
        # Check memory fallback
        if query_hash in self.memory_cache:
            entry = self.memory_cache[query_hash]
            # Check if not expired
            if time.time() - entry.get('timestamp', 0) < self.CACHE_TTL:
                return entry.get('response')
        
        return None
    
    def _find_similar(self, query_embedding: List[float]) -> Optional[Dict[str, Any]]:
        """Find semantically similar cached query"""
        best_match = None
        best_similarity = 0.0
        
        # Get all cached query embeddings
        cached_entries = self._get_all_cached_embeddings()
        
        for entry in cached_entries:
            cached_embedding = entry.get('embedding')
            if not cached_embedding:
                continue
            
            similarity = self._compute_similarity(query_embedding, cached_embedding)
            
            if similarity >= self.SIMILARITY_THRESHOLD and similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'response': entry.get('response'),
                    'similarity': similarity,
                    'original_query': entry.get('query'),
                }
        
        return best_match
    
    def _get_all_cached_embeddings(self) -> List[Dict[str, Any]]:
        """Get all cached query embeddings for similarity search"""
        entries = []
        
        # From Redis
        if self.cache and self.cache.connected:
            try:
                # Get all semantic cache keys
                keys = self.cache.redis_client.keys("semantic_cache:*")
                for key in keys[:self.MAX_CACHED_QUERIES]:
                    cached = self.cache._get(key)
                    if cached:
                        try:
                            entries.append(json.loads(cached))
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.debug(f"Error getting cached embeddings from Redis: {e}")
        
        # From memory fallback
        for query_hash, entry in list(self.memory_cache.items())[:self.MAX_CACHED_QUERIES]:
            if time.time() - entry.get('timestamp', 0) < self.CACHE_TTL:
                if entry not in entries:
                    entries.append(entry)
        
        return entries
    
    def set(self, query: str, response: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache a query and its response.
        
        Args:
            query: The user's query
            response: The response to cache
            ttl: Optional TTL override
        """
        query_hash = self._query_hash(query)
        query_embedding = self._get_embedding(query)
        
        if not query_embedding:
            logger.warning("Could not generate embedding for caching")
            return
        
        entry = {
            'query': query,
            'query_hash': query_hash,
            'embedding': query_embedding,
            'response': response,
            'timestamp': time.time(),
        }
        
        ttl = ttl or self.CACHE_TTL
        
        # Store in Redis
        if self.cache and self.cache.connected:
            try:
                key = f"semantic_cache:{query_hash}"
                self.cache._set(key, json.dumps(entry), ttl)
                logger.debug(f"Cached response for query: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Error caching to Redis: {e}")
        
        # Store in memory fallback
        self.memory_cache[query_hash] = entry
        
        # Trim memory cache if too large
        if len(self.memory_cache) > self.MAX_CACHED_QUERIES:
            # Remove oldest entries
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].get('timestamp', 0)
            )
            for key, _ in sorted_entries[:-self.MAX_CACHED_QUERIES]:
                del self.memory_cache[key]
    
    def invalidate(self, query: str):
        """Invalidate cache for a specific query"""
        query_hash = self._query_hash(query)
        
        # Remove from Redis
        if self.cache and self.cache.connected:
            try:
                key = f"semantic_cache:{query_hash}"
                self.cache.redis_client.delete(key)
            except Exception:
                pass
        
        # Remove from memory
        if query_hash in self.memory_cache:
            del self.memory_cache[query_hash]
    
    def clear(self):
        """Clear all cached entries"""
        # Clear Redis
        if self.cache and self.cache.connected:
            try:
                keys = self.cache.redis_client.keys("semantic_cache:*")
                if keys:
                    self.cache.redis_client.delete(*keys)
            except Exception:
                pass
        
        # Clear memory
        self.memory_cache.clear()
        
        # Reset stats
        self.stats = {'hits': 0, 'misses': 0, 'semantic_hits': 0}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = ((self.stats['hits'] + self.stats['semantic_hits']) / total * 100) if total > 0 else 0.0
        
        return {
            'exact_hits': self.stats['hits'],
            'semantic_hits': self.stats['semantic_hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'cached_queries': len(self.memory_cache),
            'similarity_threshold': self.SIMILARITY_THRESHOLD,
        }
