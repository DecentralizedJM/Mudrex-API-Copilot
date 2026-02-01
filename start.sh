#!/bin/bash
# Startup script for Mudrex Bot
# main.py handles: health server (immediate), RAG init, auto-ingestion, and bot

echo "🚀 Starting Mudrex API Bot..."

# Only scrape docs if docs/ is completely missing (main.py will ingest if needed)
if [ ! -d "docs" ]; then
    echo "📚 Docs directory missing. Scraping..."
    python3 scripts/scrape_docs.py || echo "⚠️  Scrape failed. main.py will try ingestion."
fi

# Start main.py - health server comes up immediately, then RAG + ingestion
exec python3 main.py
