"""
Query Planner - Decides which LLM calls are actually needed
Reduces LLM costs by using fast heuristics for simple queries

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import re
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries the planner can identify"""
    GREETING = "greeting"
    SIMPLE_FACT = "simple_fact"
    CODE_REQUEST = "code_request"
    KNOWN_ERROR = "known_error"
    ERROR_DEBUG = "error_debug"
    COMPLEX_QUESTION = "complex_question"
    GENERIC_TRADING = "generic_trading"
    MUDREX_SPECIFIC = "mudrex_specific"


@dataclass
class QueryPlan:
    """
    Plan for how to handle a query.
    Specifies which expensive operations to skip.
    """
    query_type: QueryType
    
    # Skip flags
    skip_all: bool = False  # Return canned response immediately
    skip_retrieval: bool = False  # Don't search vector store
    skip_validation: bool = False  # Don't validate document relevancy
    skip_rerank: bool = False  # Don't rerank documents
    skip_llm: bool = False  # Don't call LLM for response
    
    # What to use instead
    use_fact_store: bool = False  # Check fact store first
    use_canned_response: bool = False  # Return canned response
    canned_response_key: Optional[str] = None  # Key for canned response
    use_tool_calling: bool = False  # Use Gemini function-calling tools
    tool_hint: Optional[str] = None  # Suggested tool function name
    
    # Metadata
    confidence: float = 1.0  # How confident the planner is
    reason: str = ""  # Why this plan was chosen
    
    def __post_init__(self):
        if self.skip_all:
            self.skip_retrieval = True
            self.skip_validation = True
            self.skip_rerank = True


