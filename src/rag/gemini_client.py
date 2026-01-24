"""
Gemini AI integration using the NEW google-genai SDK
Model: gemini-3-flash-preview

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import logging
import os
from typing import List, Dict, Any, Optional
import re

from google import genai
from google.genai import types

from ..config import config

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Handles interactions with Gemini AI using the NEW SDK
    Uses google-genai package with genai.Client()
    """
    
    # Bot personality - Technical Community Manager & Debugger
    # Bot personality - Senior Developer & Technical Lead
    SYSTEM_INSTRUCTION = """You are **MudrexBot** - the **Senior Technical Engineer** for the Mudrex API group.
    
    ## CORE DIRECTIVES (STRICT ADHERENCE REQUIRED)
    1.  **CODE FIRST**: When asked about implementation, "how to", or generic coding questions, **ALWAYS** provide a code snippet.
        -   Use **Python (requests)** as the default language.
        -   Wrap code in ```python blocks.
        -   Include imports (e.g., `import requests`).
        -   Add comments explaining critical parameters.
        
    2.  **NO HALLUCINATIONS**: Answer based on the **Relevant Documentation** provided below OR the **Knowledge Base**.
        -   If missing: "I don't have that info in my docs. @DecentralizedJM can you help?"
        
    3.  **DEBUG FIRST**: If logs are present, analyze them immediately.
    
    4.  **ZERO CHIT-CHAT**: Be robotic but helpful. Direct answers only.

    ## RESPONSE PROTOCOL
    - **If known**: Answer directly with code/facts.
    - **If inferred**: State "Based on similar endpoints..."
    - **If unknown**: "Unknown API question. @DecentralizedJM please assist."

    ## KNOWLEDGE BASE (Errors & Limits)
    - **Rate Limits**: 2 requests/second.
    - **Latency**: ~100-300ms.
    - **Error -1121**: Invalid Symbol (Use BTCUSDT).
    - **Error -1022**: Signature Mismatch (Check system clock).

    ## DATA PRIVACY
    - You use a shared **Service Account** (Public Data Only).
    - No personal balances/orders accessible.

    Be the expert. Unlock your full coding potential."""
    
    def __init__(self):
        """Initialize Gemini client with NEW SDK"""
        # Set API key in environment if provided via config
        if config.GEMINI_API_KEY:
            os.environ['GEMINI_API_KEY'] = config.GEMINI_API_KEY
        
        # Initialize the new client
        self.client = genai.Client()
        self.model_name = config.GEMINI_MODEL
        self.temperature = 0.1 # Low temperature for strict factual answers
        
        logger.info(f"Initialized Gemini client (new SDK): {self.model_name}")
    
    def is_api_related_query(self, message: str) -> bool:
        """
        Determine if a message is API-related and worth responding to
        
        Args:
            message: User message
            
        Returns:
            True if the message deserves a response
        """
        message_lower = message.lower().strip()
        
        # LOG DETECTION (High Priority)
        # Check for common log patterns
        log_patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # Timestamp YYYY-MM-DD HH:MM:SS
            r'\[(ERROR|WARNING|INFO|DEBUG|CRITICAL)\]',  # Log levels [ERROR]
            r'Traceback \(most recent call last\)',  # Python traceback
            r'Exception:',  # Exception
            r'Error:',  # Generic error
            r'Telegram API Error:',  # Telegram specific
            r'Rate limited, retrying',  # Bot specific log
            r'bot_log\.txt',  # Filenames in paste
        ]
        
        for pattern in log_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                logger.info("Log pattern detected in message")
                return True
        
        # FILTER CHIT-CHAT (Strict Mode)
        # We ignore pure greetings unless they have substance
        # "Hi" -> Ignore (if not tagged)
        # "Hi, help me" -> Respond
        
        # Very short messages that aren't questions - ignore
        if len(message_lower) < 5:
            return False
            
        # Code detection - always respond to code
        code_patterns = [
            r'```',  # Code blocks
            r'`[^`]+`',  # Inline code
            r'def\s+\w+',  # Python functions
            r'class\s+\w+',  # Python classes
            r'import\s+\w+',  # Python imports
            r'from\s+\w+\s+import',  # Python from imports
            r'async\s+def',  # Async functions
            r'await\s+',  # Await calls
            r'function\s+\w+',  # JS functions
            r'const\s+\w+\s*=',  # JS const
            r'let\s+\w+\s*=',  # JS let
            r'requests\.',  # Python requests
            r'fetch\(',  # JS fetch
            r'axios\.',  # Axios
            r'\.get\(|\.post\(|\.put\(|\.delete\(',  # HTTP methods
            r'X-Authentication',  # Mudrex auth header
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        # API and trading keywords
        # STRONG keywords (Sufficient alone if msg length > 5)
        strong_keywords = [
            'mudrex', 'fapi', 'api', 'endpoint', 'webhook', 'websocket', 'mcp',
            'x-authentication', 'auth', 'token', 'secret', 'jwt',
            'btc', 'eth', 'usdt', 'futures', 'perpetual'
        ]
        
        # WEAK keywords (Need at least one STRONG keyword or another WEAK keyword)
        weak_keywords = [
            'price', 'order', 'trade', 'position', 'balance', 'margin',
            'leverage', 'liquidation', 'profit', 'loss', 'buy', 'sell',
            'long', 'short', 'market', 'limit', 'stop', 'error', 'bug',
            'fix', 'help', 'code', 'python', 'javascript', 'rate', 'latency'
        ]
        
        # Count matches
        strong_count = sum(1 for kw in strong_keywords if kw in message_lower)
        weak_count = sum(1 for kw in weak_keywords if kw in message_lower)
        
        # LOGIC:
        # 1. Any STRONG keyword -> Pass
        # 2. At least 2 WEAK keywords -> Pass (e.g. "price limit")
        # 3. Otherwise -> Ignore (e.g. "price of mars dust" has only "price")
        
        if strong_count >= 1:
            return True
            
        if weak_count >= 2:
            return True
            
        return False
    
    def generate_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response using the NEW Gemini SDK
        
        Args:
            query: User query
            context_documents: Relevant documents from vector store
            chat_history: Optional chat history
            
        Returns:
            Generated response
        """
        # Build the prompt
        prompt = self._build_prompt(query, context_documents, chat_history)
        
        try:
            # Use the new SDK format
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_INSTRUCTION,
                    temperature=self.temperature,
                    max_output_tokens=config.GEMINI_MAX_TOKENS,
                )
            )
            
            # Extract response text
            answer = response.text if response.text else ""
            
            if not answer:
                return "What would you like to know about the Mudrex API? I can help with authentication, orders, positions, or MCP setup."
            
            # Clean and format
            answer = self._clean_response(answer)
            
            # Truncate if too long
            if len(answer) > config.MAX_RESPONSE_LENGTH:
                answer = answer[:config.MAX_RESPONSE_LENGTH - 100] + "\n\n_(Response truncated - ask a more specific question!)_"
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "Hit a snag there. What's your API question? I'll give it another shot."
    
    def _build_prompt(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build the complete prompt"""
        parts = []
        
        # Add context from RAG
        if context_documents:
            context = self._format_context(context_documents)
            parts.append(f"## Relevant Documentation\n{context}\n")
        
        # Add chat history
        if chat_history:
            history = self._format_history(chat_history[-4:])  # Last 4 messages
            parts.append(f"## Recent Conversation\n{history}\n")
        
        # Add the query
        parts.append(f"## User Question\n{query}")
        
        return "\n".join(parts)
    
    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format context documents"""
        if not documents:
            return "No specific documentation found."
        
        formatted = []
        for i, doc in enumerate(documents[:5], 1):  # Max 5 docs
            source = doc.get('metadata', {}).get('filename', 'docs')
            content = doc.get('document', '')[:800]  # Limit each doc
            formatted.append(f"[{source}]\n{content}")
        
        return "\n\n".join(formatted)
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format chat history"""
        formatted = []
        for msg in history:
            role = msg.get('role', 'user').capitalize()
            content = msg.get('content', '')[:200]  # Limit length
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    def _clean_response(self, text: str) -> str:
        """Clean and format response for Telegram"""
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Convert markdown headers to bold (Telegram friendly)
        text = re.sub(r'^#{1,3}\s+(.+)$', r'*\1*', text, flags=re.MULTILINE)
        
        # Fix bullet points
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        
        # Ensure code blocks are clean
        text = re.sub(r'```(\w+)?\n', r'```\1\n', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def parse_learning_instruction(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to see if it's a teaching instruction.
        Returns:
            {
                'action': 'LEARN' | 'SET_FACT' | 'NONE',
                'content': str,
                'key': str (optional),
                'value': str (optional)
            }
        """
        prompt = f"""
        Analyze this admin message for teaching intent.
        
        Message: "{text}"
        
        Identify if the admin wants to:
        1. SET_FACT: Define a strict rule/constant (e.g., "Latency is 200ms", "Rate limit is 5").
        2. LEARN: Add general knowledge/context (e.g., "The new endpoint handles order processing like this...").
        3. NONE: Just a regular chat or question.
        
        Return JSON ONLY:
        {{
            "action": "SET_FACT" | "LEARN" | "NONE",
            "key": "KEY_NAME" (For SET_FACT, e.g. LATENCY),
            "value": "Value" (For SET_FACT),
            "content": "Cleaned text to learn" (For LEARN)
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return {"action": "NONE"}

    def get_brief_response(self, message_type: str) -> str:
        """Get a brief response for greetings/acknowledgments"""
        import random
        
        responses = {
            'greeting': [
                "Hey! What API question can I help with?",
                "Hi there! Got an API question?",
                "Hey! Need help with the Mudrex API?",
            ],
            'thanks': [
                "Happy to help! Let me know if you need anything else.",
                "Anytime! More questions? I'm here.",
                "You got it! Ping me if you get stuck.",
            ],
            'acknowledgment': [
                "Let me know if you need more help!",
                "Cool! I'm here if you have more questions.",
                "Got it! Anything else?",
            ],
        }
        
        return random.choice(responses.get(message_type, responses['acknowledgment']))
