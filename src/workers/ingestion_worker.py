"""
Ingestion Worker - Background document ingestion
Handles document updates without blocking the main bot

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

from ..config import config

logger = logging.getLogger(__name__)

# Import Redis (optional)
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


@dataclass
class IngestionJob:
    """A document ingestion job"""
    job_id: str
    job_type: str  # 'directory', 'url', 'text'
    source: str  # Path, URL, or text content
    metadata: Dict[str, Any]
    created_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'source': self.source,
            'metadata': self.metadata,
            'created_at': self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IngestionJob':
        return cls(
            job_id=data['job_id'],
            job_type=data['job_type'],
            source=data['source'],
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', time.time()),
        )


class IngestionWorker:
    """
    Background document ingestion worker.
    
    Handles:
    - Directory ingestion (scrape + ingest)
    - URL ingestion (fetch + process)
    - Text ingestion (direct add to vector store)
    
    Benefits:
    - Non-blocking document updates
    - Scheduled re-ingestion support
    - Progress tracking
    """
    
    # Queue name
    INGESTION_QUEUE = "rag:queue:ingestion"
    STATUS_PREFIX = "rag:ingestion:status:"
    
    # Timeouts
    POLL_TIMEOUT = 10
    STATUS_TTL = 3600  # 1 hour
    
    def __init__(self, rag_pipeline=None, worker_id: str = "ingestion-1"):
        """
        Initialize ingestion worker.
        
        Args:
            rag_pipeline: Initialized RAGPipeline instance
            worker_id: Unique identifier for this worker
        """
        self.rag_pipeline = rag_pipeline
        self.worker_id = worker_id
        self.running = False
        self.redis_client = None
        
        # Initialize Redis connection
        if HAS_REDIS and config.REDIS_ENABLED and config.REDIS_URL:
            try:
                self.redis_client = redis.from_url(
                    config.REDIS_URL,
                    decode_responses=True,
                )
                self.redis_client.ping()
                logger.info(f"IngestionWorker {worker_id} connected to Redis")
            except Exception as e:
                logger.error(f"IngestionWorker Redis connection failed: {e}")
                self.redis_client = None
        
        # Stats
        self.stats = {
            'jobs_processed': 0,
            'jobs_failed': 0,
            'documents_ingested': 0,
            'total_processing_time_ms': 0,
        }
    
    def enqueue_directory(
        self,
        job_id: str,
        directory_path: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Enqueue a directory for ingestion"""
        return self._enqueue_job(IngestionJob(
            job_id=job_id,
            job_type='directory',
            source=directory_path,
            metadata=metadata or {},
            created_at=time.time(),
        ))
    
    def enqueue_url(
        self,
        job_id: str,
        url: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Enqueue a URL for ingestion"""
        return self._enqueue_job(IngestionJob(
            job_id=job_id,
            job_type='url',
            source=url,
            metadata=metadata or {},
            created_at=time.time(),
        ))
    
    def enqueue_text(
        self,
        job_id: str,
        text: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Enqueue text for direct ingestion"""
        return self._enqueue_job(IngestionJob(
            job_id=job_id,
            job_type='text',
            source=text,
            metadata=metadata or {},
            created_at=time.time(),
        ))
    
    def _enqueue_job(self, job: IngestionJob) -> bool:
        """Enqueue an ingestion job"""
        if not self.redis_client:
            logger.warning("Redis not available, cannot enqueue job")
            return False
        
        try:
            self.redis_client.rpush(self.INGESTION_QUEUE, json.dumps(job.to_dict()))
            self._update_status(job.job_id, 'queued')
            logger.debug(f"Enqueued ingestion job {job.job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False
    
    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an ingestion job"""
        if not self.redis_client:
            return None
        
        try:
            status_key = f"{self.STATUS_PREFIX}{job_id}"
            status = self.redis_client.get(status_key)
            if status:
                return json.loads(status)
            return None
        except Exception:
            return None
    
    def _update_status(self, job_id: str, status: str, **kwargs):
        """Update job status"""
        if not self.redis_client:
            return
        
        status_data = {
            'status': status,
            'updated_at': time.time(),
            **kwargs,
        }
        
        try:
            status_key = f"{self.STATUS_PREFIX}{job_id}"
            self.redis_client.setex(status_key, self.STATUS_TTL, json.dumps(status_data))
        except Exception as e:
            logger.debug(f"Failed to update status: {e}")
    
    def _process_job(self, job: IngestionJob) -> Dict[str, Any]:
        """Process a single ingestion job"""
        start_time = time.time()
        self._update_status(job.job_id, 'processing')
        
        try:
            if not self.rag_pipeline:
                raise RuntimeError("RAG pipeline not initialized")
            
            documents_count = 0
            
            if job.job_type == 'directory':
                # Ingest from directory
                documents_count = self.rag_pipeline.ingest_documents(job.source)
                
            elif job.job_type == 'url':
                # Fetch and ingest URL
                # This would require implementing URL fetching
                # For now, log warning
                logger.warning("URL ingestion not yet implemented")
                documents_count = 0
                
            elif job.job_type == 'text':
                # Direct text ingestion
                self.rag_pipeline.learn_text(job.source)
                documents_count = 1
            
            processing_time = (time.time() - start_time) * 1000
            self.stats['jobs_processed'] += 1
            self.stats['documents_ingested'] += documents_count
            self.stats['total_processing_time_ms'] += processing_time
            
            self._update_status(job.job_id, 'completed',
                              documents_count=documents_count,
                              processing_time_ms=processing_time)
            
            return {
                'success': True,
                'job_id': job.job_id,
                'documents_count': documents_count,
                'processing_time_ms': processing_time,
            }
            
        except Exception as e:
            self.stats['jobs_failed'] += 1
            logger.error(f"Ingestion job {job.job_id} failed: {e}")
            
            self._update_status(job.job_id, 'failed', error=str(e))
            
            return {
                'success': False,
                'job_id': job.job_id,
                'error': str(e),
            }
    
    async def run(self):
        """Main worker loop"""
        if not self.redis_client:
            logger.error("Cannot start worker: Redis not available")
            return
        
        self.running = True
        logger.info(f"IngestionWorker {self.worker_id} starting...")
        
        while self.running:
            try:
                # Blocking pop from queue
                job_data = self.redis_client.blpop(self.INGESTION_QUEUE, timeout=self.POLL_TIMEOUT)
                
                if job_data:
                    _, job_json = job_data
                    job = IngestionJob.from_dict(json.loads(job_json))
                    
                    logger.info(f"Worker {self.worker_id} processing ingestion job {job.job_id}")
                    
                    # Process the job
                    result = self._process_job(job)
                    
                    logger.info(f"Ingestion job {job.job_id} completed: {result.get('documents_count', 0)} docs")
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"IngestionWorker {self.worker_id} stopped")
    
    def stop(self):
        """Stop the worker"""
        self.running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            **self.stats,
            'worker_id': self.worker_id,
            'running': self.running,
        }


async def start_ingestion_worker(rag_pipeline, worker_id: str = "ingestion-1"):
    """
    Start an ingestion worker.
    
    Usage:
        # In a separate process/container:
        from src.rag import RAGPipeline
        from src.workers import start_ingestion_worker
        
        pipeline = RAGPipeline()
        asyncio.run(start_ingestion_worker(pipeline, "ingestion-1"))
    """
    worker = IngestionWorker(rag_pipeline=rag_pipeline, worker_id=worker_id)
    await worker.run()
