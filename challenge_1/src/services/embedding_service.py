import asyncio
import logging
from typing import List, Optional, Dict, Any
import os
import hashlib
import json
from datetime import datetime, timedelta

try:
    import openai
except ImportError:
    openai = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings with multiple providers and fallback"""
    
    def __init__(self):
        self.primary_provider = "openai"  # or "gemini"
        self.fallback_provider = "local"
        self.cache = {}  # Simple in-memory cache
        self.rate_limit_delay = 0.1  # Seconds between API calls
        
        # Initialize providers
        self._init_openai()
        self._init_local_model()
        
        # Rate limiting
        self.last_api_call = datetime.now() - timedelta(seconds=1)
        self.api_calls_count = 0
        self.max_calls_per_minute = 500
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        self.openai_client = None
        self.openai_model = "text-embedding-3-large"
        
        if openai:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI embedding service initialized")
            else:
                logger.warning("OpenAI API key not found in environment variables")
        else:
            logger.warning("OpenAI library not installed")
    
    def _init_local_model(self):
        """Initialize local sentence transformer model"""
        self.local_model = None
        self.local_model_name = "all-MiniLM-L6-v2"
        
        if SentenceTransformer:
            try:
                self.local_model = SentenceTransformer(self.local_model_name)
                logger.info(f"Local embedding model {self.local_model_name} initialized")
            except Exception as e:
                logger.error(f"Failed to load local model: {str(e)}")
        else:
            logger.warning("sentence-transformers library not installed")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts with fallback mechanism"""
        if not texts:
            return []
        
        try:
            # Try primary provider first
            if self.primary_provider == "openai" and self.openai_client:
                return await self._generate_openai_embeddings(texts)
            elif self.primary_provider == "gemini":
                return await self._generate_gemini_embeddings(texts)
            else:
                raise Exception(f"Primary provider {self.primary_provider} not available")
        
        except Exception as e:
            logger.warning(f"Primary embedding provider failed: {str(e)}. Falling back to local model.")
            
            # Fallback to local model
            if self.local_model:
                return await self._generate_local_embeddings(texts)
            else:
                raise Exception("No embedding providers available")
    
    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        embeddings = []
        
        # Process in batches to respect rate limits
        batch_size = 100  # OpenAI allows up to 2048 inputs per request
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Check cache first
            cached_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for j, text in enumerate(batch):
                cache_key = self._get_cache_key(text, "openai")
                if cache_key in self.cache:
                    cached_embeddings.append((i + j, self.cache[cache_key]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i + j)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                await self._rate_limit_check()
                
                try:
                    response = await self.openai_client.embeddings.create(
                        model=self.openai_model,
                        input=uncached_texts
                    )
                    
                    # Cache and collect results
                    for j, embedding_data in enumerate(response.data):
                        embedding = embedding_data.embedding
                        text = uncached_texts[j]
                        original_index = uncached_indices[j]
                        
                        # Cache the result
                        cache_key = self._get_cache_key(text, "openai")
                        self.cache[cache_key] = embedding
                        
                        cached_embeddings.append((original_index, embedding))
                    
                    self.api_calls_count += 1
                    logger.info(f"Generated {len(uncached_texts)} OpenAI embeddings")
                    
                except Exception as e:
                    logger.error(f"OpenAI API error: {str(e)}")
                    raise
            
            # Sort by original index and add to results
            cached_embeddings.sort(key=lambda x: x[0])
            batch_embeddings = [emb for _, emb in cached_embeddings]
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _generate_gemini_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Google Gemini API (placeholder)"""
        # This would implement Gemini API integration
        logger.info("Gemini embedding not implemented, using local model")
        return await self._generate_local_embeddings(texts)
    
    async def _generate_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local sentence transformer model"""
        if not self.local_model:
            raise Exception("Local embedding model not available")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.local_model.encode, 
                texts
            )
            
            # Convert to list of lists
            embeddings_list = [emb.tolist() for emb in embeddings]
            
            # Cache results
            for text, embedding in zip(texts, embeddings_list):
                cache_key = self._get_cache_key(text, "local")
                self.cache[cache_key] = embedding
            
            logger.info(f"Generated {len(texts)} local embeddings")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Local embedding generation failed: {str(e)}")
            raise
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def _get_cache_key(self, text: str, provider: str) -> str:
        """Generate cache key for text and provider"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{provider}:{text_hash}"
    
    async def _rate_limit_check(self):
        """Check and enforce rate limits"""
        now = datetime.now()
        time_since_last_call = (now - self.last_api_call).total_seconds()
        
        # Enforce minimum delay between calls
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            await asyncio.sleep(sleep_time)
        
        # Reset counter every minute
        if (now - self.last_api_call).total_seconds() > 60:
            self.api_calls_count = 0
        
        # Check if we're hitting rate limits
        if self.api_calls_count >= self.max_calls_per_minute:
            sleep_time = 60 - (now - self.last_api_call).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self.api_calls_count = 0
        
        self.last_api_call = now
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        return {
            "primary_provider": self.primary_provider,
            "fallback_provider": self.fallback_provider,
            "openai_available": self.openai_client is not None,
            "local_model_available": self.local_model is not None,
            "openai_model": self.openai_model if self.openai_client else None,
            "local_model": self.local_model_name if self.local_model else None,
            "cache_size": len(self.cache)
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "api_calls_count": self.api_calls_count,
            "last_api_call": self.last_api_call.isoformat() if self.last_api_call else None
        }
    
    async def warmup_cache(self, sample_texts: List[str]):
        """Warm up cache with sample texts"""
        logger.info(f"Warming up embedding cache with {len(sample_texts)} samples")
        await self.generate_embeddings(sample_texts)
        logger.info("Cache warmup complete")
    
    def set_rate_limits(self, calls_per_minute: int, delay_seconds: float):
        """Configure rate limiting parameters"""
        self.max_calls_per_minute = calls_per_minute
        self.rate_limit_delay = delay_seconds
        logger.info(f"Rate limits updated: {calls_per_minute} calls/min, {delay_seconds}s delay")