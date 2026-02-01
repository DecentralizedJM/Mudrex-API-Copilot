"""
Pytest Configuration and Shared Fixtures
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ==================== Configuration Fixtures ====================

@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    config = MagicMock()
    config.TELEGRAM_BOT_TOKEN = "test_token"
    config.GEMINI_API_KEY = "test_gemini_key"
    config.QDRANT_URL = ""  # Empty to use pickle fallback
    config.QDRANT_API_KEY = ""
    config.QDRANT_COLLECTION_NAME = "test_collection"
    config.QDRANT_VECTOR_SIZE = 768
    config.CHROMA_PERSIST_DIR = "./test_data/chroma"
    config.EMBEDDING_MODEL = "models/gemini-embedding-001"
    config.TOP_K_RESULTS = 5
    config.SIMILARITY_THRESHOLD = 0.55
    config.CONTEXT_SEARCH_THRESHOLD = 0.30
    config.REDIS_ENABLED = False
    config.REDIS_URL = ""
    config.REDIS_TTL_RESPONSE = 86400
    config.REDIS_TTL_EMBEDDING = 2592000
    config.GEMINI_MODEL = "gemini-3-flash-preview"
    config.MAX_ITERATIVE_RETRIEVAL = 2
    config.RELEVANCY_THRESHOLD = 0.6
    config.RERANK_TOP_K = 5
    return config


@pytest.fixture
def mock_redis_config(mock_config):
    """Mock configuration with Redis enabled"""
    mock_config.REDIS_ENABLED = True
    mock_config.REDIS_URL = "redis://localhost:6379"
    return mock_config


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_documents() -> List[str]:
    """Sample documents for testing"""
    return [
        "The Mudrex API uses X-Authentication header for authentication. No HMAC or signing required.",
        "To place a market order, use POST /fapi/v1/order with symbol, side, and quantity parameters.",
        "GET /fapi/v1/positions returns all open positions for the authenticated user.",
        "Rate limits are 2 requests per second. Exceeding this will result in HTTP 429 errors.",
        "The base URL for all API calls is https://trade.mudrex.com/fapi/v1",
    ]


@pytest.fixture
def sample_metadatas() -> List[Dict[str, Any]]:
    """Sample metadata for documents"""
    return [
        {"filename": "authentication.md", "section": "headers"},
        {"filename": "orders.md", "section": "market_order"},
        {"filename": "positions.md", "section": "get_positions"},
        {"filename": "rate_limits.md", "section": "limits"},
        {"filename": "getting_started.md", "section": "base_url"},
    ]


@pytest.fixture
def sample_embeddings() -> List[List[float]]:
    """Sample embeddings (768-dimensional mock vectors)"""
    import numpy as np
    np.random.seed(42)  # For reproducibility
    return [np.random.rand(768).tolist() for _ in range(5)]


@pytest.fixture
def sample_query() -> str:
    """Sample query for testing"""
    return "How do I authenticate with the Mudrex API?"


@pytest.fixture
def sample_query_embedding() -> List[float]:
    """Sample query embedding"""
    import numpy as np
    np.random.seed(43)
    return np.random.rand(768).tolist()


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client"""
    mock = MagicMock()
    mock.models = MagicMock()
    
    # Mock embedding response
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 768
    mock_embed_result = MagicMock()
    mock_embed_result.embeddings = [mock_embedding]
    mock.models.embed_content.return_value = mock_embed_result
    
    # Mock generate_content response
    mock_response = MagicMock()
    mock_response.text = "This is a test response from Gemini."
    mock.models.generate_content.return_value = mock_response
    
    return mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    mock = MagicMock()
    
    # Mock collection info
    mock_collection = MagicMock()
    mock_collection.points_count = 100
    mock_collection.status = "green"
    mock.get_collection.return_value = mock_collection
    
    # Mock collections list
    mock_collections = MagicMock()
    mock_collections.collections = []
    mock.get_collections.return_value = mock_collections
    
    # Mock search results
    mock_result = MagicMock()
    mock_result.score = 0.85
    mock_result.payload = {
        "document": "Test document",
        "filename": "test.md"
    }
    mock.search.return_value = [mock_result]
    
    return mock


# ==================== Temporary Directory Fixtures ====================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for tests"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    chroma_dir = data_dir / "chroma"
    chroma_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_docs_dir(tmp_path):
    """Temporary docs directory with sample files"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    # Create sample doc files
    (docs_dir / "authentication.md").write_text(
        "# Authentication\nUse X-Authentication header with your API secret."
    )
    (docs_dir / "orders.md").write_text(
        "# Orders\nPOST /fapi/v1/order to place orders."
    )
    
    return docs_dir


# ==================== Environment Fixtures ====================

@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment before each test"""
    # Store original env
    original_env = os.environ.copy()
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def set_test_env():
    """Set test environment variables"""
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
    os.environ["GEMINI_API_KEY"] = "test_key"
    os.environ["REDIS_ENABLED"] = "false"
    os.environ["QDRANT_URL"] = ""
