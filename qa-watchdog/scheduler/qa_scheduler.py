"""
QA Scheduler

Schedules regular QA test runs using APScheduler.

Schedule:
- Daily full QA suite at 3 AM UTC (after copilot's 2 AM re-ingestion)
- Critical tests every 6 hours
- Spot checks every 2 hours
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..bot.watchdog import QAWatchdogBot
from ..config import Config

logger = logging.getLogger(__name__)


async def _run_daily_suite(bot: QAWatchdogBot, config: Config) -> None:
    """Run daily full QA suite"""
    logger.info("Starting scheduled daily QA suite")
    try:
        summary = await bot.run_qa_suite(count=config.DAILY_TEST_COUNT)
        logger.info(f"Daily QA complete: {summary.tests_passed}/{summary.tests_run} passed")
    except Exception as e:
        logger.error(f"Daily QA suite failed: {e}", exc_info=True)


async def _run_critical_tests(bot: QAWatchdogBot, config: Config) -> None:
    """Run critical tests"""
    logger.info("Starting scheduled critical tests")
    try:
        results = await bot.run_critical_tests(count=config.CRITICAL_TEST_COUNT)
        passed = len([r for r in results if r.passed])
        logger.info(f"Critical tests complete: {passed}/{len(results)} passed")
    except Exception as e:
        logger.error(f"Critical tests failed: {e}", exc_info=True)


async def _run_spot_check(bot: QAWatchdogBot, config: Config) -> None:
    """Run spot check"""
    logger.info("Starting scheduled spot check")
    try:
        results = await bot.run_spot_check(count=config.SPOT_CHECK_COUNT)
        passed = len([r for r in results if r.passed])
        logger.info(f"Spot check complete: {passed}/{len(results)} passed")
    except Exception as e:
        logger.error(f"Spot check failed: {e}", exc_info=True)


def setup_scheduler(bot: QAWatchdogBot, config: Config) -> AsyncIOScheduler:
    """
    Set up the QA scheduler.
    
    Schedule:
    - Daily at 3:00 AM UTC: Full QA suite (20 tests)
    - Every 6 hours: Critical tests (5 tests)  
    - Every 2 hours: Spot checks (2 tests)
    
    Args:
        bot: QAWatchdogBot instance
        config: Configuration
    
    Returns:
        Configured scheduler (call .start() to run)
    """
    scheduler = AsyncIOScheduler()
    
    # Daily full QA suite at configured hour (default 3 AM UTC)
    # This runs after the copilot's 2 AM re-ingestion
    scheduler.add_job(
        _run_daily_suite,
        CronTrigger(hour=config.DAILY_QA_HOUR, minute=config.DAILY_QA_MINUTE),
        args=[bot, config],
        id="daily_qa_suite",
        name="Daily Full QA Suite",
        replace_existing=True,
    )
    logger.info(f"Scheduled daily QA suite at {config.DAILY_QA_HOUR:02d}:{config.DAILY_QA_MINUTE:02d} UTC")
    
    # Critical tests every N hours
    scheduler.add_job(
        _run_critical_tests,
        IntervalTrigger(hours=config.CRITICAL_TEST_INTERVAL_HOURS),
        args=[bot, config],
        id="critical_tests",
        name="Critical Tests",
        replace_existing=True,
    )
    logger.info(f"Scheduled critical tests every {config.CRITICAL_TEST_INTERVAL_HOURS} hours")
    
    # Spot checks every N hours
    scheduler.add_job(
        _run_spot_check,
        IntervalTrigger(hours=config.SPOT_CHECK_INTERVAL_HOURS),
        args=[bot, config],
        id="spot_checks",
        name="Spot Checks",
        replace_existing=True,
    )
    logger.info(f"Scheduled spot checks every {config.SPOT_CHECK_INTERVAL_HOURS} hours")
    
    return scheduler


def get_next_runs(scheduler: AsyncIOScheduler) -> dict[str, str]:
    """Get next scheduled run times for each job"""
    next_runs = {}
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        if next_run:
            next_runs[job.id] = next_run.isoformat()
        else:
            next_runs[job.id] = "Not scheduled"
    return next_runs
