"""
Verification script for Semantic Intent Parsing
Tests:
1. Natural Language -> SET_FACT
2. Natural Language -> LEARN
"""
import logging
import json
from src.rag.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_semantic_intent():
    logger.info("Initializing Gemini Client...")
    client = GeminiClient()
    
    # Test 1: Set Fact
    msg1 = "Hey, just so you know, the rate limit is strictly 100 requests per minute now."
    print(f"\nMessage: '{msg1}'")
    result1 = client.parse_learning_instruction(msg1)
    print(f"Result: {json.dumps(result1, indent=2)}")
    
    if result1.get('action') == 'SET_FACT' and result1.get('key') == 'RATE_LIMIT':
        print("✅ SET_FACT Detection: SUCCESS")
    else:
        print("❌ SET_FACT Detection: FAILED")

    # Test 2: Learn
    msg2 = "The new beta endpoint /v1/super-beta allows high frequency trading but requires a special key."
    print(f"\nMessage: '{msg2}'")
    result2 = client.parse_learning_instruction(msg2)
    print(f"Result: {json.dumps(result2, indent=2)}")
    
    if result2.get('action') == 'LEARN':
        print("✅ LEARN Detection: SUCCESS")
    else:
        print("❌ LEARN Detection: FAILED")
        
    # Test 3: Normal Chat
    msg3 = "How do I authenticate?"
    print(f"\nMessage: '{msg3}'")
    result3 = client.parse_learning_instruction(msg3)
    print(f"Result: {json.dumps(result3, indent=2)}")
    
    if result3.get('action') == 'NONE':
        print("✅ NONE Detection: SUCCESS")
    else:
        print("❌ NONE Detection: FAILED")

if __name__ == "__main__":
    test_semantic_intent()
