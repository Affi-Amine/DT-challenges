from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import logging
from contextlib import asynccontextmanager

from services.document_processor import DocumentProcessor
from services.search_service import SearchService
from models.schemas import SearchResult, DocumentUploadResponse
from database.connection import DatabaseManager
from utils.file_processor import FileProcessor
from utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
document_processor: Optional[DocumentProcessor] = None
search_service: Optional[SearchService] = None
db_manager: Optional[DatabaseManager] = None
file_processor: Optional[FileProcessor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global document_processor, search_service, db_manager, file_processor
    
    # Startup
    logger.info("Starting Document Processing Pipeline...")
    
    # Initialize database connection
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Initialize services
    document_processor = DocumentProcessor(db_manager)
    search_service = SearchService(db_manager)
    file_processor = FileProcessor()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if db_manager:
        await db_manager.close()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Document Processing Pipeline",
    description="Semantic search and retrieval for large document corpus",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Document Processing Pipeline API", "status": "healthy"}

@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process multiple documents"""
    try:
        if not document_processor or not file_processor:
            raise HTTPException(status_code=500, detail="Services not initialized")
        
        # Get allowed file types from settings
        allowed_extensions = settings.allowed_file_types
        max_file_size = settings.max_file_size
        
        results = []
        for file in files:
            # Validate file type
            if not file_processor.is_supported_file(file.filename):
                results.append({
                    "filename": file.filename,
                    "document_id": None,
                    "status": "error",
                    "chunks_created": 0,
                    "error_message": f"Unsupported file type. Allowed types: {allowed_extensions}"
                })
                continue
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > max_file_size:
                results.append({
                    "filename": file.filename,
                    "document_id": None,
                    "status": "error",
                    "chunks_created": 0,
                    "error_message": f"File too large. Maximum size: {max_file_size} bytes"
                })
                continue
            
            try:
                # Process file based on type
                file_info = await file_processor.process_file(file.filename, content)
                text_content = file_info['text_content']
                
                # Process document
                document_id = await document_processor.process_document(
                    filename=file.filename,
                    content=text_content,
                    metadata={
                        "upload_source": "api",
                        "file_type": file_info['file_type'],
                        "original_size": file_info['original_size'],
                        "processed_size": file_info['processed_size']
                    }
                )
                
                # Get the actual chunk count from the database
                chunks = await db_manager.get_document_chunks(document_id)
                chunks_created = len(chunks)
                
                results.append({
                    "filename": file.filename,
                    "document_id": document_id,
                    "status": "processed",
                    "chunks_created": chunks_created,
                    "error_message": None
                })
                
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {str(file_error)}")
                results.append({
                    "filename": file.filename,
                    "document_id": None,
                    "status": "error",
                    "chunks_created": 0,
                    "error_message": str(file_error)
                })
        
        successful_count = len([r for r in results if r['status'] == 'processed'])
        
        return DocumentUploadResponse(
            message=f"Processed {successful_count}/{len(results)} documents successfully",
            documents=results,
            total_processed=successful_count,
            processing_time_seconds=0  # Could add timing if needed
        )
    
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_model=List[SearchResult])
async def search_documents(
    query: str = Query(..., description="Search query"),
    search_type: str = Query("hybrid", description="Search type: semantic, keyword, or hybrid"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """Search documents using semantic or hybrid search"""
    try:
        if not search_service:
            raise HTTPException(status_code=500, detail="Search service not initialized")
        
        if search_type == "semantic":
            results = await search_service.semantic_search(query, limit)
        elif search_type == "keyword":
            results = await search_service.keyword_search(query, limit)
        elif search_type == "hybrid":
            results = await search_service.hybrid_search(query, limit)
        else:
            raise HTTPException(status_code=400, detail="Invalid search_type. Use: semantic, keyword, or hybrid")
        
        return results
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: int):
    """Retrieve chunks for a specific document"""
    try:
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        chunks = await db_manager.get_document_chunks(doc_id)
        return {"document_id": doc_id, "chunks": chunks}
    
    except Exception as e:
        logger.error(f"Error retrieving document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        stats = await db_manager.get_system_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)