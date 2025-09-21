from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Document metadata model"""
    filename: str
    upload_source: str
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    additional_info: Optional[Dict[str, Any]] = None

class DocumentChunk(BaseModel):
    """Document chunk model"""
    id: int
    document_id: int
    chunk_text: str
    chunk_index: int
    keywords: List[str]
    created_at: datetime

class SearchResult(BaseModel):
    """Search result model"""
    chunk_id: int
    document_id: int
    filename: str
    content: str = Field(..., description="The matching text content")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score between 0 and 1")
    keywords_matched: List[str] = Field(default_factory=list, description="Keywords that matched in the search")
    context_preview: str = Field(..., description="Surrounding text for context")
    chunk_index: int = Field(..., description="Position of chunk in original document")

class DocumentUploadItem(BaseModel):
    """Individual document upload result"""
    filename: str
    document_id: Optional[int] = None
    status: str
    chunks_created: Optional[int] = None
    error_message: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    """Response for document upload endpoint"""
    message: str
    documents: List[DocumentUploadItem]
    total_processed: Optional[int] = None
    processing_time_seconds: Optional[float] = None

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_type: str = Field(default="hybrid", description="Type of search: semantic, keyword, or hybrid")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional search filters")

class SystemStats(BaseModel):
    """System statistics model"""
    total_documents: int
    total_chunks: int
    total_embeddings: int
    database_size_mb: Optional[float] = None
    avg_processing_time_ms: Optional[float] = None
    last_updated: datetime

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    message: str
    timestamp: datetime
    services: Dict[str, str]  # service_name -> status

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None

class ProcessingStatus(BaseModel):
    """Document processing status model"""
    document_id: int
    filename: str
    status: str  # pending, processing, completed, failed
    progress_percentage: float = Field(ge=0.0, le=100.0)
    chunks_processed: int
    total_chunks: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None