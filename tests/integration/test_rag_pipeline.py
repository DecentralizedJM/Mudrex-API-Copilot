"""
Integration tests for RAG Pipeline
"""
from unittest.mock import MagicMock, patch, AsyncMock
import pytest


class TestRAGPipelineIntegration:
    """Integration tests for the RAG Pipeline"""
    
    @pytest.fixture
    def mock_vector_store(self, sample_documents, sample_metadatas):
        """Create mock vector store"""
        mock = MagicMock()
        mock.search.return_value = [
            {
                "document": sample_documents[0],
                "metadata": sample_metadatas[0],
                "similarity": 0.85,
                "distance": 0.15
            }
        ]
        mock.search_all_relevant.return_value = [
            {
                "document": sample_documents[0],
                "metadata": sample_metadatas[0],
                "similarity": 0.75,
                "distance": 0.25
            }
        ]
        mock.get_count.return_value = 5
        return mock
    
    @pytest.fixture
    def mock_gemini_client_for_pipeline(self):
        """Create mock Gemini client for pipeline"""
        mock = MagicMock()
        mock.model_name = "gemini-3-flash-preview"
        mock.classify_query_domain.return_value = "mudrex_specific"
        mock.generate_response.return_value = "Here is how to authenticate with Mudrex API..."
        mock.generate_response_with_context_search.return_value = "I couldn't find specific info..."
        mock.validate_document_relevancy.return_value = []
        mock.rerank_documents.return_value = []
        mock._get_missing_feature_response.return_value = None
        mock._get_api_key_usage_response.return_value = None
        return mock
    
    @pytest.fixture
    def mock_fact_store(self):
        """Create mock fact store"""
        mock = MagicMock()
        mock.search.return_value = None
        return mock
    
    @pytest.fixture
    def rag_pipeline(self, mock_vector_store, mock_gemini_client_for_pipeline, mock_fact_store, mock_config):
        """Create RAG pipeline with mocked components"""
        mock_config.REDIS_ENABLED = False  # avoid SemanticCache() needing Gemini API key
        with patch('src.config.settings.config', mock_config):
            import src.rag.pipeline
            with patch('src.rag.pipeline.SemanticCache', MagicMock(return_value=None)):
                with patch('src.rag.pipeline.ContextManager', MagicMock(return_value=None)):
                    with patch('src.rag.pipeline.SemanticMemory', MagicMock(return_value=None)):
                        with patch('src.rag.pipeline.VectorStore', return_value=mock_vector_store):
                            with patch('src.rag.pipeline.GeminiClient', return_value=mock_gemini_client_for_pipeline):
                                with patch('src.rag.pipeline.FactStore', return_value=mock_fact_store):
                                    with patch('src.rag.pipeline.RedisCache', return_value=None):
                                        from src.rag.pipeline import RAGPipeline
                                        pipeline = RAGPipeline()
                                        pipeline.vector_store = mock_vector_store
                                        pipeline.gemini_client = mock_gemini_client_for_pipeline
                                        pipeline.fact_store = mock_fact_store
                                        pipeline.cache = None
                                        pipeline.context_manager = None
                                        pipeline.semantic_memory = None
                                        return pipeline
    
    @pytest.mark.integration
    def test_query_basic(self, rag_pipeline, mock_gemini_client_for_pipeline, sample_documents, sample_metadatas):
        """Test basic query flow"""
        # Setup mocks to return documents
        rag_pipeline.vector_store.search.return_value = [
            {
                "document": sample_documents[0],
                "metadata": sample_metadatas[0],
                "similarity": 0.85,
                "distance": 0.15
            }
        ]
        mock_gemini_client_for_pipeline.validate_document_relevancy.return_value = [
            {
                "document": sample_documents[0],
                "metadata": sample_metadatas[0],
                "similarity": 0.85,
                "distance": 0.15
            }
        ]
        mock_gemini_client_for_pipeline.rerank_documents.return_value = [
            {
                "document": sample_documents[0],
                "metadata": sample_metadatas[0],
                "similarity": 0.85,
                "distance": 0.15
            }
        ]
        
        result = rag_pipeline.query("How do I authenticate?")
        
        assert "answer" in result
        assert "sources" in result
        assert "is_relevant" in result
    
    @pytest.mark.integration
    def test_query_fact_store_hit(self, rag_pipeline, mock_fact_store):
        """Test query hits fact store"""
        mock_fact_store.search.return_value = "**LATENCY**: 200ms"
        
        result = rag_pipeline.query("What is the LATENCY?")
        
        assert result["answer"] == "**LATENCY**: 200ms"
        assert result["sources"][0]["filename"] == "FactStore (Strict User Rule)"
    
    @pytest.mark.integration
    def test_query_generic_trading(self, rag_pipeline, mock_gemini_client_for_pipeline):
        """Test generic trading query bypasses RAG"""
        mock_gemini_client_for_pipeline.classify_query_domain.return_value = "generic_trading"
        mock_gemini_client_for_pipeline.generate_generic_trading_answer.return_value = "Generic trading advice..."
        
        # Use a query that won't be caught by _get_off_topic_reply ("what is X" pattern)
        result = rag_pipeline.query("How should I manage risk in futures trading?")
        
        assert "answer" in result
        mock_gemini_client_for_pipeline.generate_generic_trading_answer.assert_called_once()
    
    @pytest.mark.integration
    def test_query_no_docs_found(self, rag_pipeline, mock_gemini_client_for_pipeline):
        """Test query when no relevant documents found"""
        rag_pipeline.vector_store.search.return_value = []
        rag_pipeline.vector_store.search_all_relevant.return_value = []
        mock_gemini_client_for_pipeline.validate_document_relevancy.return_value = []
        mock_gemini_client_for_pipeline.rerank_documents.return_value = []
        
        result = rag_pipeline.query("Some obscure question")
        
        assert "answer" in result
        mock_gemini_client_for_pipeline.generate_response_with_context_search.assert_called()
    
    @pytest.mark.integration
    def test_get_stats(self, rag_pipeline):
        """Test getting pipeline statistics"""
        stats = rag_pipeline.get_stats()
        
        assert "total_documents" in stats
        assert "model" in stats
    
    @pytest.mark.integration
    def test_learn_text(self, rag_pipeline):
        """Test learning new text"""
        rag_pipeline.learn_text("New API endpoint: GET /fapi/v1/test")
        
        rag_pipeline.vector_store.add_documents.assert_called()
    
    @pytest.mark.integration
    def test_set_and_delete_fact(self, rag_pipeline, mock_fact_store):
        """Test setting and deleting facts"""
        rag_pipeline.set_fact("TEST_KEY", "test_value")
        mock_fact_store.set.assert_called_with("TEST_KEY", "test_value")
        
        mock_fact_store.delete.return_value = True
        result = rag_pipeline.delete_fact("TEST_KEY")
        assert result is True


