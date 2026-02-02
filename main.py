"""
Mudrex API Bot - Main Entry Point
A helpful junior dev + community admin bot for Mudrex API support

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

from src.config import config
from src.rag import RAGPipeline
from src.bot import MudrexBot
from src.mcp import MudrexMCPClient
from src.tasks.scheduler import setup_scheduler
from src.lib.error_reporter import report_error_sync, report_error
from src.health import set_components, start_health_server
from src.lib.metrics import init_service_info, update_documents_count

# Configure structured logging
from src.lib.logging import configure_logging, get_logger

# Use JSON format in production, colored console in development
is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production"
configure_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=is_production,
)

logger = get_logger(__name__)


def validate_config():
    """Validate required configuration"""
    errors = config.validate()
    
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease check your .env file. See .env.example for reference.")
        sys.exit(1)


async def async_main():
    """Async main application entry point"""
    logger.info("=" * 60)
    logger.info("  Mudrex API Bot - Starting Up")
    logger.info("=" * 60)
    
    # Validate configuration
    validate_config()
    logger.info("Configuration validated")
    
    # Start health server FIRST so Railway health check passes during slow init
    health_port = int(os.getenv("PORT") or os.getenv("HEALTH_PORT", "8080"))
    health_task = asyncio.create_task(start_health_server(port=health_port))
    logger.info(f"Health server starting on port {health_port}")
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline()
    
    # One-time migration: Pickle → Qdrant (if Qdrant is configured)
    if config.QDRANT_URL and config.QDRANT_API_KEY:
        logger.info("Qdrant configured - checking for migration...")
        try:
            # Check if we're using pickle (not Qdrant)
            if not rag_pipeline.vector_store.use_qdrant:
                logger.info("Currently using pickle storage - attempting migration to Qdrant...")
                pickle_path = Path(config.CHROMA_PERSIST_DIR) / "vectors.pkl"
                if pickle_path.exists():
                    # Migrate existing pickle data
                    if rag_pipeline.vector_store.export_to_qdrant():
                        logger.info("✓ Successfully migrated pickle data to Qdrant")
                        # Reinitialize to use Qdrant
                        rag_pipeline = RAGPipeline()
                    else:
                        logger.warning("Migration failed - will ingest docs directly to Qdrant")
                else:
                    logger.info("No pickle data found - will ingest docs directly to Qdrant")
            else:
                logger.info("Already using Qdrant - no migration needed")
        except Exception as e:
            logger.warning(f"Migration check failed: {e} - continuing with normal flow")
    
    # Check document count
    stats = rag_pipeline.get_stats()
    if stats['total_documents'] == 0:
        logger.warning("No documents in vector store!")
        logger.info("Attempting to auto-ingest documentation...")
        
        # Try to ingest docs automatically
        docs_dir = Path(__file__).parent / "docs"
        if docs_dir.exists() and any(docs_dir.glob("*.md")):
            logger.info(f"Found docs directory with {len(list(docs_dir.glob('*.md')))} files")
            try:
                num_chunks = rag_pipeline.ingest_documents(str(docs_dir))
                if num_chunks > 0:
                    logger.info(f"✓ Successfully auto-ingested {num_chunks} chunks")
                    stats = rag_pipeline.get_stats()
                    logger.info(f"✓ Vector store now has {stats['total_documents']} documents")
                    # Clear semantic cache so old cached answers (e.g. from before re-ingest) are not returned
                    if rag_pipeline.semantic_cache:
                        rag_pipeline.semantic_cache.clear()
                        logger.info("Cleared semantic cache (stale answers from previous docs removed)")
                else:
                    logger.warning("Ingestion returned 0 chunks. Check docs directory.")
            except Exception as e:
                logger.error(f"Failed to auto-ingest docs: {e}")
                logger.info("Run manually: python3 scripts/ingest_docs.py")
        else:
            logger.warning(f"Docs directory not found or empty: {docs_dir}")
            logger.info("Run: python3 scripts/scrape_docs.py && python3 scripts/ingest_docs.py")
    else:
        logger.info(f"Loaded {stats['total_documents']} document chunks")
    
    # Initialize MCP client with service account (read-only key for public data)
    mcp_client = None
    if config.MCP_ENABLED:
        logger.info("Initializing MCP client (service account mode)...")
        mcp_client = MudrexMCPClient(api_secret=config.MUDREX_API_SECRET)
        try:
            await mcp_client.connect()
            if mcp_client.is_authenticated():
                tools = mcp_client.get_safe_tools()
                logger.info(f"MCP connected with service account - {len(tools)} public tools available")
            else:
                logger.warning("MCP service account key not configured - public data features disabled")
                logger.info("Set MUDREX_API_SECRET in .env with a read-only service account key")
        except Exception as e:
            logger.warning(f"MCP connection failed: {e}")
            logger.info("Bot will work without MCP features")
    
    # Initialize bot
    logger.info("Initializing Telegram bot...")
    bot = MudrexBot(rag_pipeline, mcp_client)
    
    # Set components for health checks
    set_components(rag_pipeline=rag_pipeline, mcp_client=mcp_client, bot=bot)
    
    # Initialize metrics
    init_service_info(
        version="2.0.0",
        model=config.GEMINI_MODEL,
        environment=os.getenv("RAILWAY_ENVIRONMENT", "development")
    )
    update_documents_count(stats['total_documents'])
    
    # Scheduler for daily changelog scrape + ingest + broadcast
    scheduler = None
    if config.ENABLE_CHANGELOG_WATCHER:
        docs_dir = Path(__file__).parent / "docs"
        scheduler = setup_scheduler(bot, rag_pipeline, docs_dir)
        scheduler.start()
    
    try:
        # Start the bot
        logger.info("Starting bot...")
        await bot.start_async()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("  Bot is LIVE! Press Ctrl+C to stop.")
        logger.info(f"  Health endpoint: http://localhost:{health_port}/health")
        logger.info("=" * 60)
        logger.info("")
        
        # Keep running until interrupted
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        # Check if it's a Telegram Conflict error
        error_msg = str(e)
        if "Conflict" in error_msg or "terminated by other getUpdates" in error_msg:
            logger.error("=" * 60)
            logger.error("BOT STARTUP FAILED: Multiple instances detected")
            logger.error("=" * 60)
            logger.error("Please ensure only ONE bot instance is running.")
            logger.error("Check Railway deployments and stop any duplicate instances.")
            logger.error("=" * 60)
        else:
            logger.error(f"Fatal error: {e}", exc_info=True)
        await report_error(e, "crash")
        raise
    finally:
        logger.info("Shutting down...")
        
        if scheduler:
            scheduler.shutdown(wait=False)
        await bot.stop()
        
        if mcp_client:
            await mcp_client.close()
        
        logger.info("Shutdown complete")


def setup_global_error_handlers():
    """Setup global error handlers for uncaught exceptions"""
    import sys
    
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error = exc_value if isinstance(exc_value, Exception) else Exception(str(exc_value))
        logger.error(f"Uncaught exception: {error}", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Report to Station Master (sync version for exception hook)
        report_error_sync(error, "crash")
        
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def handle_unhandled_rejection(reason):
        """Handle unhandled promise rejections (for asyncio)"""
        error = reason if isinstance(reason, Exception) else Exception(str(reason))
        logger.error(f"Unhandled exception in async task: {error}", exc_info=True)
        report_error_sync(error, "exception")
    
    # Set exception handler
    sys.excepthook = handle_uncaught_exception
    
    # Note: Python doesn't have unhandledRejection like Node.js,
    # but asyncio tasks that fail are caught in the event loop


def main():
    """Main entry point"""
    # Setup global error handlers
    setup_global_error_handlers()
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        report_error_sync(e, "crash")
        sys.exit(1)


if __name__ == "__main__":
    main()