class QueryPlanner:
    """
    Analyzes queries and creates execution plans.
    Uses fast heuristics to avoid unnecessary LLM calls.
    
    Cost reduction strategy:
    - Greetings: Skip everything (canned response)
    - Simple facts: Use fact store only
    - Code requests: Skip validation and rerank (direct retrieval + generation)
    - Error debugging: Full pipeline (context is important)
    - Complex questions: Full pipeline
    """
    
    # Greeting patterns (no script — short reply only)
    GREETING_PATTERNS = [
        r'^(hi|hello|hey|yo|sup|gm|gn|what\'?s up)[\s!.,?]*$',
        r'^(how are you|how\'?re you|how do you do)[\s!.,?]*$',
        r'^(good morning|good afternoon|good evening)[\s!.,?]*$',
        r'^(thanks|thank you|thx)[\s!.,?]*$',
    ]
    
    # Code request indicators
    CODE_INDICATORS = [
        "how to", "how do i", "example", "sample", "code",
        "snippet", "implement", "write", "create", "build",
        "show me", "give me", "can you write", "python", "javascript",
    ]
    
    # Error/debug indicators
    ERROR_INDICATORS = [
        "error", "exception", "failed", "not working", "broken",
        "issue", "problem", "bug", "wrong", "incorrect",
        "traceback", "stack trace", "status code", "http",
        "-1", "401", "403", "404", "429", "500",
    ]
    
    # Simple fact indicators (single word/phrase lookups)
    SIMPLE_FACT_INDICATORS = [
        "what is the", "what's the", "what are the",
        "rate limit", "base url", "endpoint", "latency",
    ]
    
    # Generic trading indicators (no Mudrex context needed)
    GENERIC_TRADING_MARKERS = [
        "partial fill", "pnl", "p&l", "unrealized", "unrealised",
        "kill switch", "throttle", "cross-margin", "cross margin",
        "isolated margin", "liquidation", "slippage", "spoofing",
        "risk engine", "risk management", "strategy", "strategies",
        "trading strategy", "automate", "automation", "bot strategy",
        "algorithm", "algorithmic", "backtest", "backtesting",
        "design a bot", "design this", "design an emergency",
    ]
    
    # Mudrex-specific markers
    MUDREX_MARKERS = [
        "mudrex", "fapi", "trade.mudrex.com", "x-authentication",
        "fapi/v1", "mudrex api", "mudrex futures",
    ]
    
    # Known-error patterns → tool function hints (checked before generic ERROR_DEBUG)
    KNOWN_ERROR_PATTERNS = {
        r'\b500\b.*\b(sl|tp|stop.?loss|take.?profit)\b': "troubleshoot_500_error",
        r'\b(sl|tp|stop.?loss|take.?profit)\b.*\b500\b': "troubleshoot_500_error",
        r'\b500\b.*(internal|server\s*error|inline)': "troubleshoot_500_error",
        r'\b(pnl|p&l)\b.*(discrepanc|mismatch|differ|wrong|off)': "troubleshoot_pnl_discrepancy",
        r'\b(pnl|p&l)\b.*(not match|doesn.t match|incorrect)': "troubleshoot_pnl_discrepancy",
        r'\b(401|403|-1022)\b': "troubleshoot_auth_error",
        r'\b(auth|authenticat).*(fail|error|invalid|wrong|issue)': "troubleshoot_auth_error",
        r'\b429\b': "troubleshoot_rate_limit",
        r'\brate.?limit': "troubleshoot_rate_limit",
        r'-1111\b': "troubleshoot_order_error",
        r'-1121\b': "troubleshoot_order_error",
        r'\b(precision|step.?size)\b.*(error|issue|wrong|fail)': "troubleshoot_order_error",
        # 202 Accepted — extremely common confusion (user thinks it's an error)
        r'(failed|error|❌).*\b202\b': "troubleshoot_http_202",
        r'\b202\b.*(failed|error|what|why|issue|wrong)': "troubleshoot_http_202",
        r'"success"\s*:\s*true.*\b202\b': "troubleshoot_http_202",
        # 405 Method Not Allowed
        r'\b405\b': "troubleshoot_http_405",
    }
    
    # Canned responses
    CANNED_RESPONSES = {
        "greeting": "Hey! What's up? Ask me about the API, code, or errors.",
        "thanks": "You're welcome! Let me know if you need anything else.",
    }
    
    def __init__(self, fact_store=None):
        """Initialize query planner with optional fact store reference"""
        self.fact_store = fact_store
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        self.greeting_regexes = [
            re.compile(p, re.IGNORECASE) for p in self.GREETING_PATTERNS
        ]
        self.known_error_regexes = [
            (re.compile(p, re.IGNORECASE | re.DOTALL), hint)
            for p, hint in self.KNOWN_ERROR_PATTERNS.items()
        ]
    
    def plan(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryPlan:
        """
        Create an execution plan for the query.
        
        Args:
            query: The user's query
            context: Optional context (chat history, etc.)
            
        Returns:
            QueryPlan with instructions for execution
        """
        if not query or not query.strip():
            return QueryPlan(
                query_type=QueryType.GREETING,
                skip_all=True,
                use_canned_response=True,
                canned_response_key="greeting",
                reason="Empty query"
            )
        
        query_clean = query.strip()
        query_lower = query_clean.lower()
        
        # 1. Check for greetings (fast path)
        if self._is_greeting(query_clean):
            return QueryPlan(
                query_type=QueryType.GREETING,
                skip_all=True,
                use_canned_response=True,
                canned_response_key="greeting",
                reason="Detected greeting"
            )
        
        # 2. Check fact store for direct matches (if available)
        if self.fact_store:
            fact_match = self.fact_store.search(query)
            if fact_match:
                return QueryPlan(
                    query_type=QueryType.SIMPLE_FACT,
                    skip_retrieval=True,
                    skip_validation=True,
                    skip_rerank=True,
                    skip_llm=True,
                    use_fact_store=True,
                    reason="Direct fact store match"
                )
        
        # 3. Determine query type
        # 3a. Check for specific known errors (deterministic tool-calling path)
        known_error_hint = self._is_known_error(query_lower)
        if known_error_hint:
            return QueryPlan(
                query_type=QueryType.KNOWN_ERROR,
                skip_retrieval=True,
                skip_validation=True,
                skip_rerank=True,
                use_tool_calling=True,
                tool_hint=known_error_hint,
                confidence=0.95,
                reason=f"Known error pattern matched -> {known_error_hint}"
            )
        
        # 3b. Generic error/debugging (full RAG pipeline)
        if self._is_error_debug(query_lower):
            return QueryPlan(
                query_type=QueryType.ERROR_DEBUG,
                reason="Error/debugging query - full pipeline"
            )
        
        if self._is_code_request(query_lower):
            return QueryPlan(
                query_type=QueryType.CODE_REQUEST,
                skip_validation=True,  # Skip validation for code requests
                skip_rerank=True,  # Skip rerank - first result usually good enough
                confidence=0.9,
                reason="Code request - skip validation/rerank"
            )
        
        if self._is_generic_trading(query_lower):
            return QueryPlan(
                query_type=QueryType.GENERIC_TRADING,
                skip_retrieval=True,  # Don't need RAG for generic trading
                skip_validation=True,
                skip_rerank=True,
                reason="Generic trading question - no RAG needed"
            )
        
        if self._is_mudrex_specific(query_lower):
            return QueryPlan(
                query_type=QueryType.MUDREX_SPECIFIC,
                # Full pipeline for Mudrex-specific questions
                reason="Mudrex-specific - full RAG pipeline"
            )
        
        # 4. Default: Complex question - use full pipeline
        return QueryPlan(
            query_type=QueryType.COMPLEX_QUESTION,
            confidence=0.7,
            reason="Complex question - full pipeline"
        )
    
    def _is_known_error(self, query_lower: str) -> Optional[str]:
        """Check if query matches a specific known-error pattern.
        
        Returns the tool function hint (e.g. "troubleshoot_500_error") or None.
        """
        for regex, hint in self.known_error_regexes:
            if regex.search(query_lower):
                return hint
        return None
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a simple greeting"""
        for regex in self.greeting_regexes:
            if regex.match(query):
                return True
        return False
    
    def _is_code_request(self, query_lower: str) -> bool:
        """Check if query is asking for code"""
        return any(ind in query_lower for ind in self.CODE_INDICATORS)
    
    def _is_error_debug(self, query_lower: str) -> bool:
        """Check if query is about errors/debugging"""
        return any(ind in query_lower for ind in self.ERROR_INDICATORS)
    
    def _is_generic_trading(self, query_lower: str) -> bool:
        """Check if query is about generic trading concepts"""
        # If it mentions Mudrex, it's not generic
        if self._is_mudrex_specific(query_lower):
            return False
        return any(marker in query_lower for marker in self.GENERIC_TRADING_MARKERS)
    
    def _is_mudrex_specific(self, query_lower: str) -> bool:
        """Check if query is Mudrex-specific"""
        return any(marker in query_lower for marker in self.MUDREX_MARKERS)
    
    def get_canned_response(self, key: str) -> str:
        """Get a canned response by key"""
        return self.CANNED_RESPONSES.get(key, self.CANNED_RESPONSES["greeting"])
    
    def estimate_cost_savings(self, plan: QueryPlan) -> Dict[str, Any]:
        """
        Estimate cost savings from the plan.
        
        Returns estimated LLM calls avoided.
        """
        # Full pipeline would be: validation + rerank + generation = 3-5 calls
        full_pipeline_calls = 5
        avoided_calls = 0
        
        if plan.skip_all:
            avoided_calls = full_pipeline_calls
        else:
            if plan.skip_validation:
                avoided_calls += 1
            if plan.skip_rerank:
                avoided_calls += 1
            if plan.skip_llm:
                avoided_calls += 1
        
        return {
            "full_pipeline_calls": full_pipeline_calls,
            "avoided_calls": avoided_calls,
            "remaining_calls": full_pipeline_calls - avoided_calls,
            "savings_percent": (avoided_calls / full_pipeline_calls) * 100
        }
