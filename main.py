"""
Main entry point for the Mudrex API Documentation Bot

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License - See LICENSE file for details.
Original work - Attribution required for any derivative works.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from telegram import Update

# Change to script directory to ensure relative paths work
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

from src.config import config
from src.rag import RAGPipeline
from src.bot import MudrexBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)


def validate_config():
    """Validate required configuration"""
    errors = []
    
    if not config.TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set")
    
    if not config.GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)


async def async_main():
    """Async main application entry point"""
    logger.info("=" * 50)
    logger.info("Starting Mudrex API Documentation Bot")
    logger.info("=" * 50)
    
    # Validate configuration
    validate_config()
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline()
    
    # Check if documents are loaded
    stats = rag_pipeline.get_stats()
    if stats['total_documents'] == 0:
        logger.warning("No documents found in vector store!")
        logger.info("To add documents, run: python scripts/ingest_docs.py")
        logger.info("Place your API documentation in the 'docs/' folder")
    else:
        logger.info(f"Loaded {stats['total_documents']} document chunks")
    
    # Initialize and start bot
    logger.info("Initializing Telegram bot...")
    bot = MudrexBot(rag_pipeline)
    
    try:
        logger.info("Bot is ready! Starting polling...")
        # Start polling with proper async/await
        await bot.app.initialize()
        await bot.app.start()
        await bot.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep running
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down...")
        await bot.app.updater.stop()
        await bot.app.stop()
        await bot.app.shutdown()


def main():
    """Main entry point"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
