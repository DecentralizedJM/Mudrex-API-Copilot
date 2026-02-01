#!/usr/bin/env python3
"""
One-time migration: Pickle → Qdrant, or re-ingest docs into Qdrant

Run locally:  python scripts/migrate_to_qdrant.py
Run on Railway: railway run python scripts/migrate_to_qdrant.py

Requires: QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY in environment
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    from src.config import config

    # Check Qdrant config
    if not config.QDRANT_URL or not config.QDRANT_API_KEY:
        logger.error("QDRANT_URL and QDRANT_API_KEY must be set")
        sys.exit(1)

    # Check pickle exists
    pickle_path = Path(config.CHROMA_PERSIST_DIR) / "vectors.pkl"

    if pickle_path.exists():
        logger.info("Found pickle data - migrating to Qdrant...")
        from src.rag.vector_store import VectorStore

        store = VectorStore()
        # Ensure db_file is set for export (in case we initialized with Qdrant)
        store.db_file = pickle_path
        if store.export_to_qdrant():
            logger.info("✓ Migration complete")
        else:
            logger.error("Migration failed")
            sys.exit(1)
    else:
        logger.info("No pickle data found - re-ingesting docs into Qdrant...")
        from src.rag import RAGPipeline

        docs_dir = Path(__file__).parent.parent / "docs"
        if not docs_dir.exists():
            logger.error(f"Docs directory not found: {docs_dir}")
            sys.exit(1)

        doc_files = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.txt"))
        if not doc_files:
            logger.error(f"No .md or .txt files in {docs_dir}")
            sys.exit(1)

        logger.info(f"Found {len(doc_files)} doc files")
        pipeline = RAGPipeline()
        num_chunks = pipeline.ingest_documents(str(docs_dir))

        if num_chunks > 0:
            count = pipeline.vector_store.get_count()
            logger.info(f"✓ Ingested {num_chunks} chunks into Qdrant (total: {count})")
        else:
            logger.error("Ingestion returned 0 chunks")
            sys.exit(1)


if __name__ == "__main__":
    main()
