"""
Audit Logging - Track queries and events for security and compliance
Stores anonymized records of bot activity

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from ..config import config

logger = logging.getLogger(__name__)

# Import Redis cache
try:
    from ..rag.cache import RedisCache
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class AuditEventType(Enum):
    """Types of audit events"""
    QUERY = "query"
    COMMAND = "command"
    ERROR = "error"
    SECURITY = "security"
    RATE_LIMIT = "rate_limit"
    API_KEY_EXPOSED = "api_key_exposed"
    ADMIN_ACTION = "admin_action"


@dataclass
class AuditEvent:
    """An audit log entry"""
    event_type: AuditEventType
    timestamp: str
    chat_id_hash: str  # Hashed for privacy
    user_id_hash: str  # Hashed for privacy
    query_hash: str  # Hash of query content (not the content itself)
    response_time_ms: float
    success: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['event_type'] = self.event_type.value
        return d


class AuditLogger:
    """
    Audit logger for tracking bot activity.
    
    Privacy features:
    - Hashes user/chat IDs (not stored in plain text)
    - Hashes query content (not stored)
    - Only stores metadata for analysis
    
    What is logged:
    - Query hashes (not content)
    - User/chat ID hashes
    - Response times
    - Error counts
    - Security events
    """
    
    # Maximum events to store in memory
    MAX_MEMORY_EVENTS = 10000
    
    # Redis key prefix
    REDIS_KEY_PREFIX = "audit:"
    
    # Event TTL (30 days)
    EVENT_TTL = 30 * 24 * 60 * 60
    
    def __init__(self):
        """Initialize audit logger"""
        self.events: List[AuditEvent] = []
        self.redis_client = None
        
        # Try to get Redis connection
        if HAS_REDIS and config.REDIS_ENABLED:
            try:
                cache = RedisCache()
                if cache.connected:
                    self.redis_client = cache.redis_client
                    logger.info("AuditLogger using Redis storage")
            except Exception as e:
                logger.debug(f"AuditLogger using memory storage: {e}")
        
        # Aggregated stats
        self.stats = {
            'total_queries': 0,
            'total_errors': 0,
            'security_events': 0,
            'api_key_exposures': 0,
        }
        
        logger.info("AuditLogger initialized")
    
    def _hash(self, value: Any) -> str:
        """Hash a value for privacy"""
        if value is None:
            return "none"
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp"""
        return datetime.utcnow().isoformat() + "Z"
    
    def log_query(
        self,
        chat_id: int,
        user_id: int,
        query: str,
        response_time_ms: float,
        success: bool = True,
        cache_hit: bool = False,
        doc_count: int = 0,
        domain: str = "unknown",
    ):
        """
        Log a query event.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            query: User's query (will be hashed)
            response_time_ms: Response time in milliseconds
            success: Whether query succeeded
            cache_hit: Whether response was from cache
            doc_count: Number of documents retrieved
            domain: Query domain (mudrex_specific, generic_trading, etc.)
        """
        event = AuditEvent(
            event_type=AuditEventType.QUERY,
            timestamp=self._get_timestamp(),
            chat_id_hash=self._hash(chat_id),
            user_id_hash=self._hash(user_id),
            query_hash=self._hash(query),
            response_time_ms=response_time_ms,
            success=success,
            metadata={
                'cache_hit': cache_hit,
                'doc_count': doc_count,
                'domain': domain,
                'query_length': len(query) if query else 0,
            }
        )
        
        self._store_event(event)
        self.stats['total_queries'] += 1
    
    def log_error(
        self,
        chat_id: int,
        user_id: int,
        error_type: str,
        error_message: str,
        component: str = "unknown",
    ):
        """
        Log an error event.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            error_type: Type of error (e.g., "ValueError")
            error_message: Error message (will be truncated)
            component: Component where error occurred
        """
        event = AuditEvent(
            event_type=AuditEventType.ERROR,
            timestamp=self._get_timestamp(),
            chat_id_hash=self._hash(chat_id),
            user_id_hash=self._hash(user_id),
            query_hash="",
            response_time_ms=0,
            success=False,
            metadata={
                'error_type': error_type,
                'error_preview': error_message[:100] if error_message else "",
                'component': component,
            }
        )
        
        self._store_event(event)
        self.stats['total_errors'] += 1
    
    def log_security_event(
        self,
        chat_id: int,
        user_id: int,
        event_subtype: str,
        details: Dict[str, Any] = None,
    ):
        """
        Log a security event.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            event_subtype: Type of security event (e.g., "injection_attempt")
            details: Additional details
        """
        event = AuditEvent(
            event_type=AuditEventType.SECURITY,
            timestamp=self._get_timestamp(),
            chat_id_hash=self._hash(chat_id),
            user_id_hash=self._hash(user_id),
            query_hash="",
            response_time_ms=0,
            success=True,
            metadata={
                'subtype': event_subtype,
                **(details or {}),
            }
        )
        
        self._store_event(event)
        self.stats['security_events'] += 1
    
    def log_api_key_exposure(
        self,
        chat_id: int,
        user_id: int,
        key_preview: str = None,
    ):
        """
        Log an API key exposure event.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            key_preview: Masked preview of the key (e.g., "abc...xyz")
        """
        event = AuditEvent(
            event_type=AuditEventType.API_KEY_EXPOSED,
            timestamp=self._get_timestamp(),
            chat_id_hash=self._hash(chat_id),
            user_id_hash=self._hash(user_id),
            query_hash="",
            response_time_ms=0,
            success=True,
            metadata={
                'key_preview': key_preview or "***",
            }
        )
        
        self._store_event(event)
        self.stats['api_key_exposures'] += 1
        
        # Also log warning
        logger.warning(f"API key exposed in chat {self._hash(chat_id)} by user {self._hash(user_id)}")
    
    def log_rate_limit(
        self,
        chat_id: int,
        user_id: int,
        limit_type: str,
    ):
        """
        Log a rate limit event.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            limit_type: Type of limit hit (user, group, global)
        """
        event = AuditEvent(
            event_type=AuditEventType.RATE_LIMIT,
            timestamp=self._get_timestamp(),
            chat_id_hash=self._hash(chat_id),
            user_id_hash=self._hash(user_id),
            query_hash="",
            response_time_ms=0,
            success=False,
            metadata={
                'limit_type': limit_type,
            }
        )
        
        self._store_event(event)
    
    def _store_event(self, event: AuditEvent):
        """Store event in Redis or memory"""
        # Store in Redis
        if self.redis_client:
            try:
                key = f"{self.REDIS_KEY_PREFIX}{event.timestamp}:{event.event_type.value}"
                self.redis_client.setex(key, self.EVENT_TTL, json.dumps(event.to_dict()))
            except Exception as e:
                logger.debug(f"Failed to store audit event in Redis: {e}")
        
        # Also store in memory (for quick access)
        self.events.append(event)
        
        # Trim memory if too large
        if len(self.events) > self.MAX_MEMORY_EVENTS:
            self.events = self.events[-self.MAX_MEMORY_EVENTS:]
    
    def get_recent_events(
        self,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get recent audit events.
        
        Args:
            event_type: Filter by event type
            limit: Maximum events to return
            
        Returns:
            List of event dictionaries
        """
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Return most recent
        return [e.to_dict() for e in events[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        return {
            **self.stats,
            'events_in_memory': len(self.events),
            'using_redis': self.redis_client is not None,
        }
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity for a specific user"""
        user_hash = self._hash(user_id)
        events = [e for e in self.events if e.user_id_hash == user_hash]
        return [e.to_dict() for e in events[-limit:]]


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_query(chat_id: int, user_id: int, query: str, response_time_ms: float, **kwargs):
    """Convenience function to log a query"""
    get_audit_logger().log_query(chat_id, user_id, query, response_time_ms, **kwargs)


def log_error(chat_id: int, user_id: int, error_type: str, error_message: str, **kwargs):
    """Convenience function to log an error"""
    get_audit_logger().log_error(chat_id, user_id, error_type, error_message, **kwargs)


def log_security_event(chat_id: int, user_id: int, event_subtype: str, **kwargs):
    """Convenience function to log a security event"""
    get_audit_logger().log_security_event(chat_id, user_id, event_subtype, **kwargs)


def log_api_key_exposure(chat_id: int, user_id: int, key_preview: str = None):
    """Convenience function to log an API key exposure"""
    get_audit_logger().log_api_key_exposure(chat_id, user_id, key_preview)
