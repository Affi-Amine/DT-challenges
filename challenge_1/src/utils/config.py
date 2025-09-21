import os
from typing import Optional, List
from pydantic import validator
from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application settings
    app_name: str = "DiploTools Document Processing Pipeline"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/diplomtools"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Redis settings (for caching)
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_db: int = 0
    cache_ttl: int = 3600  # 1 hour
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "text-embedding-3-small"
    openai_max_tokens: int = 8192
    openai_timeout: int = 30
    openai_max_retries: int = 3
    
    # Gemini settings (fallback)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "models/embedding-001"
    
    # Local embedding settings
    local_embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # for all-MiniLM-L6-v2
    
    # Document processing settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = [".md", ".txt", ".pdf", ".docx"]
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_document: int = 1000
    
    # Search settings
    max_search_results: int = 50
    semantic_search_weight: float = 0.7
    keyword_search_weight: float = 0.3
    min_similarity_threshold: float = 0.3
    
    # Performance settings
    max_concurrent_requests: int = 100
    request_timeout: int = 300  # 5 minutes
    batch_size: int = 10
    max_workers: int = 4
    
    # Security settings
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_headers: List[str] = ["*"]
    
    # Monitoring settings
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('semantic_search_weight', 'keyword_search_weight')
    def validate_search_weights(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Search weights must be between 0 and 1')
        return v
    
    @validator('min_similarity_threshold')
    def validate_similarity_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Similarity threshold must be between 0 and 1')
        return v
    
    @validator('allowed_file_types')
    def validate_file_types(cls, v):
        # Ensure all file types start with a dot
        return [ft if ft.startswith('.') else f'.{ft}' for ft in v]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefixes
        env_prefix = ""
        
        # Field aliases for environment variables
        fields = {
            'database_url': {'env': ['DATABASE_URL', 'DB_URL']},
            'redis_url': {'env': ['REDIS_URL', 'CACHE_URL']},
            'openai_api_key': {'env': ['OPENAI_API_KEY', 'OPENAI_KEY']},
            'gemini_api_key': {'env': ['GEMINI_API_KEY', 'GOOGLE_API_KEY']},
        }

# Global settings instance
settings = Settings()

# Configure logging
def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log') if not settings.debug else logging.NullHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    reload: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "INFO"
    reload: bool = False
    cors_origins: List[str] = []  # Should be set explicitly in production
    
    # Production database settings
    database_pool_size: int = 20
    database_max_overflow: int = 40
    
    # Production performance settings
    max_concurrent_requests: int = 200
    max_workers: int = 8

class TestSettings(Settings):
    """Test environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "postgresql://postgres:password@localhost:5432/diplomtools_test"
    redis_url: str = "redis://localhost:6379/1"  # Different Redis DB for tests
    cache_ttl: int = 60  # Shorter cache for tests
    
    # Test-specific settings
    max_file_size: int = 1024 * 1024  # 1MB for tests
    max_chunks_per_document: int = 100
    max_search_results: int = 10

def get_settings(environment: str = None) -> Settings:
    """Get settings based on environment"""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    if environment == 'production':
        return ProductionSettings()
    elif environment == 'test':
        return TestSettings()
    else:
        return DevelopmentSettings()

# Validation functions
def validate_required_settings():
    """Validate that required settings are present"""
    errors = []
    
    # Check database URL
    if not settings.database_url or settings.database_url == "postgresql://postgres:password@localhost:5432/diplomtools":
        errors.append("DATABASE_URL must be set to a valid PostgreSQL connection string")
    
    # Check embedding service configuration
    if not settings.openai_api_key and not settings.gemini_api_key:
        errors.append("At least one of OPENAI_API_KEY or GEMINI_API_KEY must be set")
    
    # Check Redis URL for production
    if os.getenv('ENVIRONMENT', '').lower() == 'production':
        if not settings.redis_url or settings.redis_url == "redis://localhost:6379/0":
            errors.append("REDIS_URL must be set for production environment")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {error}" for error in errors))

def get_database_config() -> dict:
    """Get database configuration dictionary"""
    return {
        'url': settings.database_url,
        'pool_size': settings.database_pool_size,
        'max_overflow': settings.database_max_overflow,
        'pool_timeout': settings.database_pool_timeout,
        'pool_recycle': settings.database_pool_recycle,
    }

def get_redis_config() -> dict:
    """Get Redis configuration dictionary"""
    return {
        'url': settings.redis_url,
        'password': settings.redis_password,
        'db': settings.redis_db,
        'decode_responses': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
        'retry_on_timeout': True,
    }

def get_embedding_config() -> dict:
    """Get embedding service configuration"""
    return {
        'openai': {
            'api_key': settings.openai_api_key,
            'model': settings.openai_model,
            'max_tokens': settings.openai_max_tokens,
            'timeout': settings.openai_timeout,
            'max_retries': settings.openai_max_retries,
        },
        'gemini': {
            'api_key': settings.gemini_api_key,
            'model': settings.gemini_model,
        },
        'local': {
            'model': settings.local_embedding_model,
            'dimension': settings.embedding_dimension,
        }
    }

# Initialize logging on import
setup_logging()