class TestRAGPipelineIterativeRetrieval:
    """Tests for iterative retrieval functionality"""
    
    @pytest.fixture
    def pipeline_for_iterative(self, mock_config):
        """Create pipeline for iterative retrieval tests"""
        mock_config.REDIS_ENABLED = False
        mock_config.MAX_ITERATIVE_RETRIEVAL = 2
        with patch('src.config.settings.config', mock_config):
            import src.rag.pipeline
            with patch('src.rag.pipeline.SemanticCache', MagicMock(return_value=None)):
                with patch('src.rag.pipeline.ContextManager', MagicMock(return_value=None)):
                    with patch('src.rag.pipeline.SemanticMemory', MagicMock(return_value=None)):
                        with patch('src.rag.pipeline.VectorStore') as mock_vs:
                            with patch('src.rag.pipeline.GeminiClient') as mock_gc:
                                with patch('src.rag.pipeline.FactStore'):
                                    with patch('src.rag.pipeline.RedisCache', return_value=None):
                                        from src.rag.pipeline import RAGPipeline
                                        pipeline = RAGPipeline()
                                        pipeline.vector_store = MagicMock()
                                        pipeline.gemini_client = MagicMock()
                                        pipeline.gemini_client.transform_query.return_value = "transformed query"
                                        return pipeline
    
    @pytest.mark.integration
    def test_iterative_retrieval_finds_docs(self, pipeline_for_iterative):
        """Test iterative retrieval finds documents after transformation"""
        pipeline = pipeline_for_iterative
        
        # First search fails, second succeeds
        pipeline.vector_store.search.side_effect = [
            [],  # First attempt
            [{"document": "Found!", "metadata": {}, "similarity": 0.8}]  # Second attempt
        ]
        
        results = pipeline._iterative_retrieval("complex query")
        
        assert len(results) == 1
        assert results[0]["document"] == "Found!"
    
    @pytest.mark.integration
    def test_iterative_retrieval_max_iterations(self, pipeline_for_iterative):
        """Test iterative retrieval respects max iterations"""
        pipeline = pipeline_for_iterative
        
        # All searches fail
        pipeline.vector_store.search.return_value = []
        
        results = pipeline._iterative_retrieval("impossible query")
        
        assert results == []
        # Should have called search max_iterations times
        assert pipeline.vector_store.search.call_count <= 2
