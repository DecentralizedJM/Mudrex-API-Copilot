"""
RAG Worker - Background query processor
Handles RAG queries asynchronously for horizontal scaling

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from ..config import config

logger = logging.getLogger(__name__)

# Import Redis (optional)
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


@dataclass
class QueryJob:
    """A query job to be processed"""
    job_id: str
    query: str
    chat_id: str
    user_id: str
    chat_history: list
    mcp_context: Optional[str]
    created_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'query': self.query,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'chat_history': self.chat_history,
            'mcp_context': self.mcp_context,
            'created_at': self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryJob':
        return cls(
            job_id=data['job_id'],
            query=data['query'],
            chat_id=data['chat_id'],
            user_id=data['user_id'],
            chat_history=data.get('chat_history', []),
            mcp_context=data.get('mcp_context'),
            created_at=data.get('created_at', time.time()),
        )


class RAGWorker:
    """
    Background RAG query worker.
    
    Architecture:
        Telegram Bot → Redis Queue → RAG Workers (1..N) → Result Queue → Bot
    
    Benefits:
    - Horizontal scaling (multiple workers)
    - Bot stays responsive
    - Automatic retry on failure
    - Query persistence in Redis
    """
    
    # Queue names
    QUERY_QUEUE = "rag:queue:queries"
    RESULT_QUEUE_PREFIX = "rag:result:"
    
    # Timeouts
    POLL_TIMEOUT = 5  # seconds
    RESULT_TTL = 300  # 5 minutes
    MAX_RETRIES = 3
    
    def __init__(self, rag_pipeline=None, worker_id: str = "worker-1"):
        """
        Initialize RAG worker.
        
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
                logger.info(f"RAGWorker {worker_id} connected to Redis")
            except Exception as e:
                logger.error(f"RAGWorker Redis connection failed: {e}")
                self.redis_client = None
        
        # Stats
        self.stats = {
            'jobs_processed': 0,
            'jobs_failed': 0,
            'total_processing_time_ms': 0,
        }
    
    def enqueue_query(
        self,
        job_id: str,
        query: str,
        chat_id: str,
        user_id: str,
        chat_history: list = None,
        mcp_context: str = None,
    ) -> bool:
        """
        Enqueue a query for background processing.
        
        Args:
            job_id: Unique job identifier
            query: User's query
            chat_id: Chat ID
            user_id: User ID
            chat_history: Optional chat history
            mcp_context: Optional MCP context
            
        Returns:
            True if enqueued successfully
        """
        if not self.redis_client:
            logger.warning("Redis not available, cannot enqueue job")
            return False
        
        job = QueryJob(
            job_id=job_id,
            query=query,
            chat_id=chat_id,
            user_id=user_id,
            chat_history=chat_history or [],
            mcp_context=mcp_context,
            created_at=time.time(),
        )
        
        try:
            self.redis_client.rpush(self.QUERY_QUEUE, json.dumps(job.to_dict()))
            logger.debug(f"Enqueued job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False
    
    def get_result(self, job_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get result for a job (blocking with timeout).
        
        Args:
            job_id: Job ID to get result for
            timeout: Maximum time to wait
            
        Returns:
            Result dict or None if not available
        """
        if not self.redis_client:
            return None
        
        result_key = f"{self.RESULT_QUEUE_PREFIX}{job_id}"
        
        try:
            # Blocking pop with timeout
            result = self.redis_client.blpop(result_key, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None
    
    def _store_result(self, job_id: str, result: Dict[str, Any]):
        """Store result in Redis"""
        if not self.redis_client:
            return
        
        result_key = f"{self.RESULT_QUEUE_PREFIX}{job_id}"
        try:
            self.redis_client.rpush(result_key, json.dumps(result))
            self.redis_client.expire(result_key, self.RESULT_TTL)
        except Exception as e:
            logger.error(f"Failed to store result: {e}")
    
    def _process_job(self, job: QueryJob) -> Dict[str, Any]:
        """Process a single job"""
        start_time = time.time()
        
        try:
            if not self.rag_pipeline:
                raise RuntimeError("RAG pipeline not initialized")
            
            result = self.rag_pipeline.query(
                question=job.query,
                chat_history=job.chat_history,
                mcp_context=job.mcp_context,
                chat_id=job.chat_id,
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.stats['jobs_processed'] += 1
            self.stats['total_processing_time_ms'] += processing_time
            
            return {
                'success': True,
                'job_id': job.job_id,
                'result': result,
                'processing_time_ms': processing_time,
                'worker_id': self.worker_id,
            }
            
        except Exception as e:
            self.stats['jobs_failed'] += 1
            logger.error(f"Job {job.job_id} failed: {e}")
            
            return {
                'success': False,
                'job_id': job.job_id,
                'error': str(e),
                'worker_id': self.worker_id,
            }
    
    async def run(self):
        """
        Main worker loop - poll for jobs and process them.
        Run this in a separate process/container for horizontal scaling.
        """
        if not self.redis_client:
            logger.error("Cannot start worker: Redis not available")
            return
        
        self.running = True
        logger.info(f"RAGWorker {self.worker_id} starting...")
        
        while self.running:
            try:
                # Blocking pop from queue
                job_data = self.redis_client.blpop(self.QUERY_QUEUE, timeout=self.POLL_TIMEOUT)
                
                if job_data:
                    _, job_json = job_data
                    job = QueryJob.from_dict(json.loads(job_json))
                    
                    logger.info(f"Worker {self.worker_id} processing job {job.job_id}")
                    
                    # Process the job
                    result = self._process_job(job)
                    
                    # Store result
                    self._store_result(job.job_id, result)
                    
                    logger.info(f"Job {job.job_id} completed in {result.get('processing_time_ms', 0):.0f}ms")
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
        
        logger.info(f"RAGWorker {self.worker_id} stopped")
    
    def stop(self):
        """Stop the worker"""
        self.running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        avg_time = 0
        if self.stats['jobs_processed'] > 0:
            avg_time = self.stats['total_processing_time_ms'] / self.stats['jobs_processed']
        
        return {
            **self.stats,
            'avg_processing_time_ms': avg_time,
            'worker_id': self.worker_id,
            'running': self.running,
        }


async def start_rag_worker(rag_pipeline, worker_id: str = "worker-1"):
    """
    Start a RAG worker.
    
    Usage:
        # In a separate process/container:
        from src.rag import RAGPipeline
        from src.workers import start_rag_worker
        
        pipeline = RAGPipeline()
        asyncio.run(start_rag_worker(pipeline, "worker-1"))
    """
    worker = RAGWorker(rag_pipeline=rag_pipeline, worker_id=worker_id)
    await worker.run()
