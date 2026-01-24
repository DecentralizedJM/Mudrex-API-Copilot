
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import RAGPipeline

# Configure logging to suppress debug noise
logging.basicConfig(level=logging.ERROR)

def verify():
    print("Initializing RAG Pipeline...")
    rag = RAGPipeline()
    
    questions = [
        "How do I create an API key?",
        "What are the rate limits for the API?",
        "How do I get the list of assets?",
        "What does error code -1121 mean?",
        "Can I use my key on multiple systems?"
    ]
    
    print("\nStarting Verification...")
    print("-" * 50)
    
    for q in questions:
        print(f"\nQuestion: {q}")
        response = rag.query(q)
        print(f"Relevance: {response.get('is_relevant')}")
        print(f"Sources: {len(response.get('sources', []))}")
        if response.get('sources'):
            print(f"Top Source: {response['sources'][0]['filename']}")
        print(f"Answer snippet: {response.get('answer', '')[:200]}...")
        print("-" * 50)

if __name__ == "__main__":
    verify()
