"""
Unit tests for Vector Store
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import numpy as np


class TestVectorStorePickleFallback:
    """Tests for VectorStore pickle fallback mode"""
    
    @pytest.fixture
    def vector_store(self, tmp_path, mock_config, mock_gemini_client):
        """Create VectorStore with pickle fallback"""
        mock_config.QDRANT_URL = ""
        mock_config.QDRANT_API_KEY = ""
        mock_config.CHROMA_PERSIST_DIR = str(tmp_path / "chroma")
        with patch('src.config.settings.config', mock_config):
            import src.rag.vector_store as vs_mod
            with patch.object(vs_mod, 'config', mock_config):
                with patch('src.rag.vector_store.genai') as mock_genai:
                    mock_genai.Client.return_value = mock_gemini_client
                    from src.rag.vector_store import VectorStore
                    store = VectorStore()
                    return store
    
    @pytest.mark.unit
    def test_init_pickle_fallback(self, vector_store):
        """Test initialization with pickle fallback"""
        assert vector_store.use_qdrant is False
        assert vector_store.documents == []
        assert vector_store.embeddings == []
    
    @pytest.mark.unit
    def test_add_documents(self, vector_store, sample_documents, sample_metadatas):
        """Test adding documents"""
        vector_store.add_documents(
            documents=sample_documents[:2],
            metadatas=sample_metadatas[:2]
        )
        
        assert len(vector_store.documents) == 2
        assert len(vector_store.embeddings) == 2
        assert len(vector_store.metadatas) == 2
    
    @pytest.mark.unit
    def test_add_documents_empty(self, vector_store):
        """Test adding empty document list"""
        vector_store.add_documents(documents=[])
        assert len(vector_store.documents) == 0
    
    @pytest.mark.unit
    def test_search(self, vector_store, sample_documents, sample_metadatas):
        """Test document search"""
        # Add documents
        vector_store.documents = sample_documents[:2]
        vector_store.metadatas = sample_metadatas[:2]
        vector_store.embeddings = [np.random.rand(768).tolist() for _ in range(2)]
        
        # Search
        results = vector_store.search("authentication", top_k=2)
        
        assert isinstance(results, list)
    
    @pytest.mark.unit
    def test_search_empty_store(self, vector_store):
        """Test search with no documents"""
        results = vector_store.search("test query")
        assert results == []
    
    @pytest.mark.unit
    def test_clear(self, vector_store, sample_documents):
        """Test clearing the store"""
        vector_store.documents = sample_documents[:2]
        vector_store.embeddings = [[0.1] * 768, [0.2] * 768]
        vector_store.metadatas = [{}, {}]
        vector_store.ids = ["id1", "id2"]
        
        vector_store.clear()
        
        assert vector_store.documents == []
        assert vector_store.embeddings == []
        assert vector_store.metadatas == []
        assert vector_store.ids == []
    
    @pytest.mark.unit
    def test_get_count(self, vector_store, sample_documents):
        """Test document count"""
        assert vector_store.get_count() == 0
        
        vector_store.documents = sample_documents[:3]
        assert vector_store.get_count() == 3
    
    @pytest.mark.unit
    def test_health_check_pickle(self, vector_store):
        """Test health check returns pickle status"""
        health = vector_store.health_check()
        
        assert health["healthy"] is True
        assert health["backend"] == "pickle"
        assert "warning" in health


class TestVectorStoreQdrant:
    """Tests for VectorStore with Qdrant backend"""
    
    @pytest.fixture
    def vector_store_qdrant(self, tmp_path, mock_config, mock_gemini_client, mock_qdrant_client):
        """Create VectorStore with Qdrant (mock QdrantClient; qdrant-client may not be installed)"""
        mock_config.QDRANT_URL = "https://test.qdrant.io"
        mock_config.QDRANT_API_KEY = "test_api_key"
        mock_config.QDRANT_COLLECTION_NAME = "test_collection"
        mock_config.QDRANT_VECTOR_SIZE = 768
        with patch('src.config.settings.config', mock_config):
            import src.rag.vector_store as vs_mod
            with patch.object(vs_mod, 'config', mock_config):
                with patch.object(vs_mod, 'HAS_QDRANT', True):  # force Qdrant path when lib not installed
                    with patch('src.rag.vector_store.genai') as mock_genai:
                        mock_genai.Client.return_value = mock_gemini_client
                        with patch('src.rag.vector_store.QdrantClient') as mock_qdrant_cls:
                            mock_qdrant_cls.return_value = mock_qdrant_client
                            from src.rag.vector_store import VectorStore
                            store = VectorStore()
                            return store
    
    @pytest.mark.unit
    def test_init_qdrant(self, vector_store_qdrant):
        """Test initialization with Qdrant"""
        assert vector_store_qdrant.use_qdrant is True
    
    @pytest.mark.unit
    def test_search_qdrant(self, vector_store_qdrant, mock_qdrant_client):
        """Test search with Qdrant backend"""
        # Mock search results
        mock_result = MagicMock()
        mock_result.score = 0.85
        mock_result.payload = {
            "document": "Test document about authentication",
            "filename": "auth.md"
        }
        # query_points is tried first; set up its return value
        mock_qp_result = MagicMock()
        mock_qp_result.points = [mock_result]
        mock_qdrant_client.query_points.return_value = mock_qp_result
        mock_qdrant_client.search.return_value = [mock_result]
        vector_store_qdrant.client = mock_qdrant_client
        
        results = vector_store_qdrant.search("authentication")
        
        assert len(results) == 1
        assert results[0]["document"] == "Test document about authentication"
        assert results[0]["similarity"] == 0.85
    
    @pytest.mark.unit
    def test_health_check_qdrant(self, vector_store_qdrant, mock_qdrant_client):
        """Test health check with Qdrant"""
        vector_store_qdrant.client = mock_qdrant_client
        
        health = vector_store_qdrant.health_check()
        
        assert health["healthy"] is True
        assert health["backend"] == "qdrant"
        assert health["document_count"] == 100


class TestEmbeddings:
    """Tests for embedding functionality"""
    
    @pytest.fixture
    def vector_store(self, tmp_path, mock_config, mock_gemini_client):
        """Create VectorStore for embedding tests"""
        mock_config.QDRANT_URL = ""
        mock_config.QDRANT_API_KEY = ""
        mock_config.CHROMA_PERSIST_DIR = str(tmp_path / "chroma")
        with patch('src.config.settings.config', mock_config):
            import src.rag.vector_store as vs_mod
            with patch.object(vs_mod, 'config', mock_config):
                with patch('src.rag.vector_store.genai') as mock_genai:
                    mock_genai.Client.return_value = mock_gemini_client
                    from src.rag.vector_store import VectorStore
                    store = VectorStore()
                    return store
    
    @pytest.mark.unit
    def test_get_embedding(self, vector_store):
        """Test getting single embedding"""
        embedding = vector_store._get_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
    
    @pytest.mark.unit
    def test_get_embeddings_batch(self, vector_store):
        """Test getting batch embeddings"""
        texts = ["text 1", "text 2", "text 3"]

        # The mock embed_content needs to return N embeddings when called
        # with a list of N texts (batch mode uses _embed_content_batch).
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_batch_result = MagicMock()
        mock_batch_result.embeddings = [mock_embedding] * len(texts)
        vector_store.gemini_client.models.embed_content.return_value = mock_batch_result

        embeddings = vector_store._get_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 768
