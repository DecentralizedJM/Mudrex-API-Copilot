"""
RAG Pipeline - Orchestrates the retrieval and generation process

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License - See LICENSE file for details.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

import requests

from google.genai import types

from .vector_store import VectorStore
from .gemini_client import GeminiClient
from .document_loader import DocumentLoader
from .fact_store import FactStore
from .cache import RedisCache
from .query_planner import QueryPlanner, QueryPlan, QueryType
from .semantic_cache import SemanticCache
from ..config import config

logger = logging.getLogger(__name__)

# Import context manager and semantic memory (optional)
try:
    from .context_manager import ContextManager
except ImportError:
    ContextManager = None

try:
    from .semantic_memory import SemanticMemory
except ImportError:
    SemanticMemory = None


class RAGPipeline:
    """Coordinates the RAG workflow with query planning for cost optimization"""
    
    def __init__(self):
        """Initialize RAG components"""
        self.vector_store = VectorStore()
        self.gemini_client = GeminiClient()
        self.document_loader = DocumentLoader()
        self.fact_store = FactStore()
        self.cache = RedisCache() if config.REDIS_ENABLED else None
        
        # Initialize query planner (for cost optimization)
        self.query_planner = QueryPlanner(fact_store=self.fact_store)
        
        # Initialize semantic cache (for similar query deduplication)
        self.semantic_cache = SemanticCache() if config.REDIS_ENABLED else None
        
        # Initialize context management (optional)
        self.context_manager = ContextManager() if ContextManager else None
        self.semantic_memory = SemanticMemory() if SemanticMemory else None
        
        logger.info("RAG Pipeline initialized with query planner and semantic cache")
    
    def _get_off_topic_reply(self, question: str) -> Optional[str]:
        """Detect off-topic / general-knowledge questions; return short reply or None (no RAG/Gemini)."""
        q = question.strip().lower()
        # Remove common bot mention
        q = re.sub(r'@\w+\s*', '', q).strip()
        if len(q) < 10:
            return None
        # "Who is X", "Who was X", "What is X" when X is not API-related
        api_keywords = ('api', 'mudrex api', 'endpoint', 'error', 'order', 'auth', 'token', 'header', 'code -', '-1021', '-1111', '404', '400')
        if any(k in q for k in api_keywords):
            return None
        if re.match(r'^(who is|who was|who are|what is|what was)\s+.+', q):
            return "I'm the Mudrex API copilot — ask me about the API, code, or errors."
        return None

    def _get_bot_architecture_reply(self, question: str) -> Optional[str]:
        """Don't expose how the copilot works. Redirect to @DecentralizedJM."""
        q = question.lower()
        # Don't treat pasted log/error output as bot-architecture (e.g. SECRET LOGGING, stack traces)
        log_error_indicators = (
            "[⚠️]", "secret logging", "potential key leak", "key leak to console",
            "in client.py", "in init.py", "in tools.py", "in server.py",
            "x-authentication", "api_secret", "traceback", "exception:",
        )
        if any(ind in q for ind in log_error_indicators):
            return None
        # Don't treat error-debug questions as bot-architecture (user asking about a log/error they pasted)
        error_debug_phrases = (
            "what is this error", "what's this error", "what does this error",
            "what is this mean", "what does this mean", "what's this mean",
            "explain this error", "why am i seeing", "why am i getting",
            "why am i getting this", "what does this log", "explain this log",
        )
        if any(p in q for p in error_debug_phrases):
            return None
        keywords = (
            "build a bot like you", "build you", "how do you work", "how you work",
            "rag", "vector store", "api copilot architecture", "copilot testing bot",
            "deploy a bot like", "build one like you", "share your code", "share me your code",
            "how can i build you", "how to build you", "details of api copilot",
            "guide me to build", "steps from starting to deployment", "built one",
        )
        if not any(k in q for k in keywords):
            return None
        return (
            "I'm the Mudrex API copilot — built by @DecentralizedJM. "
            "For questions about how I work or building something similar, reach out to him!"
        )

    def _get_mudrex_loyalist_reply(self, question: str) -> Optional[str]:
        """Copilot is Mudrex loyalist: praise Mudrex; for 'why' say I'm here to help."""
        q = question.lower()
        if not any(k in q for k in ("which platform", "is mudrex reliable", "mudrex vs", "other platforms", "api trading which", "good platform for api")):
            return None
        if "why" in q or "better" in q:
            return "Mudrex is built for programmatic trading with a simple REST API. I'm here to help you with the API — ask me anything about endpoints, code, or errors."
        return (
            "Mudrex is a great choice for API trading — simple REST, no complex signing, and I'm here to help. "
            "For setup and code, check https://docs.trade.mudrex.com or ask me about specific endpoints."
        )
    
    def _ping_mudrex_api(self, timeout: int = 5) -> Tuple[bool, Optional[int], str]:
        """Ping Mudrex API; return (is_up, status_code, detail)."""
        base = "https://trade.mudrex.com/fapi/v1"
        headers = {}
        if config.MUDREX_API_SECRET:
            headers["X-Authentication"] = config.MUDREX_API_SECRET
        try:
            # GET a lightweight endpoint; 200 or 401 = API reachable
            r = requests.get(f"{base}/futures", params={"limit": 1}, headers=headers or None, timeout=timeout)
            if r.status_code in (200, 401):
                return True, r.status_code, "reachable"
            return False, r.status_code, f"HTTP {r.status_code}"
        except requests.exceptions.ConnectionError as e:
            return False, None, "connection failed"
        except requests.exceptions.Timeout:
            return False, None, "timeout"
        except Exception as e:
            return False, None, str(e)
    
    def is_connectivity_question(self, question: str) -> bool:
        """True if the user is asking whether the API is down / connectivity check."""
        q = question.lower()
        return any(
            k in q for k in (
                "api down", "api is down", "unable to connect", "connectivity",
                "connection", "is mudrex api", "api not working", "can't connect",
                "cannot connect", "mcp", "check connection", "check live", "is api up"
            )
        )

    def run_connectivity_check(self) -> str:
        """
        Ping Mudrex API and return the second message (status + script + footer).
        Call this after sending "Let me check." and showing typing.
        """
        logger.info("Connectivity check: pinging Mudrex API")
        up, status_code, detail = self._ping_mudrex_api()
        if up:
            status_line = "I just checked — the Mudrex API is **up** and reachable."
            script = (
                "Quick test from your side (replace with your API secret):\n\n"
                "```python\n"
                "import requests\n\n"
                "BASE_URL = \"https://trade.mudrex.com/fapi/v1\"\n"
                "headers = {\"X-Authentication\": \"YOUR_API_SECRET\"}\n\n"
                "# Test connectivity — list futures (limit 1)\n"
                "r = requests.get(f\"{BASE_URL}/futures\", params={\"limit\": 1}, headers=headers, timeout=10)\n"
                "print(r.status_code, \"OK\" if r.status_code == 200 else r.json())\n"
                "```"
            )
        else:
            status_line = f"I just checked — the API returned: **{detail}**. It may be temporarily unreachable or your network may be blocking the request."
            script = (
                "When it's back, test with:\n\n"
                "```python\n"
                "import requests\n\n"
                "r = requests.get(\"https://trade.mudrex.com/fapi/v1/futures\", params={\"limit\": 1}, headers={\"X-Authentication\": \"YOUR_SECRET\"}, timeout=10)\n"
                "print(r.status_code, r.json())\n"
                "```"
            )
        footer = "Try the snippet above. If you get an error, share the error code and I can help."
        return f"{status_line}\n\n{script}\n\n_{footer}_"

    def _get_connectivity_check_reply(self, question: str) -> Optional[Dict[str, Any]]:
        """If question is about API down/connectivity, return reply dict (used only when not using two-step flow)."""
        if not self.is_connectivity_question(question):
            return None
        answer = self.run_connectivity_check()
        return {
            "answer": answer,
            "sources": [{"filename": "Mudrex API status (live check)", "similarity": 1.0}],
            "is_relevant": True,
        }
    
    def ingest_documents(self, docs_directory: str) -> int:
        """
        Ingest documents from a directory into the vector store
        
        Args:
            docs_directory: Path to documentation directory
            
        Returns:
            Number of chunks added
        """
        logger.info(f"Starting document ingestion from: {docs_directory}")
        
        # Load documents
        documents = self.document_loader.load_from_directory(docs_directory)
        
        if not documents:
            logger.warning("No documents found to ingest")
            return 0
        
        # Process and chunk documents
        texts, metadatas, ids = self.document_loader.process_documents(documents)
        
        # Add to vector store
        self.vector_store.add_documents(texts, metadatas, ids)
        
        logger.info(f"Successfully ingested {len(texts)} chunks from {len(documents)} documents")
        return len(texts)
    
    def query(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = None,
        mcp_context: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a query through the RAG pipeline with query planning optimization.
        When mcp_context is provided (live MCP data), it is passed to the model as co-pilot context.
        
        Args:
            question: User question
            chat_history: Optional conversation history
            top_k: Number of documents to retrieve
            mcp_context: Optional live data from MCP (list_futures, get_future, etc.)
            
        Returns:
            Dict with 'answer', 'sources', and 'is_relevant'
        """
        # 0. Query Planning - Decide execution strategy for cost optimization
        plan = self.query_planner.plan(question, context={"chat_history": chat_history})
        logger.debug(f"Query plan: {plan.query_type.value}, reason: {plan.reason}")
        
        # Handle canned responses (greetings, etc.) - skip everything
        if plan.skip_all and plan.use_canned_response:
            response = self.query_planner.get_canned_response(plan.canned_response_key or "greeting")
            logger.info(f"Using canned response for {plan.query_type.value}")
            return {
                'answer': response,
                'sources': [{'filename': 'QueryPlanner (canned)', 'similarity': 1.0}],
                'is_relevant': True,
                'plan': plan.query_type.value
            }
        
        # 1. Check Fact Store (Strict Rules) - PRIORITY OVER EVERYTHING
        fact_match = self.fact_store.search(question)
        if fact_match:
            logger.info(f"Fact Match found for query: {question}")
            return {
                'answer': fact_match,
                'sources': [{'filename': 'FactStore (Strict User Rule)', 'similarity': 1.0}],
                'is_relevant': True
            }

        # NOTE: is_api_related check is now done in telegram_bot.py (handle_message)
        # Pipeline should always process what gets to it after that gatekeeper check
        
        # 1.5. Off-topic / general knowledge — short reply, no RAG/Gemini (fast, low API usage)
        off_topic_reply = self._get_off_topic_reply(question)
        if off_topic_reply:
            logger.info("Off-topic question: using short reply (no RAG)")
            return {
                "answer": off_topic_reply,
                "sources": [{"filename": "Mudrex API Copilot", "similarity": 1.0}],
                "is_relevant": True,
            }
        
        # 1.5b. Bot architecture / how copilot works — confidential, redirect to @DecentralizedJM
        bot_arch_reply = self._get_bot_architecture_reply(question)
        if bot_arch_reply:
            logger.info("Bot-architecture question: redirect to creator (no RAG)")
            return {
                "answer": bot_arch_reply,
                "sources": [{"filename": "Mudrex API Copilot", "similarity": 1.0}],
                "is_relevant": True,
            }
        
        # 1.5c. Mudrex loyalist — which platform / is Mudrex reliable → praise Mudrex, I'm here to help
        mudrex_loyalist_reply = self._get_mudrex_loyalist_reply(question)
        if mudrex_loyalist_reply:
            logger.info("Platform-choice question: Mudrex loyalist reply (no RAG)")
            return {
                "answer": mudrex_loyalist_reply,
                "sources": [{"filename": "Mudrex API Copilot", "similarity": 1.0}],
                "is_relevant": True,
            }
        
        # 1.6. API down / connectivity — ping Mudrex API and return live status + script
        connectivity_reply = self._get_connectivity_check_reply(question)
        if connectivity_reply:
            return connectivity_reply
        
        # 2. Check response cache first (exact match)
        if self.cache:
            try:
                cached = self.cache.get_response(question, chat_history, mcp_context)
                if cached:
                    logger.info("Cache hit: returning cached response")
                    return cached
            except Exception as e:
                logger.warning(f"Cache get error (continuing without cache): {e}")
        
        # 2.1. Check semantic cache (similar query match)
        if self.semantic_cache:
            try:
                semantic_cached = self.semantic_cache.get(question)
                if semantic_cached:
                    logger.info("Semantic cache hit: returning cached response for similar query")
                    return semantic_cached
            except Exception as e:
                logger.warning(f"Semantic cache error (continuing): {e}")

        # 2.4. Trade ideas / signals — fixed template (no REST endpoint on Mudrex trade API)
        trade_ideas_response = self.gemini_client._get_missing_feature_response(question)
        if trade_ideas_response and any(kw in question.lower() for kw in ("trade ideas", "signals", "signal")):
            logger.info("Using template response for trade ideas/signals")
            return {
                "answer": trade_ideas_response,
                "sources": [{"filename": "Community resources (trade ideas/signals)", "similarity": 1.0}],
                "is_relevant": True,
            }

        # 2.4b. "What to do with my API key" / "guide me" — Mudrex auth only (no HMAC)
        api_key_usage = self.gemini_client._get_api_key_usage_response(question)
        if api_key_usage:
            logger.info("Using template response for API key usage")
            return {
                "answer": api_key_usage,
                "sources": [{"filename": "Authentication (API key usage)", "similarity": 1.0}],
                "is_relevant": True,
            }

        # 2.5. Get enhanced context (if context manager available)
        enhanced_context = None
        semantic_memories = []
        if self.context_manager and chat_id:
            try:
                enhanced_context = self.context_manager.get_context(
                    chat_id=str(chat_id),
                    query=question,
                    include_recent=5,
                    include_memories=True
                )
                semantic_memories = enhanced_context.get('memories', [])
                
                # Use enhanced history if available
                if enhanced_context.get('history'):
                    chat_history = enhanced_context['history']
                    if enhanced_context.get('summary'):
                        # Prepend summary to history
                        chat_history = [
                            {'role': 'system', 'content': enhanced_context['summary']}
                        ] + chat_history
            except Exception as ctx_error:
                logger.warning(f"Error getting enhanced context (using fallback): {ctx_error}")
                # Continue with regular chat_history
        
        # 3. Domain classification: Mudrex-specific vs generic trading/system-design
        domain = self.gemini_client.classify_query_domain(question)
        if domain == "generic_trading":
            logger.info("Domain classified as generic_trading; using generic trading persona without Mudrex docs")
            
            # Include semantic memories in context if available
            if semantic_memories:
                memory_context = "\n\nRelevant context from previous conversations:\n"
                memory_context += "\n".join([
                    f"- {mem.get('content', '')}" for mem in semantic_memories[:3]
                ])
                # Prepend to question
                question = memory_context + "\n\nUser question: " + question
            
            answer = self.gemini_client.generate_generic_trading_answer(
                question,
                chat_history,
            )
            
            result = {
                'answer': answer,
                'sources': [{'filename': 'Generic trading knowledge (non-Mudrex-specific)', 'similarity': 1.0}],
                'is_relevant': True,
            }

            # Cache generic responses as well (saves tokens for repeated design questions)
            if self.cache:
                try:
                    self.cache.set_response(question, chat_history, mcp_context, result)
                except Exception as e:
                    logger.warning(f"Cache set error for generic response (non-critical): {e}")
            return result
        
        # 4. Initial retrieval (Mudrex-specific path with RAG)
        logger.info(f"Processing query: {question[:50]}...")
        retrieved_docs = self.vector_store.search(question, top_k=top_k)
        
        # 4.5. If query looks like an error log, boost retrieval with error-code docs
        if self._looks_like_error_log(question):
            logger.info("Query looks like error log; boosting with error-code docs")
            error_docs = self.vector_store.search(
                "Mudrex API error codes precision step size order errors",
                top_k=5
            )
            if error_docs:
                seen = {doc.get("document", "")[:200] for doc in retrieved_docs}
                for doc in reversed(error_docs):
                    key = doc.get("document", "")[:200]
                    if key not in seen:
                        seen.add(key)
                        retrieved_docs.insert(0, doc)
                logger.info(f"Added {len(error_docs)} error-related doc(s) to context")
        
        # DEBUG: Log retrieval scores
        if retrieved_docs:
            logger.info("Top retrieved docs:")
            for doc in retrieved_docs:
                logger.info(f"- {doc['metadata'].get('filename')}: {doc['similarity']:.4f}")
        else:
            logger.info("No docs retrieved above threshold")
        
        # 5. If empty, try iterative retrieval with query transformation (handles indirect/difficult questions)
        if not retrieved_docs:
            logger.info("No docs found; trying iterative retrieval with enhanced query transformation")
            retrieved_docs = self._iterative_retrieval(question, top_k=top_k)
        
        # 6. If still empty, use low-threshold search for context
        if not retrieved_docs:
            logger.info("Trying low-threshold search for context")
            retrieved_docs = self.vector_store.search_all_relevant(question, top_k=10)
        
        # 6.5. If still empty, try query decomposition for complex questions
        if not retrieved_docs and len(question.split()) > 8:  # Complex/long questions
            logger.info("Trying query decomposition for complex question")
            decomposed = self._decompose_query(question)
            if decomposed and decomposed != question:
                logger.info(f"Decomposed query: '{question}' -> '{decomposed}'")
                retrieved_docs = self.vector_store.search(decomposed, top_k=top_k)
                if not retrieved_docs:
                    retrieved_docs = self.vector_store.search_all_relevant(decomposed, top_k=10)
        
        # 7. Validate document relevancy (Reliable RAG) - skip if plan says so
        if retrieved_docs and not plan.skip_validation:
            logger.info(f"Validating relevancy of {len(retrieved_docs)} documents")
            retrieved_docs = self.gemini_client.validate_document_relevancy(question, retrieved_docs)
        elif plan.skip_validation:
            logger.debug("Skipping validation per query plan")
        
        # 8. Rerank documents for better quality - skip if plan says so
        if retrieved_docs and not plan.skip_rerank:
            logger.info(f"Reranking {len(retrieved_docs)} documents")
            retrieved_docs = self.gemini_client.rerank_documents(question, retrieved_docs)
        elif plan.skip_rerank:
            logger.debug("Skipping rerank per query plan")
        
        # 9. Generate response
        if retrieved_docs:
            # Include semantic memories in mcp_context if available
            enhanced_mcp_context = mcp_context or ""
            if semantic_memories:
                memory_context = "\n\nRelevant context from previous conversations:\n"
                memory_context += "\n".join([
                    f"- {mem.get('content', '')}" for mem in semantic_memories[:3]
                ])
                enhanced_mcp_context = memory_context + "\n\n" + (mcp_context or "")
            
            # Generate response with validated and reranked docs
            answer = self.gemini_client.generate_response(
                question,
                retrieved_docs,
                chat_history,
                enhanced_mcp_context if enhanced_mcp_context else None,
            )
            
            # Extract sources
            sources = [
                {
                    'filename': doc['metadata'].get('filename', 'Unknown'),
                    'similarity': doc.get('similarity', 0.0)
                }
                for doc in retrieved_docs[:3]  # Top 3 sources
            ]
        else:
            # No docs found - use context search (no Google Search)
            logger.info("No relevant docs found; using context search without Google Search")
            
            # Include semantic memories if available
            enhanced_mcp_context = mcp_context or ""
            if semantic_memories:
                memory_context = "\n\nRelevant context from previous conversations:\n"
                memory_context += "\n".join([
                    f"- {mem.get('content', '')}" for mem in semantic_memories[:3]
                ])
                enhanced_mcp_context = memory_context + "\n\n" + (mcp_context or "")
            
            answer = self.gemini_client.generate_response_with_context_search(
                question, [], chat_history, enhanced_mcp_context if enhanced_mcp_context else None
            )
            sources = [{'filename': 'Context Search (no docs)', 'similarity': 0.0}]
        
        result = {
            'answer': answer,
            'sources': sources,
            'is_relevant': True
        }
        
        # Cache the response (exact match cache)
        if self.cache:
            try:
                self.cache.set_response(question, chat_history, mcp_context, result)
            except Exception as e:
                logger.warning(f"Cache set error (non-critical): {e}")
        
        # Cache in semantic cache (for similar queries)
        if self.semantic_cache:
            try:
                self.semantic_cache.set(question, result)
            except Exception as e:
                logger.warning(f"Semantic cache set error (non-critical): {e}")
        
        return result
    
    def _iterative_retrieval(
        self,
        question: str,
        max_iterations: int = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Iterative retrieval: if first search fails, transform query and try again.
        
        Args:
            question: Original query
            max_iterations: Maximum iterations (defaults to MAX_ITERATIVE_RETRIEVAL)
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents, or empty list if none found
        """
        if max_iterations is None:
            max_iterations = config.MAX_ITERATIVE_RETRIEVAL
        
        current_query = question
        
        for iteration in range(max_iterations):
            if iteration > 0:
                # Transform query for better retrieval
                logger.info(f"Iteration {iteration + 1}: Transforming query")
                current_query = self.gemini_client.transform_query(current_query)
            
            # Try search with current query
            docs = self.vector_store.search(current_query, top_k=top_k)
            if docs:
                logger.info(f"Found {len(docs)} docs after {iteration + 1} iteration(s)")
                return docs
        
        logger.info(f"No docs found after {max_iterations} iterations")
        return []
    
    def _looks_like_error_log(self, question: str) -> bool:
        """
        Detect if the user message looks like a pasted error (HTTP status, code, msg, etc.)
        so we can boost retrieval with error-code docs.
        """
        q = question.strip()
        if not q or len(q) > 2000:
            return False
        # HTTP status in message (e.g. "400", "401", "429", "500")
        if re.search(r"\b(400|401|403|404|429|500)\b", q):
            return True
        # JSON-style error: "code" and "msg"
        if '"code"' in q and '"msg"' in q:
            return True
        if "'code'" in q and "'msg'" in q:
            return True
        # Numeric error code (e.g. -1111, -1121)
        if re.search(r"-\d{4}\b", q):
            return True
        # Common error log patterns
        if re.search(r"POST\s+/fapi|GET\s+/fapi", q, re.I) and re.search(r"\b(400|401|429)\b", q):
            return True
        return False

    def _decompose_query(self, question: str) -> str:
        """
        Decompose complex/indirect questions into simpler, more direct API-related queries.
        
        Args:
            question: Complex or indirect question
            
        Returns:
            Simplified, direct query focused on API aspects
        """
        decompose_prompt = f"""Break down this complex or indirect question into a simpler, direct API-related query.

Original Question: {question}

Extract the core API-related intent:
1. If it's about implementation/automation → Focus on "how to" + API keywords
2. If it's about errors/issues → Focus on error type + API keywords  
3. If it's indirect (e.g., "my bot is broken") → Rewrite as direct API question
4. If it's multi-part → Extract the main API question

Examples:
- "my bot keeps crashing when placing orders" → "order placement API error troubleshooting"
- "how do I make this work automatically" → "API automation order placement"
- "something is wrong with authentication" → "authentication API error"

Return ONLY the simplified query, nothing else."""
        
        try:
            response = self.gemini_client.client.models.generate_content(
                model=self.gemini_client.model_name,
                contents=decompose_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=100
                )
            )
            
            if response and response.text:
                decomposed = response.text.strip()
                # Remove quotes if present
                decomposed = decomposed.strip('"\'')
                return decomposed
        except Exception as e:
            logger.warning(f"Error decomposing query: {e}")
        
        return question  # Fallback to original
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            'total_documents': self.vector_store.get_count(),
            'model': self.gemini_client.model_name
        }

    def learn_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Learn new unstructured text (Admin only). Chunks long text. Optional metadata (e.g. source, filename).
        
        Note: If ENABLE_CHANGELOG_WATCHER is true, learned content will be cleared during daily re-ingestion.
        For permanent storage, add content to docs/ directory instead.
        """
        base = metadata or {}
        base['source'] = base.get('source', 'admin_learn')
        base['learned'] = True  # Mark as learned content
        
        # Enhance text for better retrieval: add keywords for common queries
        enhanced_text = self._enhance_learned_text(text)
        
        if len(enhanced_text) > 1500:
            chunks = self.document_loader.chunk_document(enhanced_text, chunk_size=1000, overlap=200)
            metadatas = [dict(base, chunk_index=i, total_chunks=len(chunks)) for i in range(len(chunks))]
            self.vector_store.add_documents(chunks, metadatas, None)
            logger.info(f"Learned {len(chunks)} chunks ({len(text)} chars)")
        else:
            self.vector_store.add_documents([enhanced_text], [base], None)
            logger.info(f"Learned new text: {text[:50]}...")
    
    def _enhance_learned_text(self, text: str) -> str:
        """
        Enhance learned text with keywords to improve retrieval.
        Adds common query variations for URLs, dashboard, web access, etc.
        Distinguishes between web dashboard URLs and API base URLs.
        """
        text_lower = text.lower()
        enhanced = text
        
        # If text contains a URL, add common query variations
        if 'http' in text_lower or 'www.' in text_lower or '.com' in text_lower:
            # Extract URL if present
            import re
            url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text)
            if url_match:
                url = url_match.group(1)
                
                # Determine if it's a web dashboard URL or API base URL
                is_api_url = 'trade.mudrex.com' in url or '/fapi/' in url or '/api/' in url
                is_dashboard_url = 'www.mudrex.com' in url or 'pro-trading' in url
                
                if is_dashboard_url:
                    # Web dashboard URL variations
                    variations = [
                        f"Dashboard URL: {url}",
                        f"Web URL: {url}",
                        f"API trading URL: {url}",
                        f"Access URL: {url}",
                        f"Website: {url}",
                        f"Web dashboard: {url}",
                        f"Browser URL: {url}",
                    ]
                    enhanced = f"{text}\n\n" + "\n".join(variations)
                elif is_api_url:
                    # API base URL variations
                    variations = [
                        f"API base URL: {url}",
                        f"REST API URL: {url}",
                        f"API endpoint: {url}",
                        f"API base endpoint: {url}",
                    ]
                    enhanced = f"{text}\n\n" + "\n".join(variations)
                else:
                    # Generic URL - add both types of variations
                    variations = [
                        f"URL: {url}",
                        f"Web URL: {url}",
                        f"Dashboard URL: {url}",
                    ]
                    enhanced = f"{text}\n\n" + "\n".join(variations)
        
        # If text mentions "dashboard", add URL-related keywords
        if 'dashboard' in text_lower and 'www.mudrex.com' in text_lower:
            enhanced = f"{enhanced}\n\nKeywords: dashboard URL, web URL, API dashboard, trading dashboard, access URL, browser URL"
        elif 'dashboard' in text_lower:
            enhanced = f"{enhanced}\n\nKeywords: dashboard URL, web URL, API dashboard"
        
        return enhanced

    def set_fact(self, key: str, value: str) -> None:
        """Set a strict fact (Admin only)"""
        self.fact_store.set(key, value)

    def delete_fact(self, key: str) -> bool:
        """Delete a strict fact (Admin only)"""
        return self.fact_store.delete(key)
