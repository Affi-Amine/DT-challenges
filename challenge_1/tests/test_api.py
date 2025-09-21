import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import json
import tempfile
import os
from pathlib import Path

# Import the main app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
# Import simple test config to avoid Pydantic issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from test_config import test_settings

@pytest.fixture
def client():
    """Create a test client"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def async_client():
    """Create an async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_markdown_file():
    """Create a sample markdown file for testing"""
    content = """
# Sample Document

This is a sample markdown document for testing the DiploTools document processing pipeline.

## Introduction

This document contains information about international relations and diplomatic processes.
It discusses various aspects of diplomacy, including:

- Bilateral negotiations
- Multilateral agreements
- United Nations resolutions
- Treaty implementation

## Key Concepts

### Diplomatic Immunity

Diplomatic immunity is a principle of international law that provides foreign diplomats with protection from legal action in the host country.

### Vienna Convention

The Vienna Convention on Diplomatic Relations (1961) is a key international treaty that defines diplomatic relations between independent countries.

## Conclusion

Effective diplomacy requires understanding of international law, cultural sensitivity, and strategic communication.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

class TestDocumentUpload:
    """Test document upload functionality"""
    
    @patch('services.document_processor.DocumentProcessor.process_document')
    @patch('database.connection.DatabaseManager.insert_document')
    def test_upload_markdown_file(self, mock_insert, mock_process, client, sample_markdown_file):
        """Test uploading a markdown file"""
        # Mock the database and processing
        mock_insert.return_value = "test-doc-id"
        mock_process.return_value = {
            "chunk_count": 5,
            "keywords": ["diplomacy", "international", "treaty"],
            "processing_time": 1.5
        }
        
        with open(sample_markdown_file, 'rb') as f:
            response = client.post(
                "/documents/upload",
                files={"file": ("test.md", f, "text/markdown")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
        assert "message" in data
    
    def test_upload_invalid_file_type(self, client):
        """Test uploading an invalid file type"""
        # Create a fake file with invalid extension
        with tempfile.NamedTemporaryFile(suffix='.xyz') as f:
            f.write(b"invalid content")
            f.seek(0)
            
            response = client.post(
                "/documents/upload",
                files={"file": ("test.xyz", f, "application/octet-stream")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_upload_no_file(self, client):
        """Test upload endpoint without file"""
        response = client.post("/documents/upload")
        assert response.status_code == 422  # Validation error

class TestSearchEndpoints:
    """Test search functionality"""
    
    @patch('services.search_service.SearchService.hybrid_search')
    def test_search_documents(self, mock_search, client):
        """Test document search"""
        # Mock search results
        mock_search.return_value = {
            "results": [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "content": "Sample content about diplomacy",
                    "similarity_score": 0.85,
                    "document_title": "Sample Document",
                    "chunk_index": 0
                }
            ],
            "total_results": 1,
            "search_time": 0.15,
            "search_type": "hybrid"
        }
        
        response = client.post(
            "/search",
            json={
                "query": "diplomacy international relations",
                "max_results": 10,
                "search_type": "hybrid"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_results" in data
        assert "search_time" in data
        assert len(data["results"]) == 1
    
    def test_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.post(
            "/search",
            json={"query": "", "max_results": 10}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_search_invalid_search_type(self, client):
        """Test search with invalid search type"""
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "search_type": "invalid_type"
            }
        )
        
        assert response.status_code == 422  # Validation error

class TestChunkEndpoints:
    """Test chunk retrieval functionality"""
    
    @patch('database.connection.DatabaseManager.get_chunk_by_id')
    def test_get_chunk_by_id(self, mock_get_chunk, client):
        """Test retrieving a chunk by ID"""
        # Mock chunk data
        mock_get_chunk.return_value = {
            "id": "chunk-1",
            "document_id": "doc-1",
            "content": "Sample chunk content",
            "chunk_index": 0,
            "keywords": ["sample", "content"],
            "metadata": {}
        }
        
        response = client.get("/chunks/chunk-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "chunk-1"
        assert "content" in data
    
    @patch('database.connection.DatabaseManager.get_chunk_by_id')
    def test_get_nonexistent_chunk(self, mock_get_chunk, client):
        """Test retrieving a non-existent chunk"""
        mock_get_chunk.return_value = None
        
        response = client.get("/chunks/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

class TestSystemEndpoints:
    """Test system information endpoints"""
    
    @patch('database.connection.DatabaseManager.get_system_stats')
    def test_get_system_stats(self, mock_stats, client):
        """Test system statistics endpoint"""
        # Mock system stats
        mock_stats.return_value = {
            "total_documents": 10,
            "total_chunks": 50,
            "avg_chunks_per_document": 5.0,
            "total_size_mb": 25.5,
            "processing_status": {
                "pending": 1,
                "completed": 8,
                "failed": 1
            },
            "cache_stats": {
                "total_queries": 100,
                "cache_hits": 75,
                "cache_hit_rate": 0.75
            }
        }
        
        response = client.get("/system/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "processing_status" in data

@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async functionality"""
    
    async def test_async_health_check(self, async_client):
        """Test async health check"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('services.search_service.SearchService.hybrid_search')
    async def test_async_search(self, mock_search, async_client):
        """Test async search"""
        mock_search.return_value = {
            "results": [],
            "total_results": 0,
            "search_time": 0.1,
            "search_type": "hybrid"
        }
        
        response = await async_client.post(
            "/search",
            json={"query": "test query", "max_results": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_endpoint(self, client):
        """Test non-existent endpoint returns 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test wrong HTTP method returns 405"""
        response = client.delete("/health")
        assert response.status_code == 405

if __name__ == "__main__":
    pytest.main([__file__])