import asyncpg
import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import json
from utils.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_string = self._get_connection_string()
    
    def _get_connection_string(self) -> str:
        """Get database connection string from environment variables"""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'document_pipeline')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def initialize(self):
        """Initialize database connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            logger.info("Database connection pool created")
            
            # Create tables and indexes
            await self._create_tables()
            await self._create_indexes()
            
            logger.info("Database initialization complete")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            # Enable pg-vector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create documents table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create document_chunks table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    embedding vector({settings.embedding_dimension}),
                    keywords TEXT[],
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create search_cache table for performance
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    id SERIAL PRIMARY KEY,
                    query_hash VARCHAR(64) UNIQUE NOT NULL,
                    query_text TEXT NOT NULL,
                    search_type VARCHAR(20) NOT NULL,
                    results JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL
                );
            """)
            
            logger.info("Database tables created successfully")
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        async with self.pool.acquire() as conn:
            # Vector similarity index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
                ON document_chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            
            # Keywords GIN index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_keywords 
                ON document_chunks USING GIN (keywords);
            """)
            
            # Full-text search index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_text 
                ON document_chunks USING GIN (to_tsvector('english', chunk_text));
            """)
            
            # Document filename index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_filename 
                ON documents (filename);
            """)
            
            # Cache expiration index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_cache_expires 
                ON search_cache (expires_at);
            """)
            
            logger.info("Database indexes created successfully")
    
    async def insert_document(self, filename: str, content: str, metadata: Dict[str, Any]) -> int:
        """Insert a new document and return its ID"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                "INSERT INTO documents (filename, content, metadata) VALUES ($1, $2, $3) RETURNING id",
                filename, content, json.dumps(metadata)
            )
            return result['id']
    
    async def insert_document_chunk(
        self, 
        document_id: int, 
        chunk_text: str, 
        chunk_index: int, 
        embedding: List[float], 
        keywords: List[str]
    ) -> int:
        """Insert a document chunk with embedding"""
        async with self.pool.acquire() as conn:
            # Convert embedding list to PostgreSQL vector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            result = await conn.fetchrow(
                """INSERT INTO document_chunks 
                   (document_id, chunk_text, chunk_index, embedding, keywords) 
                   VALUES ($1, $2, $3, $4::vector, $5) RETURNING id""",
                document_id, chunk_text, chunk_index, embedding_str, keywords
            )
            return result['id']
    
    async def semantic_search(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        async with self.pool.acquire() as conn:
            # Convert query embedding to PostgreSQL vector format
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            results = await conn.fetch(
                """
                SELECT 
                    dc.id as chunk_id,
                    dc.document_id,
                    d.filename,
                    dc.chunk_text as content,
                    dc.chunk_index,
                    dc.keywords,
                    1 - (dc.embedding <=> $1::vector) as relevance_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> $1::vector
                LIMIT $2
                """,
                query_embedding_str, limit
            )
            
            return [dict(row) for row in results]
    
    async def keyword_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        async with self.pool.acquire() as conn:
            # Use PostgreSQL full-text search
            results = await conn.fetch(
                """
                SELECT 
                    dc.id as chunk_id,
                    dc.document_id,
                    d.filename,
                    dc.chunk_text as content,
                    dc.chunk_index,
                    dc.keywords,
                    ts_rank(to_tsvector('english', dc.chunk_text), plainto_tsquery('english', $1)) as relevance_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE to_tsvector('english', dc.chunk_text) @@ plainto_tsquery('english', $1)
                   OR dc.keywords && string_to_array($1, ' ')
                ORDER BY relevance_score DESC
                LIMIT $2
                """,
                query, limit
            )
            
            return [dict(row) for row in results]
    
    async def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT id, chunk_text, chunk_index, keywords, created_at
                FROM document_chunks
                WHERE document_id = $1
                ORDER BY chunk_index
                """,
                document_id
            )
            
            return [dict(row) for row in results]
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        async with self.pool.acquire() as conn:
            # Get document count
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            
            # Get chunk count
            chunk_count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
            
            # Get embedding count
            embedding_count = await conn.fetchval(
                "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"
            )
            
            # Get database size (approximate)
            db_size = await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            
            return {
                "total_documents": doc_count,
                "total_chunks": chunk_count,
                "total_embeddings": embedding_count,
                "database_size": db_size,
                "last_updated": datetime.now()
            }
    
    async def cache_search_results(self, query_hash: str, query_text: str, search_type: str, results: List[Dict], ttl_hours: int = 1):
        """Cache search results for performance"""
        async with self.pool.acquire() as conn:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            await conn.execute(
                """
                INSERT INTO search_cache (query_hash, query_text, search_type, results, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (query_hash) DO UPDATE SET
                    results = EXCLUDED.results,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
                """,
                query_hash, query_text, search_type, json.dumps(results), expires_at
            )
    
    async def get_cached_search_results(self, query_hash: str) -> Optional[List[Dict]]:
        """Get cached search results if available and not expired"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT results FROM search_cache 
                WHERE query_hash = $1 AND expires_at > NOW()
                """,
                query_hash
            )
            
            if result:
                return json.loads(result['results'])
            return None
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        async with self.pool.acquire() as conn:
            deleted_count = await conn.fetchval(
                "DELETE FROM search_cache WHERE expires_at <= NOW() RETURNING COUNT(*)"
            )
            logger.info(f"Cleaned up {deleted_count} expired cache entries")