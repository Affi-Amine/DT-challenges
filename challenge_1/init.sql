-- Initialize DiploTools database with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size BIGINT NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    keywords TEXT[] DEFAULT '{}',
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_timestamp TIMESTAMP WITH TIME ZONE,
    chunk_count INTEGER DEFAULT 0,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Create document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(384),
    keywords TEXT[] DEFAULT '{}',
    entities JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    word_count INTEGER DEFAULT 0,
    char_count INTEGER DEFAULT 0,
    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- Create search cache table
CREATE TABLE IF NOT EXISTS search_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    search_type VARCHAR(20) DEFAULT 'semantic' CHECK (search_type IN ('semantic', 'keyword', 'hybrid')),
    results JSONB NOT NULL,
    result_count INTEGER DEFAULT 0,
    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create system stats table
CREATE TABLE IF NOT EXISTS system_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stat_type VARCHAR(50) NOT NULL,
    stat_value NUMERIC NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance

-- Documents table indexes
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp ON documents(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_keywords ON documents USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);

-- Document chunks table indexes
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON document_chunks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON document_chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_keywords ON document_chunks USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_chunks_entities ON document_chunks USING GIN(entities);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON document_chunks USING GIN(metadata);

-- Vector similarity search index (HNSW for better performance)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON document_chunks 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (comment out HNSW if using this)
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat ON document_chunks 
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search index for content
CREATE INDEX IF NOT EXISTS idx_chunks_content_fts ON document_chunks 
USING GIN(to_tsvector('english', content));

-- Search cache indexes
CREATE INDEX IF NOT EXISTS idx_search_cache_query_hash ON search_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_cache_created ON search_cache(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_search_cache_last_accessed ON search_cache(last_accessed);
CREATE INDEX IF NOT EXISTS idx_search_cache_search_type ON search_cache(search_type);

-- System stats indexes
CREATE INDEX IF NOT EXISTS idx_system_stats_type ON system_stats(stat_type);
CREATE INDEX IF NOT EXISTS idx_system_stats_timestamp ON system_stats(timestamp);

-- Create functions for common operations

-- Function to calculate cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Function to update document chunk count
CREATE OR REPLACE FUNCTION update_document_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE documents 
        SET chunk_count = chunk_count + 1 
        WHERE id = NEW.document_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE documents 
        SET chunk_count = chunk_count - 1 
        WHERE id = OLD.document_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update chunk count
CREATE TRIGGER trigger_update_chunk_count
    AFTER INSERT OR DELETE ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION update_document_chunk_count();

-- Cache cleanup function
CREATE OR REPLACE FUNCTION cleanup_search_cache(retention_hours INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM search_cache 
    WHERE last_accessed < NOW() - (retention_hours || ' hours')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Document statistics function
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE(
    total_documents BIGINT,
    total_chunks BIGINT,
    total_size_bytes BIGINT,
    avg_chunks_per_doc NUMERIC,
    total_words BIGINT,
    pending_documents BIGINT,
    processing_documents BIGINT,
    completed_documents BIGINT,
    failed_documents BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_documents,
        SUM(d.chunk_count)::BIGINT as total_chunks,
        SUM(d.file_size)::BIGINT as total_size_bytes,
        AVG(d.chunk_count)::NUMERIC as avg_chunks_per_doc,
        COALESCE(SUM((SELECT SUM(word_count) FROM document_chunks WHERE document_id = d.id)), 0)::BIGINT as total_words,
        COUNT(*) FILTER (WHERE d.processing_status = 'pending')::BIGINT as pending_documents,
        COUNT(*) FILTER (WHERE d.processing_status = 'processing')::BIGINT as processing_documents,
        COUNT(*) FILTER (WHERE d.processing_status = 'completed')::BIGINT as completed_documents,
        COUNT(*) FILTER (WHERE d.processing_status = 'failed')::BIGINT as failed_documents
    FROM documents d;
END;
$$ LANGUAGE plpgsql;

-- Insert initial system stats
INSERT INTO system_stats (stat_type, stat_value) VALUES 
('database_initialized', '{"version": "1.0.0", "timestamp": "' || CURRENT_TIMESTAMP || '"}');

-- Create a view for search analytics
CREATE OR REPLACE VIEW search_analytics AS
SELECT 
    search_type,
    COUNT(*) as query_count,
    AVG(result_count) as avg_results,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_query_time,
    DATE_TRUNC('day', created_timestamp) as query_date
FROM search_cache 
GROUP BY search_type, DATE_TRUNC('day', created_timestamp)
ORDER BY query_date DESC;

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Create a user for the application (optional)
-- CREATE USER diplomtools_app WITH PASSWORD 'your_app_password';
-- GRANT CONNECT ON DATABASE diplomtools TO diplomtools_app;
-- GRANT USAGE ON SCHEMA public TO diplomtools_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO diplomtools_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO diplomtools_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO diplomtools_app;

COMMIT;