"""
Vector database handler using Qdrant Cloud (Production-grade)
Fallback to local pickle storage if Qdrant is not configured
Updated to use NEW google-genai SDK for embeddings

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import logging
import hashlib
import os
import pickle
import time
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

from google import genai

from ..config import config

logger = logging.getLogger(__name__)

# Import cache (avoid circular import)
try:
    from .cache import RedisCache
except ImportError:
    RedisCache = None

# Import Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    logger.warning("qdrant-client not installed. Install with: pip install qdrant-client")


class VectorStore:
    """
    Production-grade vector store using Qdrant Cloud.
    Falls back to local pickle storage if Qdrant is not configured.
    
    Features:
    - Qdrant Cloud integration for production
    - Batch document insertion
    - Metadata filtering
    - Automatic collection creation
    - Embedding caching via Redis
    """
    
    def __init__(self):
        """Initialize vector store with Qdrant or fallback to pickle"""
        # Set API key in environment for Gemini
        if config.GEMINI_API_KEY:
            os.environ['GEMINI_API_KEY'] = config.GEMINI_API_KEY
        
        # Initialize Gemini client for embeddings
        self.gemini_client = genai.Client()
        
        # Initialize cache if available
        self.cache = RedisCache() if (config.REDIS_ENABLED and RedisCache) else None
        
        # Determine storage backend
        self.use_qdrant = HAS_QDRANT and config.QDRANT_URL and config.QDRANT_API_KEY
        
        if self.use_qdrant:
            self._init_qdrant()
        else:
            self._init_pickle_fallback()
    
    def _init_qdrant(self):
        """Initialize Qdrant Cloud connection"""
        try:
            self.client = QdrantClient(
                url=config.QDRANT_URL,
                api_key=config.QDRANT_API_KEY,
                timeout=30,
            )
            self.collection_name = config.QDRANT_COLLECTION_NAME
            self._ensure_collection()
            
            # Get collection info
            info = self.client.get_collection(self.collection_name)
            doc_count = info.points_count
            logger.info(f"Connected to Qdrant Cloud: {config.QDRANT_URL}")
            logger.info(f"Collection '{self.collection_name}' has {doc_count} documents")
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            logger.warning("Falling back to local pickle storage")
            self.use_qdrant = False
            self._init_pickle_fallback()
    
    def _init_pickle_fallback(self):
        """Initialize legacy pickle-based storage (fallback)"""
        logger.warning("Using pickle-based storage (NOT recommended for production)")
        logger.warning("Set QDRANT_URL and QDRANT_API_KEY for production use")
        
        self.persist_dir = Path(config.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.persist_dir / "vectors.pkl"
        
        if self.db_file.exists():
            self._load_pickle_db()
        else:
            self.documents = []
            self.embeddings = []
            self.metadatas = []
            self.ids = []
        
        logger.info(f"Initialized pickle vector store with {len(self.documents)} documents")
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists with correct configuration"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            logger.info(f"Creating Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=config.QDRANT_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created collection with vector size {config.QDRANT_VECTOR_SIZE}")
    
    def _load_pickle_db(self):
        """Load pickle database from disk"""
        try:
            with open(self.db_file, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.embeddings = data.get('embeddings', [])
                self.metadatas = data.get('metadatas', [])
                self.ids = data.get('ids', [])
        except Exception as e:
            logger.error(f"Failed to load pickle DB: {e}")
            self.documents = []
            self.embeddings = []
            self.metadatas = []
            self.ids = []
    
    def _save_pickle_db(self):
        """Save pickle database to disk"""
        with open(self.db_file, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'embeddings': self.embeddings,
                'metadatas': self.metadatas,
                'ids': self.ids
            }, f)
    
    def _get_embedding(self, text: str, retries: int = 2) -> List[float]:
        """Get embedding for text using Gemini SDK with retry logic"""
        # Check cache first
        if self.cache:
            cached = self.cache.get_embedding(text)
            if cached:
                logger.debug("Embedding cache hit")
                return cached
        
        for attempt in range(retries + 1):
            try:
                result = self.gemini_client.models.embed_content(
                    model=config.EMBEDDING_MODEL,
                    contents=text,
                )
                embedding = result.embeddings[0].values
                
                # Cache the embedding
                if self.cache:
                    self.cache.set_embedding(text, embedding)
                
                return embedding
                
            except Exception as e:
                if attempt < retries:
                    logger.warning(f"Embedding retry {attempt + 1}/{retries}: {e}")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                logger.error(f"Embedding failed after {retries + 1} attempts: {e}")
                raise
    
    def _get_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batches.
        More efficient than individual calls.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call
            
        Returns:
            List of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Check cache for each text in batch
            batch_embeddings = []
            texts_to_embed = []
            cache_indices = []
            
            for j, text in enumerate(batch):
                if self.cache:
                    cached = self.cache.get_embedding(text)
                    if cached:
                        batch_embeddings.append((j, cached))
                        continue
                texts_to_embed.append(text)
                cache_indices.append(j)
            
            # Get embeddings for uncached texts
            if texts_to_embed:
                try:
                    result = self.gemini_client.models.embed_content(
                        model=config.EMBEDDING_MODEL,
                        contents=texts_to_embed,
                    )
                    
                    for idx, embedding in zip(cache_indices, result.embeddings):
                        emb_values = embedding.values
                        batch_embeddings.append((idx, emb_values))
                        
                        # Cache the embedding
                        if self.cache:
                            self.cache.set_embedding(texts_to_embed[cache_indices.index(idx)], emb_values)
                            
                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    # Fallback to individual embeddings
                    for idx, text in zip(cache_indices, texts_to_embed):
                        try:
                            emb = self._get_embedding(text)
                            batch_embeddings.append((idx, emb))
                        except Exception:
                            logger.error(f"Failed to embed text at index {idx}")
                            raise
            
            # Sort by original index and extract embeddings
            batch_embeddings.sort(key=lambda x: x[0])
            all_embeddings.extend([emb for _, emb in batch_embeddings])
        
        return all_embeddings
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of text documents to add
            metadatas: Optional metadata for each document
            ids: Optional unique IDs for documents (auto-generated if not provided)
        """
        if not documents:
            logger.warning("No documents provided to add")
            return
        
        # Generate IDs if not provided
        if ids is None:
            ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]
        
        # Generate metadatas if not provided
        if metadatas is None:
            metadatas = [{}] * len(documents)
        
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        
        if self.use_qdrant:
            self._add_documents_qdrant(documents, metadatas, ids)
        else:
            self._add_documents_pickle(documents, metadatas, ids)
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def _add_documents_qdrant(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to Qdrant with batch embeddings"""
        # Get embeddings in batches
        embeddings = self._get_embeddings_batch(documents)
        
        # Prepare points for Qdrant
        points = []
        for doc, emb, meta, doc_id in zip(documents, embeddings, metadatas, ids):
            # Convert string ID to UUID-compatible format
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            
            # Store document text in payload
            payload = {
                "document": doc,
                "original_id": doc_id,
                **meta
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=emb,
                payload=payload
            ))
        
        # Batch upsert to Qdrant
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
                wait=True
            )
            logger.debug(f"Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
    
    def _add_documents_pickle(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to pickle storage"""
        for doc, metadata, doc_id in zip(documents, metadatas, ids):
            embedding = self._get_embedding(doc)
            
            self.documents.append(doc)
            self.embeddings.append(embedding)
            self.metadatas.append(metadata)
            self.ids.append(doc_id)
        
        self._save_pickle_db()
    
    def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return (default from config)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of dicts containing document, metadata, and similarity
        """
        if top_k is None:
            top_k = config.TOP_K_RESULTS
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        
        if self.use_qdrant:
            return self._search_qdrant(query_embedding, top_k, filter_metadata)
        else:
            return self._search_pickle(query_embedding, top_k, filter_metadata)
    
    def _search_qdrant(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search Qdrant collection"""
        # Build filter if provided
        query_filter = None
        if filter_metadata:
            conditions = [
                models.FieldCondition(
                    key=k,
                    match=models.MatchValue(value=v)
                )
                for k, v in filter_metadata.items()
            ]
            query_filter = models.Filter(must=conditions)
        
        # Search Qdrant
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=config.SIMILARITY_THRESHOLD,
        )
        
        # Format results
        formatted_results = []
        for result in results:
            payload = result.payload
            formatted_results.append({
                'document': payload.get('document', ''),
                'metadata': {k: v for k, v in payload.items() if k not in ['document', 'original_id']},
                'similarity': result.score,
                'distance': 1 - result.score
            })
        
        logger.info(f"Found {len(formatted_results)} relevant documents for query (Qdrant)")
        return formatted_results
    
    def _search_pickle(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search pickle storage"""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        if not self.documents:
            logger.warning("No documents in vector store")
            return []
        
        query_vector = np.array(query_embedding).reshape(1, -1)
        doc_vectors = np.array(self.embeddings)
        similarities = cosine_similarity(query_vector, doc_vectors)[0]
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        formatted_results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            
            if similarity >= config.SIMILARITY_THRESHOLD:
                if filter_metadata:
                    match = all(
                        self.metadatas[idx].get(k) == v
                        for k, v in filter_metadata.items()
                    )
                    if not match:
                        continue
                
                formatted_results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadatas[idx],
                    'similarity': similarity,
                    'distance': 1 - similarity
                })
        
        logger.info(f"Found {len(formatted_results)} relevant documents for query (pickle)")
        return formatted_results
    
    def search_all_relevant(
        self,
        query: str,
        top_k: int = 10,
        min_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search with lower threshold for context gathering.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_threshold: Minimum similarity threshold
            
        Returns:
            List of dicts containing document, metadata, and similarity
        """
        if min_threshold is None:
            min_threshold = config.CONTEXT_SEARCH_THRESHOLD
        
        query_embedding = self._get_embedding(query)
        
        if self.use_qdrant:
            # Search with lower threshold
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=min_threshold,
            )
            
            formatted_results = []
            for result in results:
                payload = result.payload
                formatted_results.append({
                    'document': payload.get('document', ''),
                    'metadata': {k: v for k, v in payload.items() if k not in ['document', 'original_id']},
                    'similarity': result.score,
                    'distance': 1 - result.score
                })
            
            logger.info(f"Found {len(formatted_results)} documents with lower threshold ({min_threshold}) (Qdrant)")
            return formatted_results
        else:
            # Pickle fallback
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            if not self.documents:
                return []
            
            query_vector = np.array(query_embedding).reshape(1, -1)
            doc_vectors = np.array(self.embeddings)
            similarities = cosine_similarity(query_vector, doc_vectors)[0]
            
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            formatted_results = []
            for idx in top_indices:
                similarity = float(similarities[idx])
                if similarity >= min_threshold:
                    formatted_results.append({
                        'document': self.documents[idx],
                        'metadata': self.metadatas[idx],
                        'similarity': similarity,
                        'distance': 1 - similarity
                    })
            
            logger.info(f"Found {len(formatted_results)} documents with lower threshold ({min_threshold}) (pickle)")
            return formatted_results
    
    def clear(self) -> None:
        """Clear all documents from the collection"""
        if self.use_qdrant:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            logger.info("Cleared Qdrant collection")
        else:
            self.documents = []
            self.embeddings = []
            self.metadatas = []
            self.ids = []
            self._save_pickle_db()
            logger.info("Cleared pickle vector store")
    
    def get_count(self) -> int:
        """Get the number of documents in the store"""
        if self.use_qdrant:
            try:
                info = self.client.get_collection(self.collection_name)
                return info.points_count
            except Exception as e:
                logger.error(f"Failed to get Qdrant collection count: {e}")
                return 0
        else:
            return len(self.documents)
    
    def health_check(self) -> Dict[str, Any]:
        """Check vector store health status"""
        if self.use_qdrant:
            try:
                info = self.client.get_collection(self.collection_name)
                return {
                    "healthy": True,
                    "backend": "qdrant",
                    "collection": self.collection_name,
                    "document_count": info.points_count,
                    "status": info.status.value if hasattr(info.status, 'value') else str(info.status)
                }
            except Exception as e:
                return {
                    "healthy": False,
                    "backend": "qdrant",
                    "error": str(e)
                }
        else:
            return {
                "healthy": True,
                "backend": "pickle",
                "document_count": len(self.documents),
                "warning": "Using pickle storage - not recommended for production"
            }
    
    def export_to_qdrant(self) -> bool:
        """
        Export pickle data to Qdrant (migration helper).
        Call this to migrate from pickle to Qdrant.
        
        Returns:
            True if successful
        """
        if not HAS_QDRANT or not config.QDRANT_URL or not config.QDRANT_API_KEY:
            logger.error("Qdrant not configured. Set QDRANT_URL and QDRANT_API_KEY")
            return False
        
        # Load pickle data
        if not self.db_file.exists():
            logger.warning("No pickle database to export")
            return False
        
        self._load_pickle_db()
        
        if not self.documents:
            logger.warning("No documents in pickle database")
            return False
        
        logger.info(f"Exporting {len(self.documents)} documents to Qdrant...")
        
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY,
        )
        
        # Ensure collection exists
        collections = qdrant_client.get_collections().collections
        exists = any(c.name == config.QDRANT_COLLECTION_NAME for c in collections)
        
        if not exists:
            qdrant_client.create_collection(
                collection_name=config.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=config.QDRANT_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
        
        # Prepare points
        points = []
        for doc, emb, meta, doc_id in zip(self.documents, self.embeddings, self.metadatas, self.ids):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            payload = {
                "document": doc,
                "original_id": doc_id,
                **meta
            }
            points.append(PointStruct(
                id=point_id,
                vector=emb,
                payload=payload
            ))
        
        # Batch upsert
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            qdrant_client.upsert(
                collection_name=config.QDRANT_COLLECTION_NAME,
                points=batch,
                wait=True
            )
            logger.info(f"Exported batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
        
        logger.info(f"Successfully exported {len(self.documents)} documents to Qdrant")
        return True
