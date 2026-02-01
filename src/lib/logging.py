"""
Structured Logging Configuration using structlog
Provides JSON-formatted logs with context propagation

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import logging
import sys
import os
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor


def add_environment_info(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add environment information to log entries"""
    event_dict["environment"] = os.getenv("RAILWAY_ENVIRONMENT", "development")
    event_dict["service"] = os.getenv("RAILWAY_SERVICE_NAME", "mudrex-api-copilot")
    return event_dict


def add_version_info(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add version information to log entries"""
    event_dict["version"] = "2.0.0"
    return event_dict


def censor_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Censor sensitive data from logs"""
    sensitive_keys = [
        "api_key", "api_secret", "token", "password", "secret",
        "x-authentication", "authorization", "credential"
    ]
    
    def censor_value(key: str, value: Any) -> Any:
        if isinstance(value, str) and any(s in key.lower() for s in sensitive_keys):
            if len(value) > 8:
                return f"{value[:4]}...{value[-4:]}"
            return "***REDACTED***"
        elif isinstance(value, dict):
            return {k: censor_value(k, v) for k, v in value.items()}
        return value
    
    for key in list(event_dict.keys()):
        event_dict[key] = censor_value(key, event_dict[key])
    
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    include_timestamp: bool = True,
):
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: If True, output JSON; if False, output colored console format
        include_timestamp: Include timestamps in logs
    """
    # Determine format based on environment
    is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production"
    use_json = json_format or is_production
    
    # Build processor chain
    # Note: filter_by_level removed - make_filtering_bound_logger handles filtering
    processors: list[Processor] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_environment_info,
        censor_sensitive_data,
    ]
    
    if include_timestamp:
        processors.insert(0, structlog.processors.TimeStamper(fmt="iso"))
    
    # Add renderer based on format
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Also configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    
    return structlog.get_logger()


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Optional logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(logger_name=name)
    return logger


class LogContext:
    """Context manager for adding temporary context to logs"""
    
    def __init__(self, **context):
        self.context = context
        self.logger = None
    
    def __enter__(self):
        self.logger = structlog.get_logger()
        return self.logger.bind(**self.context)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Convenience functions for common log patterns

def log_query(
    query: str,
    query_id: str,
    chat_id: str,
    **kwargs
):
    """Log a query event"""
    logger = get_logger("query")
    logger.info(
        "query_received",
        query_id=query_id,
        chat_id=chat_id,
        query_length=len(query),
        query_preview=query[:100] if len(query) > 100 else query,
        **kwargs
    )


def log_query_complete(
    query_id: str,
    latency_ms: float,
    doc_count: int,
    cache_hit: bool,
    domain: str,
    **kwargs
):
    """Log query completion"""
    logger = get_logger("query")
    logger.info(
        "query_complete",
        query_id=query_id,
        latency_ms=round(latency_ms, 2),
        doc_count=doc_count,
        cache_hit=cache_hit,
        domain=domain,
        **kwargs
    )


def log_error(
    error: Exception,
    component: str,
    context: Optional[Dict[str, Any]] = None,
):
    """Log an error with context"""
    logger = get_logger(component)
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        component=component,
        **(context or {}),
        exc_info=True,
    )


def log_cache_event(
    operation: str,  # get, set, hit, miss
    key_type: str,   # response, embedding, validation, etc.
    cache_hit: bool = None,
    **kwargs
):
    """Log a cache event"""
    logger = get_logger("cache")
    logger.debug(
        f"cache_{operation}",
        key_type=key_type,
        cache_hit=cache_hit,
        **kwargs
    )


def log_llm_call(
    operation: str,  # generate, validate, rerank, transform
    model: str,
    latency_ms: float,
    tokens_used: Optional[int] = None,
    **kwargs
):
    """Log an LLM API call"""
    logger = get_logger("llm")
    logger.info(
        "llm_call",
        operation=operation,
        model=model,
        latency_ms=round(latency_ms, 2),
        tokens_used=tokens_used,
        **kwargs
    )


def log_retrieval(
    query_id: str,
    docs_found: int,
    latency_ms: float,
    threshold: float,
    **kwargs
):
    """Log a document retrieval event"""
    logger = get_logger("retrieval")
    logger.debug(
        "retrieval_complete",
        query_id=query_id,
        docs_found=docs_found,
        latency_ms=round(latency_ms, 2),
        threshold=threshold,
        **kwargs
    )
