"""
Utility libraries for the Mudrex API Bot
"""
from .error_reporter import report_error, report_error_sync
from .logging import (
    configure_logging,
    get_logger,
    log_query,
    log_query_complete,
    log_error,
    log_cache_event,
    log_llm_call,
    log_retrieval,
    LogContext,
)
from .metrics import (
    generate_metrics,
    record_cache_hit,
    record_cache_miss,
    record_cache_set,
    record_error,
    record_embedding,
    update_documents_count,
    update_cache_hit_rate,
    QueryTimer,
    LLMTimer,
)
from .security import (
    InputSanitizer,
    APIKeyDetector,
    sanitize_input,
    detect_api_key,
    mask_sensitive_data,
)
from .audit import (
    AuditLogger,
    AuditEventType,
    get_audit_logger,
    log_query as audit_log_query,
    log_error as audit_log_error,
    log_security_event,
    log_api_key_exposure,
)

__all__ = [
    # Error reporting
    "report_error",
    "report_error_sync",
    # Logging
    "configure_logging",
    "get_logger",
    "log_query",
    "log_query_complete",
    "log_error",
    "log_cache_event",
    "log_llm_call",
    "log_retrieval",
    "LogContext",
    # Metrics
    "generate_metrics",
    "record_cache_hit",
    "record_cache_miss",
    "record_cache_set",
    "record_error",
    "record_embedding",
    "update_documents_count",
    "update_cache_hit_rate",
    "QueryTimer",
    "LLMTimer",
    # Security
    "InputSanitizer",
    "APIKeyDetector",
    "sanitize_input",
    "detect_api_key",
    "mask_sensitive_data",
    # Audit
    "AuditLogger",
    "AuditEventType",
    "get_audit_logger",
    "audit_log_query",
    "audit_log_error",
    "log_security_event",
    "log_api_key_exposure",
]
