
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import RAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_persona():
    print("Initializing RAG Pipeline with new Persona...")
    rag = RAGPipeline()

    log_message = """
    bot_log.txt:4944:2026-01-14 18:36:10 [ERROR] AsyncBot: ❌ Telegram API Error: 409
    bot_log.txt:4945:2026-01-14 18:36:14 [WARNING] mudrex.client: Rate limited, retrying in 1.0s...
    """
    print("\n1. Testing Response to Error Logs (409 Conflict):")
    response = rag.query(log_message)
    print("-" * 50)
    print(response['answer'])
    print("-" * 50)
    
    if "409" in response['answer'] and "two instances" in response['answer'].lower():
        print("   ✅ Bot correctly identified 409 Conflict issue")
    else:
        print("   ❌ Bot failed to identify specific 409 issue")

    # Test Persona Style
    print("\n2. Testing Persona Style (Direct vs Chatty):")
    q = "How do I authenticate?"
    response = rag.query(q)
    print(f"Q: {q}")
    print(f"A: {response['answer'][:100]}...")
    
    if "hope" in response['answer'].lower() or "please" in response['answer'].lower():
         print("   ⚠️  Bot might still be too polite/fluffy")
    else:
         print("   ✅ Bot seems direct")

    # Test Latency Knowledge
    print("\n3. Testing Latency Knowledge:")
    q_latency = "What is the rate limit and latency?"
    response = rag.query(q_latency)
    print(f"Q: {q_latency}")
    print(f"A: {response['answer'][:150]}...")
    
    if "2 requests/second" in response['answer'] and "100-300ms" in response['answer']:
        print("   ✅ Bot answered BOTH rate limit and latency")
    else:
        print("   ❌ Bot failed to provide complete info")

if __name__ == "__main__":
    test_persona()
