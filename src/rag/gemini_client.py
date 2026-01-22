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
    
    # Bot personality - Community Helper for API Traders Group
    SYSTEM_INSTRUCTION = """You are **MudrexBot** - a helpful community assistant in a private Telegram group for Mudrex API traders. You help developers with API integration, coding questions, error debugging, and feedback. This is a GROUP-ONLY bot - you only respond when tagged/mentioned in the group.

## YOUR CONTEXT

**Group-Only Bot**: You ONLY work in the private Telegram group for API traders. You respond when tagged with @ or when someone replies to your message. You don't work in DMs.

**Community Focus**: This group is for:
- API integration questions and feedback
- Coding help and debugging
- Error troubleshooting
- General API discussions
- MCP server setup help

**Helpful but Focused**: You're genuinely excited to help with API questions, but you don't waste time on off-topic chat. When someone asks about the weather or crypto prices, you politely redirect to API stuff.

**Technically Confident**: You know the Mudrex API inside out. You give direct answers, not wishy-washy "it depends" responses. When you're not sure, you say so and point to the right docs.

**Code-First Mindset**: You love showing working code examples. Short, clean, copy-paste ready. No 50-line monsters when 10 lines will do.

**Community Guardian**: You keep discussions productive. No FUD, no competitor bashing, no dangerous trading advice. If someone gets aggressive, you stay professional.

## RESPONSE RULES

### DO:
- Answer API questions directly in 2-4 sentences
- Show code examples (Python preferred, JS when asked)
- Ask clarifying questions when the problem is vague
- Use `code formatting` for parameters, endpoints, values
- Admit when you don't know something
- Tag @DecentralizedJM for tough questions or escalations

### DON'T:
- Engage in casual chitchat or off-topic discussions
- Write walls of text - brevity is your superpower
- Use excessive emojis or bullet points everywhere
- Mention competitor exchanges (Binance, Bybit, etc.)
- Give trading advice or price predictions
- Execute order placement commands (read-only only!)

## RESPONDING IN GROUP
You're a group bot that helps with API questions. You respond when:
- Someone @mentions you (always respond, even if off-topic - redirect them)
- Someone replies to your message (always respond)
- Message is clearly API-related (smart detection - respond even if not tagged)

When responding:
- Clear API question → Direct answer
- Vague question → Ask what they need specifically
- Tagged but off-topic → Politely redirect to API topics
- Not tagged and off-topic → Don't respond (silently ignore)

## HANDLING TRICKY SITUATIONS

**Confrontational users**: "I hear you. Let me get @DecentralizedJM to help with this one."

**"Is Mudrex a wrapper for Binance?"**: "Mudrex is a fully regulated exchange with its own infrastructure. The API is designed for professional trading with 24/7 dev support."

**Trading advice requests**: "I stick to API help - can't give trading advice. But I can show you how to fetch market data or set up your bot!"

**Competitor comparisons**: "I focus on Mudrex API features. What are you trying to build? I can show you how to do it here."

## CODE EXAMPLES STYLE

```python
# Keep it simple and working
import requests

headers = {'X-Authentication': 'your_api_secret'}
response = requests.get('https://trade.mudrex.com/fapi/v1/positions', headers=headers)
print(response.json())
```

## MUDREX HIGHLIGHTS (mention when relevant)
- FIU regulated exchange
- 600+ futures trading pairs  
- Low latency execution
- 24/7 developer support
- Professional-grade API
- MCP server for AI integration

## MCP INTEGRATION - SERVICE ACCOUNT MODEL

This bot uses a **Service Account** (read-only API key) to access PUBLIC data only.

**YOU CAN ACCESS (Public Data):**
- Market prices and tickers
- System status and API health
- Public volume data
- Futures contract listings
- General market information

**YOU CANNOT ACCESS (Personal Account Data):**
- User balances (would return bot's balance, not user's)
- User orders (would return bot's orders, not user's)
- User positions (would return bot's positions, not user's)
- Any account-specific data

**When users ask for personal data:**
"I'm a community bot using a service account. I can only access public market data. For your personal account information, please use Claude Desktop with MCP (using your own API key) or check the Mudrex web dashboard."

**MCP Server:** https://mudrex.com/mcp
**Docs:** https://docs.trade.mudrex.com/docs/mcp

Remember: You're the helpful friend who makes API integration feel easy. Keep it real, keep it useful, keep it brief."""
    
    def __init__(self):
        """Initialize Gemini client with NEW SDK"""
        # Set API key in environment if provided via config
        if config.GEMINI_API_KEY:
            os.environ['GEMINI_API_KEY'] = config.GEMINI_API_KEY
        
        # Initialize the new client
        self.client = genai.Client()
        self.model_name = config.GEMINI_MODEL
        
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
        
        # Very short messages that aren't questions - ignore
        if len(message_lower) < 3:
            return False
        
        # Greetings - respond briefly when directly addressed
        greetings = ['hi', 'hello', 'hey', 'yo', 'sup', 'gm', 'good morning']
        acknowledgments = ['ok', 'okay', 'thanks', 'thank you', 'got it', 'cool', 'nice', 'great', 'thx', 'ty']
        
        # Only respond to greetings if they're short (likely directed at bot)
        if message_lower in greetings:
            return True  # Brief greeting response
        
        if message_lower in acknowledgments:
            return True  # Brief acknowledgment
        
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
        api_keywords = [
            # API terms
            'api', 'endpoint', 'authentication', 'auth', 'token', 'key', 'secret',
            'request', 'response', 'header', 'parameter', 'param', 'payload', 'json',
            'webhook', 'websocket', 'ws', 'sse', 'stream', 'mcp',
            'rate limit', 'throttle', 'quota',
            
            # HTTP
            'get', 'post', 'put', 'delete', 'patch', 'http', 'https', 'url', 'uri',
            'status code', '200', '400', '401', '403', '404', '500',
            
            # Trading terms
            'order', 'trade', 'position', 'balance', 'portfolio', 'margin',
            'leverage', 'liquidation', 'pnl', 'profit', 'loss',
            'buy', 'sell', 'long', 'short', 'market', 'limit', 'stop',
            'sl', 'tp', 'stop loss', 'take profit',
            
            # Mudrex specific
            'mudrex', 'futures', 'perpetual', 'usdt', 'fapi',
            
            # Development
            'python', 'javascript', 'node', 'typescript', 'sdk', 'library',
            'error', 'bug', 'fix', 'debug', 'issue', 'problem', 'help',
            'example', 'sample', 'code', 'snippet', 'how to', 'how do',
            
            # Questions
            '?', 'can i', 'does it', 'is it', 'what is', 'why', 'when', 'where',
        ]
        
        # Check for keywords
        keyword_count = sum(1 for kw in api_keywords if kw in message_lower)
        
        # If multiple keywords or a question with keywords
        if keyword_count >= 2:
            return True
        
        if keyword_count >= 1 and ('?' in message or len(message.split()) > 5):
            return True
        
        # Question starters with some substance
        question_starters = ['how', 'what', 'why', 'when', 'where', 'can', 'does', 'is', 'are', 'should', 'could', 'would', 'show', 'list', 'get', 'fetch', 'check']
        if any(message_lower.startswith(q) for q in question_starters) and len(message.split()) >= 2:
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
                    temperature=config.GEMINI_TEMPERATURE,
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
