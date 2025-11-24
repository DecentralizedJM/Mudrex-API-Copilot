"""
Gemini AI integration for generating responses

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License - See LICENSE file for details.
"""
import logging
from typing import List, Dict, Any, Optional
import os
import google.generativeai as genai

from ..config import config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Handles interactions with Gemini AI"""
    
    def __init__(self):
        """Initialize Gemini client"""
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Initialized Gemini client with model: {config.GEMINI_MODEL}")
    
    def is_api_related_query(self, message: str) -> bool:
        """
        Determine if a message is an API-related question
        
        Args:
            message: User message
            
        Returns:
            True if the message is API-related
        """
        # Quick keyword check first
        api_keywords = [
            'api', 'endpoint', 'authentication', 'auth', 'token',
            'request', 'response', 'error', 'code', 'status',
            'header', 'parameter', 'payload', 'json', 'webhook',
            'rate limit', 'authentication', 'authorization',
            'get', 'post', 'put', 'delete', 'patch',
            'how to', 'how do i', 'can i', 'does it', 'why',
            '?', 'help', 'issue', 'problem', 'not working'
        ]
        
        message_lower = message.lower()
        
        # Check for question indicators
        has_question_mark = '?' in message
        has_question_word = any(message_lower.startswith(word) for word in ['how', 'what', 'why', 'when', 'where', 'can', 'does', 'is', 'are'])
        has_api_keyword = any(keyword in message_lower for keyword in api_keywords)
        
        # If it looks like a question about APIs, return True
        if (has_question_mark or has_question_word) and has_api_keyword:
            return True
        
        # For more complex cases, use Gemini (optional, can be expensive)
        # For now, use keyword-based detection
        return has_api_keyword and len(message.split()) > 3
    
    def generate_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response using RAG
        
        Args:
            query: User query
            context_documents: Relevant documents from vector store
            chat_history: Optional chat history for context
            
        Returns:
            Generated response
        """
        # Build context from retrieved documents
        context = self._build_context(context_documents)
        
        # Create prompt
        prompt = self._create_prompt(query, context, chat_history)
        
        try:
            # Generate response with the updated SDK
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.GEMINI_TEMPERATURE,
                    max_output_tokens=config.GEMINI_MAX_TOKENS,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            # Check if response has candidates
            if not response or not response.candidates:
                logger.warning("No response candidates from Gemini")
                return "I couldn't generate a response. Please try rephrasing your question about the Mudrex API."
            
            # Try to extract text safely
            try:
                answer = response.text.strip()
            except (ValueError, AttributeError) as e:
                logger.error(f"Could not extract text from response: {e}")
                # Try to get text from candidate parts
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    answer = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text')).strip()
                else:
                    return "I couldn't generate a complete response. Please try rephrasing your question about the Mudrex API."
            
            if not answer:
                return "I couldn't find relevant information to answer your question. Please make sure you're asking about the Mudrex API."
            
            # Clean up and format the response
            answer = self._clean_response(answer)
            
            # Ensure response isn't too long for Telegram
            if len(answer) > config.MAX_RESPONSE_LENGTH:
                answer = answer[:config.MAX_RESPONSE_LENGTH - 3] + "..."
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I encountered an error while processing your question. Please try again or rephrase your query."
    
    def _clean_response(self, text: str) -> str:
        """Clean and format response for better Telegram display"""
        import re
        
        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Fix markdown formatting issues
        # Convert ### headers to bold text (Telegram doesn't support headers well)
        text = re.sub(r'###\s+(.+)', r'*\1*', text)
        text = re.sub(r'##\s+(.+)', r'*\1*', text)
        text = re.sub(r'#\s+(.+)', r'*\1*', text)
        
        # Convert markdown lists to bullet points
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        
        # Fix numbered lists
        text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
        
        # Ensure code blocks are properly formatted
        # Replace triple backticks with single backticks for inline code if short
        def replace_short_code_blocks(match):
            code = match.group(1).strip()
            # If code is single line and short, make it inline
            if '\n' not in code and len(code) < 60:
                return f'`{code}`'
            return match.group(0)
        
        text = re.sub(r'```(?:http|json|python|javascript)?\n?(.+?)```', replace_short_code_blocks, text, flags=re.DOTALL)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        # Ensure proper spacing around sections
        text = text.strip()
        
        return text
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        if not documents:
            return "No relevant documentation found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get('metadata', {}).get('filename', 'Unknown')
            content = doc.get('document', '')
            context_parts.append(f"[Source {i}: {source}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Create the complete prompt for Gemini"""
        
        system_instruction = """You are a highly skilled Mudrex community manager and developer intern with deep knowledge of the Mudrex API.

YOUR PERSONALITY:
- Confident, friendly, and approachable - like a smart colleague, not a formal assistant
- Speak naturally and conversationally - avoid robotic or overly formal language
- You're part of the Mudrex community - use "we" when referring to Mudrex features
- Smart and knowledgeable - IQ 200 level understanding of APIs and coding
- Don't cite sources or say "according to documentation" - you just KNOW this stuff

YOUR ROLE:
- Help developers integrate with Mudrex API
- Provide clear, accurate technical guidance
- Write clean code examples when needed
- Be concise but thorough - no fluff

RESPONSE STYLE:
- Start directly with the answer - no "Sure!" or "Of course!" prefixes
- Be confident - "The endpoint uses..." not "According to docs, the endpoint uses..."
- Use emojis very sparingly - only for emphasis when it helps (✓, ⚠️, 💡)
- Keep it real and practical

CODE EXAMPLES:
- Always provide working code when relevant
- Use proper formatting with ``` code blocks
- Include all necessary headers, parameters
- Show complete examples, not fragments

FORMATTING FOR TELEGRAM:
- Use *bold* for API names, endpoints, important terms
- Use `code` for parameters, values, variable names
- Use bullet points (•) for lists
- Keep paragraphs short (2-3 sentences max)
- Use line breaks for readability

IMPORTANT RULES:
- ONLY answer Mudrex API questions - stay technical
- If asked about non-API topics, politely redirect
- Never make up information - if you don't know, say so
- Focus on practical solutions

Example tone:
"The Futures API needs two headers: `X-Authentication` (your API secret) and `X-Time` (millisecond timestamp). Here's how to set it up:

```python
headers = {
    'X-Authentication': 'your_secret_key',
    'X-Time': str(int(time.time() * 1000))
}
```

Make sure you're using milliseconds, not seconds - that's a common gotcha!"
"""
        
        prompt_parts = [system_instruction]
        
        # Add chat history if available
        if chat_history:
            prompt_parts.append("\n--- Recent Conversation ---")
            for msg in chat_history[-3:]:  # Last 3 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.capitalize()}: {content}")
        
        # Add context and query
        prompt_parts.extend([
            f"\n--- Relevant Documentation ---\n{context}",
            f"\n--- User Question ---\n{query}",
            "\n--- Your Response ---"
        ])
        
        return "\n".join(prompt_parts)
