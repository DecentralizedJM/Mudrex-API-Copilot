
import pickle
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import config

def inspect_db():
    db_file = Path(config.CHROMA_PERSIST_DIR) / "vectors.pkl"
    print(f"Inspecting {db_file}...")
    
    if not db_file.exists():
        print("File does not exist!")
        return
        
    with open(db_file, 'rb') as f:
        data = pickle.load(f)
        
    docs = data.get('documents', [])
    embeddings = data.get('embeddings', [])
    metas = data.get('metadatas', [])
    
    print(f"Total Documents: {len(docs)}")
    print(f"Total Embeddings: {len(embeddings)}")
    print(f"Total Metadata: {len(metas)}")
    
    if len(docs) > 0:
        print("\nSample Document 1:")
        print(f"Text: {docs[0][:100]}...")
        print(f"Metadata: {metas[0]}")
        print(f"Embedding Shape: {len(embeddings[0]) if embeddings else 'None'}")
        
    # Check for empty embeddings
    empty_embeddings = [i for i, emb in enumerate(embeddings) if not emb or len(emb) == 1]
    if empty_embeddings:
        print(f"\n⚠️ Found {len(empty_embeddings)} empty/invalid embeddings!")
    else:
        print("\n✓ All embeddings look valid (size > 1)")

if __name__ == "__main__":
    inspect_db()
