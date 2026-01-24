
import os
import sys
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import config

# Load env
load_dotenv()
if config.GEMINI_API_KEY:
    os.environ['GEMINI_API_KEY'] = config.GEMINI_API_KEY

def test_embeddings():
    print(f"Testing embeddings with model: {config.EMBEDDING_MODEL}")
    
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    text1 = "How do I authenticate with the API?"
    text2 = "To authenticate, use the X-Authentication header."
    text3 = "What is the capital of France?"
    
    try:
        # Get embeddings
        print("Generating embeddings...")
        
        def get_embedding(text):
            result = client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=text,
            )
            return result.embeddings[0].values
            
        emb1 = get_embedding(text1)
        emb2 = get_embedding(text2)
        emb3 = get_embedding(text3)
        
        print(f"Embedding size: {len(emb1)}")
        
        # Calculate similarity
        vec1 = np.array(emb1).reshape(1, -1)
        vec2 = np.array(emb2).reshape(1, -1)
        vec3 = np.array(emb3).reshape(1, -1)
        
        sim12 = cosine_similarity(vec1, vec2)[0][0]
        sim13 = cosine_similarity(vec1, vec3)[0][0]
        
        print("\nResults:")
        print(f"Similarity (Query vs Answer): {sim12:.4f}")
        print(f"Similarity (Query vs Irrelevant): {sim13:.4f}")
        
        if sim12 > sim13:
            print("✓ SUCCESS: Relevant text is more similar")
        else:
            print("✗ FAILURE: Irrelevant text is more similar")
            
        if sim12 < 0.1:
            print("⚠️ WARNING: Similarity is very low even for relevant text. Check embedding model dimensions or normalization.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_embeddings()
