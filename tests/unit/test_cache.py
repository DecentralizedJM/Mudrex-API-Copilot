"""
Unit tests for Redis Cache
"""
import json
from unittest.mock import MagicMock, patch
import pytest


class TestRedisCache:
    """Tests for RedisCache class"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.setex.return_value = True
        return mock
    
    @pytest.fixture
    def cache_with_mock_redis(self, mock_redis, mock_config):
        """Create cache instance with mocked Redis"""
        with patch('src.rag.cache.config', mock_config):
            mock_config.REDIS_ENABLED = True
            mock_config.REDIS_URL = "redis://localhost:6379"
            
            with patch('src.rag.cache.redis') as mock_redis_module:
                mock_redis_module.from_url.return_value = mock_redis
                
                from src.rag.cache import RedisCache
                cache = RedisCache()
                cache.redis_client = mock_redis
                cache.connected = True
                return cache
    
    @pytest.mark.unit
    def test_normalize_text(self, cache_with_mock_redis):
        """Test text normalization for caching"""
        cache = cache_with_mock_redis
        
        # Test basic normalization
        assert cache._normalize_text("Hello World") == "hello world"
        assert cache._normalize_text("  Multiple   Spaces  ") == "multiple spaces"
        assert cache._normalize_text("Punctuation! Here?") == "punctuation here"
        assert cache._normalize_text("") == ""
        assert cache._normalize_text(None) == ""
    
    @pytest.mark.unit
    def test_hash_text(self, cache_with_mock_redis):
        """Test text hashing"""
        cache = cache_with_mock_redis
        
        # Same text should produce same hash
        hash1 = cache._hash_text("test query")
        hash2 = cache._hash_text("test query")
        assert hash1 == hash2
        
        # Different text should produce different hash
        hash3 = cache._hash_text("different query")
        assert hash1 != hash3
        
        # Hash should be 16 characters
        assert len(hash1) == 16
    
    @pytest.mark.unit
    def test_get_response_cache_miss(self, cache_with_mock_redis, mock_redis):
        """Test cache miss returns None"""
        cache = cache_with_mock_redis
        mock_redis.get.return_value = None
        
        result = cache.get_response("test query")
        assert result is None
        assert cache.stats['misses'] == 1
    
    @pytest.mark.unit
    def test_get_response_cache_hit(self, cache_with_mock_redis, mock_redis):
        """Test cache hit returns cached value"""
        cache = cache_with_mock_redis
        
        cached_response = {
            "answer": "Test answer",
            "sources": [{"filename": "test.md"}]
        }
        mock_redis.get.return_value = json.dumps(cached_response)
        
        result = cache.get_response("test query")
        assert result == cached_response
        assert cache.stats['hits'] == 1
    
    @pytest.mark.unit
    def test_set_response(self, cache_with_mock_redis, mock_redis, mock_config):
        """Test setting response in cache"""
        cache = cache_with_mock_redis
        
        response = {"answer": "Test answer"}
        cache.set_response("test query", result=response)
        
        # Verify setex was called
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.unit
    def test_get_embedding_cache_miss(self, cache_with_mock_redis, mock_redis):
        """Test embedding cache miss"""
        cache = cache_with_mock_redis
        mock_redis.get.return_value = None
        
        result = cache.get_embedding("test text")
        assert result is None
    
    @pytest.mark.unit
    def test_get_embedding_cache_hit(self, cache_with_mock_redis, mock_redis):
        """Test embedding cache hit"""
        cache = cache_with_mock_redis
        
        embedding = [0.1, 0.2, 0.3]
        mock_redis.get.return_value = json.dumps(embedding)
        
        result = cache.get_embedding("test text")
        assert result == embedding
    
    @pytest.mark.unit
    def test_set_embedding(self, cache_with_mock_redis, mock_redis):
        """Test setting embedding in cache"""
        cache = cache_with_mock_redis
        
        embedding = [0.1, 0.2, 0.3]
        cache.set_embedding("test text", embedding)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.unit
    def test_get_stats(self, cache_with_mock_redis):
        """Test cache statistics"""
        cache = cache_with_mock_redis
        cache.stats = {'hits': 10, 'misses': 5}
        
        stats = cache.get_stats()
        assert stats['hits'] == 10
        assert stats['misses'] == 5
        assert stats['hit_rate'] == pytest.approx(66.67, rel=0.1)


class TestRedisCacheDisabled:
    """Tests for cache when Redis is disabled"""
    
    @pytest.mark.unit
    def test_cache_disabled(self, mock_config):
        """Test cache gracefully handles disabled state"""
        with patch('src.rag.cache.config', mock_config):
            mock_config.REDIS_ENABLED = False
            
            from src.rag.cache import RedisCache
            cache = RedisCache()
            
            assert cache.connected is False
            assert cache.get_response("test") is None
            assert cache.get_embedding("test") is None
