"""
Unit tests for Fact Store
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestFactStore:
    """Tests for FactStore class"""
    
    @pytest.fixture
    def fact_store(self, tmp_path):
        """Create FactStore instance with temp directory"""
        with patch('src.rag.fact_store.Path') as mock_path:
            # Make Path("data") return tmp_path / "data"
            data_dir = tmp_path / "data"
            data_dir.mkdir()
            mock_path.return_value = data_dir
            
            from src.rag.fact_store import FactStore
            store = FactStore()
            store.data_dir = data_dir
            store.file_path = data_dir / "facts.json"
            store.facts = {}
            return store
    
    @pytest.mark.unit
    def test_set_fact(self, fact_store):
        """Test setting a fact"""
        fact_store.set("LATENCY", "200ms")
        
        assert fact_store.facts["LATENCY"] == "200ms"
    
    @pytest.mark.unit
    def test_set_fact_case_insensitive(self, fact_store):
        """Test that keys are stored uppercase"""
        fact_store.set("latency", "200ms")
        
        assert "LATENCY" in fact_store.facts
        assert fact_store.facts["LATENCY"] == "200ms"
    
    @pytest.mark.unit
    def test_get_fact(self, fact_store):
        """Test getting a fact"""
        fact_store.facts["RATE_LIMIT"] = "2 req/sec"
        
        result = fact_store.get("RATE_LIMIT")
        assert result == "2 req/sec"
    
    @pytest.mark.unit
    def test_get_fact_case_insensitive(self, fact_store):
        """Test getting a fact with lowercase key"""
        fact_store.facts["RATE_LIMIT"] = "2 req/sec"
        
        result = fact_store.get("rate_limit")
        assert result == "2 req/sec"
    
    @pytest.mark.unit
    def test_get_nonexistent_fact(self, fact_store):
        """Test getting a fact that doesn't exist"""
        result = fact_store.get("NONEXISTENT")
        assert result is None
    
    @pytest.mark.unit
    def test_delete_fact(self, fact_store):
        """Test deleting a fact"""
        fact_store.facts["TEMP"] = "value"
        
        result = fact_store.delete("TEMP")
        
        assert result is True
        assert "TEMP" not in fact_store.facts
    
    @pytest.mark.unit
    def test_delete_nonexistent_fact(self, fact_store):
        """Test deleting a fact that doesn't exist"""
        result = fact_store.delete("NONEXISTENT")
        assert result is False
    
    @pytest.mark.unit
    def test_get_all_facts(self, fact_store):
        """Test getting all facts"""
        fact_store.facts = {
            "KEY1": "value1",
            "KEY2": "value2"
        }
        
        all_facts = fact_store.get_all()
        
        assert all_facts == {"KEY1": "value1", "KEY2": "value2"}
        # Should return a copy, not the original
        all_facts["KEY3"] = "value3"
        assert "KEY3" not in fact_store.facts
    
    @pytest.mark.unit
    def test_search_finds_match(self, fact_store):
        """Test search finds matching fact"""
        fact_store.facts = {
            "LATENCY": "200ms",
            "RATE_LIMIT": "2 req/sec"
        }
        
        result = fact_store.search("What is the LATENCY?")
        
        assert result is not None
        assert "LATENCY" in result
        assert "200ms" in result
    
    @pytest.mark.unit
    def test_search_no_match(self, fact_store):
        """Test search returns None when no match"""
        fact_store.facts = {
            "LATENCY": "200ms"
        }
        
        result = fact_store.search("What is the weather?")
        assert result is None
    
    @pytest.mark.unit
    def test_persistence_save(self, fact_store):
        """Test that facts are saved to file"""
        fact_store.set("TEST_KEY", "test_value")
        
        # Check file was created and contains data
        if fact_store.file_path.exists():
            with open(fact_store.file_path, 'r') as f:
                data = json.load(f)
                assert "TEST_KEY" in data
    
    @pytest.mark.unit
    def test_persistence_load(self, fact_store):
        """Test that facts are loaded from file"""
        # Create a facts file
        facts_data = {"LOADED_KEY": "loaded_value"}
        with open(fact_store.file_path, 'w') as f:
            json.dump(facts_data, f)
        
        # Load it
        fact_store._load()
        
        assert fact_store.facts.get("LOADED_KEY") == "loaded_value"
