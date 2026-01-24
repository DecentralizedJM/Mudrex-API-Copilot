"""
Verification script for Coding Skills
Tests if the bot returns code snippets as requested.
"""
import logging
from src.rag.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_coding_response():
    logger.info("Initializing Gemini Client...")
    client = GeminiClient()
    
    # Test Question
    query = "How do I place a limit order in Python?"
    print(f"\nQuery: '{query}'")
    
    # Generate response (using empty context for pure model test or minimal context)
    # We want to see if it unleashes the coding skill even with minimal context
    response = client.generate_response(query, context_documents=[])
    
    print(f"\nResponse:\n{response}\n")
    
    if "```python" in response or "import requests" in response:
        print("✅ Coding verification: SUCCESS (Code block detected)")
    else:
        print("❌ Coding verification: FAILED (No code block found)")

if __name__ == "__main__":
    test_coding_response()
