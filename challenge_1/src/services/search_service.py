import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import hashlib
from datetime import datetime

from services.embedding_service import EmbeddingService
from database.connection import DatabaseManager
from models.schemas import SearchResult
from utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)

class SearchService:
    """Service for semantic and hybrid document search"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.embedding_service = EmbeddingService()
        self.text_processor = TextProcessor()
        
        # Search configuration
        self.semantic_weight = 0.7
        self.keyword_weight = 0.3
        self.min_relevance_score = 0.1
        self.context_window = 200  # Characters for context preview
    
    async def hybrid_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword approaches"""
        try:
            logger.info(f"Performing hybrid search for: '{query}' (limit: {limit})")
            
            # Check cache first
            cache_key = self._get_search_cache_key(query, "hybrid", limit)
            cached_results = await self.db_manager.get_cached_search_results(cache_key)
            if cached_results:
                logger.info("Returning cached search results")
                return [SearchResult(**result) for result in cached_results]
            
            # Perform parallel searches
            semantic_task = asyncio.create_task(self.semantic_search(query, limit * 2))
            keyword_task = asyncio.create_task(self.keyword_search(query, limit * 2))
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic search failed: {semantic_results}")
                semantic_results = []
            
            if isinstance(keyword_results, Exception):
                logger.error(f"Keyword search failed: {keyword_results}")
                keyword_results = []
            
            # Combine and rank results
            combined_results = self._combine_search_results(
                semantic_results, keyword_results, query
            )
            
            # Limit results
            final_results = combined_results[:limit]
            
            # Cache results
            await self._cache_search_results(cache_key, query, "hybrid", final_results)
            
            logger.info(f"Hybrid search returned {len(final_results)} results")
            return final_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            raise
    
    async def semantic_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform semantic search using vector similarity"""
        try:
            logger.info(f"Performing semantic search for: '{query}' (limit: {limit})")
            
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_single_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Search database
            raw_results = await self.db_manager.semantic_search(query_embedding, limit)
            
            # Convert to SearchResult objects
            search_results = []
            for result in raw_results:
                search_result = self._create_search_result(
                    result, query, search_type="semantic"
                )
                if search_result.relevance_score >= self.min_relevance_score:
                    search_results.append(search_result)
            
            logger.info(f"Semantic search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise
    
    async def keyword_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform keyword-based search"""
        try:
            logger.info(f"Performing keyword search for: '{query}' (limit: {limit})")
            
            # Search database
            raw_results = await self.db_manager.keyword_search(query, limit)
            
            # Convert to SearchResult objects
            search_results = []
            for result in raw_results:
                search_result = self._create_search_result(
                    result, query, search_type="keyword"
                )
                if search_result.relevance_score >= self.min_relevance_score:
                    search_results.append(search_result)
            
            logger.info(f"Keyword search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {str(e)}")
            raise
    
    def _create_search_result(self, db_result: Dict[str, Any], query: str, search_type: str) -> SearchResult:
        """Create SearchResult object from database result"""
        content = db_result['content']
        keywords = db_result.get('keywords', [])
        
        # Find matched keywords
        query_words = set(query.lower().split())
        matched_keywords = [kw for kw in keywords if kw.lower() in query_words]
        
        # Generate context preview
        context_preview = self._generate_context_preview(content, query)
        
        # Normalize relevance score
        relevance_score = float(db_result.get('relevance_score', 0.0))
        if search_type == "keyword" and relevance_score > 1.0:
            # PostgreSQL ts_rank can return values > 1, normalize to 0-1
            relevance_score = min(relevance_score / 10.0, 1.0)
        
        return SearchResult(
            chunk_id=db_result['chunk_id'],
            document_id=db_result['document_id'],
            filename=db_result['filename'],
            content=content,
            relevance_score=relevance_score,
            keywords_matched=matched_keywords,
            context_preview=context_preview,
            chunk_index=db_result.get('chunk_index', 0)
        )
    
    def _combine_search_results(
        self, 
        semantic_results: List[SearchResult], 
        keyword_results: List[SearchResult], 
        query: str
    ) -> List[SearchResult]:
        """Combine and rank results from semantic and keyword searches"""
        # Create a map of chunk_id to results for deduplication
        results_map = {}
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result.chunk_id
            if chunk_id not in results_map:
                # Weight semantic score
                result.relevance_score = result.relevance_score * self.semantic_weight
                results_map[chunk_id] = result
            else:
                # Combine scores if duplicate
                existing = results_map[chunk_id]
                existing.relevance_score += result.relevance_score * self.semantic_weight
        
        # Add keyword results
        for result in keyword_results:
            chunk_id = result.chunk_id
            if chunk_id not in results_map:
                # Weight keyword score
                result.relevance_score = result.relevance_score * self.keyword_weight
                results_map[chunk_id] = result
            else:
                # Combine scores if duplicate
                existing = results_map[chunk_id]
                existing.relevance_score += result.relevance_score * self.keyword_weight
                # Merge matched keywords
                existing.keywords_matched = list(set(
                    existing.keywords_matched + result.keywords_matched
                ))
        
        # Convert back to list and sort by relevance
        combined_results = list(results_map.values())
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Apply additional ranking factors
        self._apply_ranking_boost(combined_results, query)
        
        return combined_results
    
    def _apply_ranking_boost(self, results: List[SearchResult], query: str):
        """Apply additional ranking factors to search results"""
        query_words = set(query.lower().split())
        
        for result in results:
            boost_factor = 1.0
            
            # Boost for exact phrase matches
            if query.lower() in result.content.lower():
                boost_factor *= 1.2
            
            # Boost for multiple keyword matches
            matched_count = len(result.keywords_matched)
            if matched_count > 1:
                boost_factor *= (1.0 + 0.1 * matched_count)
            
            # Boost for title/header keywords (if content starts with common header patterns)
            content_start = result.content[:100].lower()
            if any(word in content_start for word in query_words):
                boost_factor *= 1.1
            
            # Apply boost
            result.relevance_score *= boost_factor
        
        # Re-sort after boosting
        results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    def _generate_context_preview(self, content: str, query: str, max_length: int = None) -> str:
        """Generate context preview highlighting query terms"""
        if max_length is None:
            max_length = self.context_window
        
        query_words = query.lower().split()
        content_lower = content.lower()
        
        # Find the best position to show context
        best_pos = 0
        max_matches = 0
        
        # Look for position with most query word matches
        for i in range(0, len(content) - max_length + 1, 50):
            window = content_lower[i:i + max_length]
            matches = sum(1 for word in query_words if word in window)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        
        # Extract context window
        context = content[best_pos:best_pos + max_length]
        
        # Add ellipsis if truncated
        if best_pos > 0:
            context = "..." + context
        if best_pos + max_length < len(content):
            context = context + "..."
        
        return context.strip()
    
    def _get_search_cache_key(self, query: str, search_type: str, limit: int) -> str:
        """Generate cache key for search query"""
        cache_string = f"{query}:{search_type}:{limit}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _cache_search_results(self, cache_key: str, query: str, search_type: str, results: List[SearchResult]):
        """Cache search results"""
        try:
            # Convert SearchResult objects to dictionaries for caching
            results_dict = [result.dict() for result in results]
            
            await self.db_manager.cache_search_results(
                query_hash=cache_key,
                query_text=query,
                search_type=search_type,
                results=results_dict,
                ttl_hours=1
            )
        except Exception as e:
            logger.warning(f"Failed to cache search results: {str(e)}")
    
    async def get_similar_documents(self, document_id: int, limit: int = 5) -> List[SearchResult]:
        """Find documents similar to a given document"""
        try:
            # Get document chunks
            chunks = await self.db_manager.get_document_chunks(document_id)
            
            if not chunks:
                return []
            
            # Use the first chunk as representative content
            representative_text = chunks[0]['chunk_text']
            
            # Perform semantic search with the representative text
            results = await self.semantic_search(representative_text, limit + 10)
            
            # Filter out chunks from the same document
            filtered_results = [
                result for result in results 
                if result.document_id != document_id
            ]
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            # Extract keywords from existing documents that match partial query
            suggestions = []
            
            if len(partial_query) >= 2:
                # Perform a quick keyword search to find related terms
                results = await self.keyword_search(partial_query, 20)
                
                # Extract unique keywords from results
                all_keywords = set()
                for result in results:
                    all_keywords.update(result.keywords_matched)
                
                # Filter and sort suggestions
                suggestions = [
                    kw for kw in all_keywords 
                    if partial_query.lower() in kw.lower()
                ][:limit]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating search suggestions: {str(e)}")
            return []
    
    def configure_search_weights(self, semantic_weight: float, keyword_weight: float):
        """Configure search result weighting"""
        total_weight = semantic_weight + keyword_weight
        self.semantic_weight = semantic_weight / total_weight
        self.keyword_weight = keyword_weight / total_weight
        
        logger.info(f"Search weights updated: semantic={self.semantic_weight:.2f}, keyword={self.keyword_weight:.2f}")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search service statistics"""
        return {
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "min_relevance_score": self.min_relevance_score,
            "context_window": self.context_window,
            "embedding_service_info": self.embedding_service.get_model_info()
        }