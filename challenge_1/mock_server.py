#!/usr/bin/env python3
"""
Mock FastAPI server for Challenge 1 testing
This provides the basic endpoints that the tests expect
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import hashlib

app = FastAPI(
    title="DiploTools Document Processing API",
    description="Mock API for testing purposes",
    version="1.0.0"
)

class SearchRequest(BaseModel):
    query: str
    search_type: str = "hybrid"
    limit: int = 5

class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict

class DocumentInfo(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    size: int
    content: str

# Document storage - in a real app, this would be a database
uploaded_documents: List[DocumentInfo] = []

# Mock data for testing
mock_documents = [
    {
        "id": "doc_1",
        "content": "Diplomatic immunity is a principle of international law that provides foreign diplomats with protection from legal action in the country in which they are working. This immunity extends to diplomatic premises, communications, and personal effects.",
        "score": 0.95,
        "metadata": {"title": "Diplomatic Immunity Principles", "type": "legal_document", "country": "International", "date": "2024-01-15", "classification": "public"}
    },
    {
        "id": "doc_2", 
        "content": "International relations theory encompasses various approaches to understanding how states interact in the global system. Realism, liberalism, and constructivism are the main theoretical frameworks.",
        "score": 0.87,
        "metadata": {"title": "IR Theory Overview", "type": "academic_paper", "country": "USA", "date": "2024-02-10", "classification": "public"}
    },
    {
        "id": "doc_3",
        "content": "The Vienna Convention on Diplomatic Relations of 1961 establishes the framework for diplomatic relations between independent countries. It codifies the ancient practice of diplomatic immunity and sets out the privileges and immunities of diplomatic missions.",
        "score": 0.92,
        "metadata": {"title": "Vienna Convention 1961", "type": "treaty", "country": "International", "date": "1961-04-18", "classification": "public"}
    },
    {
        "id": "doc_4",
        "content": "Bilateral trade agreements between Tunisia and European Union member states have increased by 15% in 2024. Key sectors include agriculture, textiles, and renewable energy cooperation.",
        "score": 0.88,
        "metadata": {"title": "Tunisia-EU Trade Relations", "type": "economic_report", "country": "Tunisia", "date": "2024-03-20", "classification": "public"}
    },
    {
        "id": "doc_5",
        "content": "The Ambassador's credentials were presented to the Head of State in a formal ceremony. The diplomatic mission is now fully operational and ready to strengthen bilateral relations between both nations.",
        "score": 0.85,
        "metadata": {"title": "Credential Presentation Ceremony", "type": "diplomatic_note", "country": "France", "date": "2024-01-25", "classification": "official"}
    },
    {
        "id": "doc_6",
        "content": "Consular services include passport renewal, visa applications, notarization of documents, and assistance to nationals abroad. Emergency consular assistance is available 24/7 for citizens in distress.",
        "score": 0.83,
        "metadata": {"title": "Consular Services Guide", "type": "service_document", "country": "Canada", "date": "2024-02-05", "classification": "public"}
    },
    {
        "id": "doc_7",
        "content": "The peace negotiation process requires careful mediation between conflicting parties. Diplomatic channels must remain open to facilitate dialogue and find sustainable solutions to regional conflicts.",
        "score": 0.90,
        "metadata": {"title": "Peace Mediation Guidelines", "type": "policy_document", "country": "Switzerland", "date": "2024-01-30", "classification": "confidential"}
    },
    {
        "id": "doc_8",
        "content": "Cultural exchange programs promote mutual understanding between nations. Educational scholarships, artist residencies, and language learning initiatives strengthen people-to-people connections.",
        "score": 0.81,
        "metadata": {"title": "Cultural Diplomacy Programs", "type": "program_document", "country": "Germany", "date": "2024-02-15", "classification": "public"}
    },
    {
        "id": "doc_9",
        "content": "Climate change negotiations at the international level require coordinated diplomatic efforts. Small island developing states face existential threats from rising sea levels and extreme weather events.",
        "score": 0.89,
        "metadata": {"title": "Climate Diplomacy Strategy", "type": "policy_document", "country": "Maldives", "date": "2024-03-01", "classification": "public"}
    },
    {
        "id": "doc_10",
        "content": "Multilateral organizations play a crucial role in global governance. The United Nations, World Trade Organization, and regional bodies facilitate international cooperation and conflict resolution.",
        "score": 0.86,
        "metadata": {"title": "Multilateral Diplomacy", "type": "analysis_report", "country": "International", "date": "2024-02-28", "classification": "public"}
    },
    {
        "id": "doc_11",
        "content": "Economic sanctions are diplomatic tools used to influence state behavior. They can target specific individuals, entities, or entire economic sectors. The effectiveness of sanctions depends on international coordination.",
        "score": 0.84,
        "metadata": {"title": "Economic Sanctions Analysis", "type": "policy_analysis", "country": "USA", "date": "2024-03-10", "classification": "restricted"}
    },
    {
        "id": "doc_12",
        "content": "Diplomatic protocol governs the formal rules of etiquette and precedence in international relations. Proper protocol ensures smooth diplomatic interactions and prevents misunderstandings.",
        "score": 0.82,
        "metadata": {"title": "Diplomatic Protocol Manual", "type": "manual", "country": "UK", "date": "2024-01-20", "classification": "official"}
    }
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DiploTools Document Processing API",
        "version": "1.0.0",
        "timestamp": "2024-01-20T10:00:00Z"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "DiploTools Document Processing API", "status": "running"}

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8', errors='ignore')
    
    # Generate unique document ID
    doc_id = f"uploaded_{hashlib.md5(f'{file.filename}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"
    
    # Store the document
    doc_info = DocumentInfo(
        id=doc_id,
        filename=file.filename,
        uploaded_at=datetime.now().isoformat() + "Z",
        size=len(content),
        content=content_str
    )
    uploaded_documents.append(doc_info)
    
    # Also add to search documents for search functionality
    search_doc = {
        "id": doc_id,
        "content": content_str[:500] + "..." if len(content_str) > 500 else content_str,  # Truncate for search
        "score": 0.95,
        "metadata": {
            "title": file.filename,
            "type": "uploaded_document",
            "country": "User Upload",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "classification": "user_uploaded"
        }
    }
    mock_documents.append(search_doc)
    
    return {
        "message": "Document uploaded and processed successfully",
        "document_id": doc_id,
        "filename": file.filename,
        "size": len(content),
        "chunks_created": max(1, len(content_str) // 100),  # Estimate chunks
        "processing_time": "1.23s"
    }

@app.post("/search")
async def search_documents(request: SearchRequest):
    """Search documents using hybrid search"""
    # Mock search results based on query
    results = []
    for doc in mock_documents:
        if any(word.lower() in doc["content"].lower() for word in request.query.split()):
            results.append(SearchResult(**doc))
    
    # Limit results
    results = results[:request.limit]
    
    return {
        "query": request.query,
        "search_type": request.search_type,
        "total_results": len(results),
        "results": [result.dict() for result in results],
        "processing_time": "0.45s"
    }

@app.get("/search")
async def search_documents_get(
    query: str,
    search_type: str = "hybrid",
    limit: int = 5
):
    """Search documents using GET method"""
    request = SearchRequest(query=query, search_type=search_type, limit=limit)
    return await search_documents(request)

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_documents": 25,
        "total_chunks": 150,
        "total_embeddings": 150,
        "database_size": "2.5MB",
        "cache_hit_rate": 0.85,
        "avg_search_time": "0.45s",
        "uptime": "2h 30m",
        "system_health": "excellent"
    }

@app.get("/documents")
async def list_documents(limit: int = 10, offset: int = 0):
    """List uploaded documents"""
    # Combine static mock documents with uploaded documents
    static_docs = [
        {"id": "doc_1", "filename": "diplomatic_protocol.md", "uploaded_at": "2024-01-20T09:00:00Z"},
        {"id": "doc_2", "filename": "international_law.pdf", "uploaded_at": "2024-01-20T09:15:00Z"},
        {"id": "doc_3", "filename": "trade_agreements.docx", "uploaded_at": "2024-01-20T09:30:00Z"},
        {"id": "doc_4", "filename": "tunisia_eu_trade.pdf", "uploaded_at": "2024-03-20T10:00:00Z"},
        {"id": "doc_5", "filename": "credential_ceremony.docx", "uploaded_at": "2024-01-25T11:00:00Z"},
        {"id": "doc_6", "filename": "consular_services.md", "uploaded_at": "2024-02-05T12:00:00Z"},
        {"id": "doc_7", "filename": "peace_mediation.pdf", "uploaded_at": "2024-01-30T13:00:00Z"},
        {"id": "doc_8", "filename": "cultural_diplomacy.docx", "uploaded_at": "2024-02-15T14:00:00Z"},
        {"id": "doc_9", "filename": "climate_strategy.pdf", "uploaded_at": "2024-03-01T15:00:00Z"},
        {"id": "doc_10", "filename": "multilateral_analysis.md", "uploaded_at": "2024-02-28T16:00:00Z"},
        {"id": "doc_11", "filename": "sanctions_analysis.pdf", "uploaded_at": "2024-03-10T17:00:00Z"},
        {"id": "doc_12", "filename": "protocol_manual.docx", "uploaded_at": "2024-01-20T18:00:00Z"}
    ]
    
    # Add uploaded documents
    uploaded_docs = [
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at
        }
        for doc in uploaded_documents
    ]
    
    # Combine all documents
    all_documents = static_docs + uploaded_docs
    total_count = len(all_documents)
    
    # Apply pagination
    paginated_docs = all_documents[offset:offset + limit]
    
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "documents": paginated_docs
    }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    return {
        "message": f"Document {document_id} deleted successfully",
        "document_id": document_id
    }

if __name__ == "__main__":
    print("Starting DiploTools Mock API Server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")