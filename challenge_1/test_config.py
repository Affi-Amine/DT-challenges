# Simple test configuration to avoid Pydantic issues
import os

class SimpleTestConfig:
    """Simple test configuration"""
    app_name = "DiploTools Test"
    debug = True
    log_level = "DEBUG"
    host = "0.0.0.0"
    port = 8000
    
    # Database (mock for tests)
    database_url = "sqlite:///test.db"
    
    # File processing
    max_file_size = 1024 * 1024  # 1MB
    allowed_file_types = [".md", ".txt", ".pdf", ".docx"]
    chunk_size = 1000
    chunk_overlap = 200
    
    # Search
    max_search_results = 10
    semantic_search_weight = 0.7
    keyword_search_weight = 0.3
    min_similarity_threshold = 0.3

test_settings = SimpleTestConfig()