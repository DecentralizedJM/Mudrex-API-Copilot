#!/usr/bin/env python3
"""
QA Watchdog Bot - Entry Point

A QA/monitoring bot that tests the Mudrex API Copilot by:
1. Sending test questions to a Telegram group
2. Grading the copilot's responses
3. Reporting failures with detailed reports
"""
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, Config
from bot.watchdog import QAWatchdogBot
from scheduler.qa_scheduler import setup_scheduler, get_next_runs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

# Suppress httpx/httpcore INFO logs - they expose tokens in request URLs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Health check server
_health_app = None


async def start_health_server(port: int) -> None:
    """Start a simple health check server"""
    from aiohttp import web
    
    async def health_handler(request):
        return web.json_response({"status": "healthy", "service": "qa-watchdog"})
    
    async def ready_handler(request):
        return web.json_response({"status": "ready"})
    
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/health/live", health_handler)
    app.router.add_get("/health/ready", ready_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"Health server started on port {port}")


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("  QA Watchdog Bot - Starting Up")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = get_config()
        logger.info("Configuration loaded")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Start health server
    await start_health_server(config.HEALTH_PORT)
    
    # Initialize bot
    bot = QAWatchdogBot(config)
    await bot.initialize()
    logger.info("Bot initialized")
    
    # Setup scheduler
    scheduler = setup_scheduler(bot, config)
    scheduler.start()
    logger.info("Scheduler started")
    
    # Log next run times
    next_runs = get_next_runs(scheduler)
    logger.info("Next scheduled runs:")
    for job_id, next_time in next_runs.items():
        logger.info(f"  - {job_id}: {next_time}")
    
    # Delay before starting bot - lets old instance shut down during redeploy (avoids Conflict)
    delay = config.BOT_STARTUP_DELAY
    if delay > 0:
        logger.info(f"Waiting {delay}s before starting bot (avoids Conflict during redeploy)...")
        await asyncio.sleep(delay)
    
    # Start the bot
    await bot.start()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("  QA Watchdog Bot is LIVE!")
    logger.info(f"  Test Group: {config.QA_TEST_GROUP_ID}")
    logger.info(f"  Copilot: @{config.COPILOT_BOT_USERNAME}")
    if config.COPILOT_QA_URL:
        logger.info(f"  Mode: DIRECT API ({config.COPILOT_QA_URL})")
    else:
        logger.info("  Mode: TELEGRAM (wait for reply) - set COPILOT_QA_URL for direct API")
    logger.info(f"  Health: http://localhost:{config.HEALTH_PORT}/health")
    logger.info("=" * 60)
    logger.info("")
    
    # Optional: run a spot check on startup to verify setup
    if config.RUN_QA_ON_STARTUP:
        logger.info("Running spot check on startup (RUN_QA_ON_STARTUP=1)...")
        asyncio.create_task(bot.run_spot_check(count=1))
    
    # Keep running
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()
    
    # Handle signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Wait for stop signal
    await stop_event.wait()
    
    # Cleanup
    logger.info("Shutting down...")
    scheduler.shutdown()
    await bot.stop()
    logger.info("Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
