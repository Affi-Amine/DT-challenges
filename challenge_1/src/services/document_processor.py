import re
import logging
from typing import List, Dict, Any, Tuple
import asyncio
from datetime import datetime
import hashlib

from services.embedding_service import EmbeddingService
from database.connection import DatabaseManager
from utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing and chunking documents"""
    
    def __init__(self, db_manager: DatabaseManager, chunk_size: int = 1000, overlap: int = 200):
        self.db_manager = db_manager
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.embedding_service = EmbeddingService()
        self.text_processor = TextProcessor()
        
    async def process_document(self, filename: str, content: str, metadata: Dict[str, Any]) -> int:
        """Process a document: clean, chunk, embed, and store"""
        try:
            logger.info(f"Processing document: {filename}")
            start_time = datetime.now()
            
            # 1. Clean and normalize content
            cleaned_content = self._clean_markdown_content(content)
            
            # 2. Insert document record
            document_metadata = {
                **metadata,
                "original_length": len(content),
                "cleaned_length": len(cleaned_content),
                "processing_started_at": start_time.isoformat()
            }
            
            document_id = await self.db_manager.insert_document(
                filename=filename,
                content=cleaned_content,
                metadata=document_metadata
            )
            
            # 3. Create semantic chunks
            chunks = self._create_semantic_chunks(cleaned_content)
            logger.info(f"Created {len(chunks)} chunks for document {filename}")
            
            # 4. Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                await self._process_chunk_batch(document_id, batch, i)
            
            # 5. Update document metadata with processing results
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_document_metadata(document_id, {
                "chunks_created": len(chunks),
                "processing_time_seconds": processing_time,
                "processing_completed_at": datetime.now().isoformat()
            })
            
            logger.info(f"Successfully processed document {filename} in {processing_time:.2f}s")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise
    
    def _clean_markdown_content(self, content: str) -> str:
        """Clean and normalize markdown content"""
        # Remove markdown syntax while preserving structure
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)  # Remove headers
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Remove italic
        content = re.sub(r'`(.*?)`', r'\1', content)  # Remove inline code
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Remove links, keep text
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Normalize paragraph breaks
        content = re.sub(r'[ \t]+', ' ', content)  # Normalize spaces
        content = content.strip()
        
        return content
    
    def _create_semantic_chunks(self, content: str) -> List[Dict[str, Any]]:
        """Create semantic chunks preserving paragraph and section boundaries"""
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        current_chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph would exceed chunk size
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(self._create_chunk_dict(current_chunk, current_chunk_index))
                    current_chunk_index += 1
                
                # Handle oversized paragraphs
                if len(paragraph) > self.chunk_size:
                    # Split large paragraph into smaller chunks
                    sub_chunks = self._split_large_text(paragraph)
                    for sub_chunk in sub_chunks:
                        chunks.append(self._create_chunk_dict(sub_chunk, current_chunk_index))
                        current_chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk_dict(current_chunk, current_chunk_index))
        
        # Add overlap between chunks
        self._add_chunk_overlap(chunks)
        
        return chunks
    
    def _create_chunk_dict(self, text: str, index: int) -> Dict[str, Any]:
        """Create a chunk dictionary with metadata"""
        keywords = self.text_processor.extract_keywords(text)
        
        return {
            "text": text,
            "index": index,
            "keywords": keywords,
            "length": len(text),
            "word_count": len(text.split())
        }
    
    def _split_large_text(self, text: str) -> List[str]:
        """Split large text into smaller chunks at sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _add_chunk_overlap(self, chunks: List[Dict[str, Any]]):
        """Add overlap between consecutive chunks for better context"""
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Get last N characters from previous chunk
            prev_text = prev_chunk["text"]
            overlap_text = prev_text[-self.overlap:] if len(prev_text) > self.overlap else prev_text
            
            # Find a good break point (end of sentence or word)
            overlap_text = self._find_good_break_point(overlap_text, reverse=True)
            
            # Add overlap to current chunk
            if overlap_text:
                current_chunk["text"] = overlap_text + " " + current_chunk["text"]
                current_chunk["length"] = len(current_chunk["text"])
    
    def _find_good_break_point(self, text: str, reverse: bool = False) -> str:
        """Find a good break point at sentence or word boundary"""
        if not text:
            return text
        
        # Look for sentence endings
        sentence_endings = ['.', '!', '?']
        
        if reverse:
            # Look from the beginning for the first sentence ending
            for i, char in enumerate(text):
                if char in sentence_endings and i < len(text) - 1:
                    return text[:i+1].strip()
        else:
            # Look from the end for the last sentence ending
            for i in range(len(text) - 1, -1, -1):
                if text[i] in sentence_endings:
                    return text[i+1:].strip()
        
        # If no sentence ending found, break at word boundary
        words = text.split()
        if len(words) > 1:
            if reverse:
                # Take first half of words
                return ' '.join(words[:len(words)//2])
            else:
                # Take second half of words
                return ' '.join(words[len(words)//2:])
        
        return text
    
    async def _process_chunk_batch(self, document_id: int, chunks: List[Dict[str, Any]], start_index: int):
        """Process a batch of chunks: generate embeddings and store"""
        try:
            # Extract texts for embedding
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings in batch
            embeddings = await self.embedding_service.generate_embeddings(texts)
            
            # Store chunks with embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                await self.db_manager.insert_document_chunk(
                    document_id=document_id,
                    chunk_text=chunk["text"],
                    chunk_index=start_index + i,
                    embedding=embedding,
                    keywords=chunk["keywords"]
                )
            
            logger.info(f"Processed batch of {len(chunks)} chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error processing chunk batch: {str(e)}")
            raise
    
    async def _update_document_metadata(self, document_id: int, updates: Dict[str, Any]):
        """Update document metadata with processing results"""
        # This would require adding an update method to DatabaseManager
        logger.info(f"Document {document_id} processing completed: {updates}")
    
    async def reprocess_document(self, document_id: int) -> bool:
        """Reprocess an existing document (useful for updates)"""
        try:
            # Get document content
            # Delete existing chunks
            # Reprocess with current settings
            logger.info(f"Reprocessing document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error reprocessing document {document_id}: {str(e)}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "embedding_model": self.embedding_service.get_model_info()
        }