"""
QA Watchdog Bot

Telegram bot that:
1. Sends test questions to the test group mentioning the copilot
2. Listens for copilot responses
3. Grades responses and reports failures
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

from telegram import Bot, Update, Message
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Absolute imports (app runs as python main.py from qa-watchdog root)
from config import Config
from qa.test_bank import TestBank, TestCase
from qa.grader import ResponseGrader, GradeResult
from qa.reporter import Reporter, ReportManager, DailySummary

logger = logging.getLogger(__name__)


class QAWatchdogBot:
    """
    QA Watchdog Bot that tests the API Copilot.
    
    Workflow:
    1. Send question to group mentioning @API_Assistant_V2_bot
    2. Wait for reply from copilot
    3. Grade the response
    4. Report failures
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize components
        self.test_bank = TestBank(
            gemini_api_key=config.QA_GEMINI_API_KEY,
            data_dir=config.DATA_DIR
        )
        self.grader = ResponseGrader(
            gemini_api_key=config.QA_GEMINI_API_KEY,
            model=config.GEMINI_MODEL
        )
        self.reporter = Reporter(admin_username=config.ADMIN_USERNAME)
        self.report_manager = ReportManager(reports_dir=config.REPORTS_DIR)
        
        # Telegram app
        self.app: Optional[Application] = None
        self.bot: Optional[Bot] = None
        
        # State for tracking responses
        self._pending_tests: dict[int, tuple[TestCase, float]] = {}  # message_id -> (test_case, sent_time)
        self._response_events: dict[int, asyncio.Event] = {}
        self._responses: dict[int, Message] = {}
        
        # QA run state
        self._running = False
        self._current_run_results: list[GradeResult] = []
    
    async def initialize(self) -> None:
        """Initialize the bot"""
        self.app = (
            ApplicationBuilder()
            .token(self.config.QA_TELEGRAM_BOT_TOKEN)
            .build()
        )
        self.bot = self.app.bot
        
        # Register handlers
        self.app.add_handler(CommandHandler("qa_status", self._cmd_status))
        self.app.add_handler(CommandHandler("qa_run", self._cmd_run_qa))
        self.app.add_handler(CommandHandler("qa_critical", self._cmd_run_critical))
        self.app.add_handler(CommandHandler("qa_report", self._cmd_report))
        
        # Handler to catch copilot responses
        self.app.add_handler(MessageHandler(
            filters.Chat(self.config.QA_TEST_GROUP_ID) & filters.TEXT,
            self._on_message
        ))
        
        logger.info("QA Watchdog Bot initialized")
    
    async def start(self) -> None:
        """Start the bot (non-blocking)"""
        if not self.app:
            await self.initialize()
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("QA Watchdog Bot started")
    
    async def stop(self) -> None:
        """Stop the bot"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        
        logger.info("QA Watchdog Bot stopped")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /qa_status command"""
        status = "🟢 Running" if self._running else "⚪ Idle"
        pending = len(self._pending_tests)
        
        msg = f"""*QA Watchdog Status*
        
Status: {status}
Pending Tests: {pending}
Test Group: `{self.config.QA_TEST_GROUP_ID}`
Copilot: @{self.config.COPILOT_BOT_USERNAME}

*Recent Activity:*
"""
        # Get recent reports
        recent = self.report_manager.get_recent_failures(days=1)
        if recent:
            msg += f"📄 {len(recent)} failure report(s) today\n"
        else:
            msg += "✅ No failures today\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    
    async def _cmd_run_qa(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /qa_run command - run full QA suite"""
        if self._running:
            await update.message.reply_text("⚠️ QA run already in progress")
            return
        
        await update.message.reply_text("🚀 Starting full QA suite...")
        
        # Run in background
        asyncio.create_task(self.run_qa_suite(count=self.config.DAILY_TEST_COUNT))
    
    async def _cmd_run_critical(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /qa_critical command - run critical tests only"""
        if self._running:
            await update.message.reply_text("⚠️ QA run already in progress")
            return
        
        await update.message.reply_text("🚀 Starting critical tests...")
        
        # Run in background
        asyncio.create_task(self.run_critical_tests(count=self.config.CRITICAL_TEST_COUNT))
    
    async def _cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /qa_report command - show recent failures"""
        recent = self.report_manager.get_recent_failures(days=7)
        
        if not recent:
            await update.message.reply_text("✅ No failures in the last 7 days!")
            return
        
        msg = f"*Recent Failure Reports ({len(recent)})*\n\n"
        for path in recent[:10]:
            msg += f"📄 `{path.name}`\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    
    def _is_from_copilot(self, message: Message) -> bool:
        """Check if message is from the Copilot bot (it may reply to anyone who asked)."""
        if not message or not message.from_user:
            return False
        username = (message.from_user.username or "").lower()
        copilot = (self.config.COPILOT_BOT_USERNAME or "").lower().lstrip("@")
        return username == copilot
    
    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages - check if it's a copilot response"""
        message = update.message
        if not message or not message.text:
            return
        
        # Case 1: Reply to our test message (ideal)
        if message.reply_to_message:
            original_id = message.reply_to_message.message_id
            if original_id in self._pending_tests and self._is_from_copilot(message):
                self._responses[original_id] = message
                if original_id in self._response_events:
                    self._response_events[original_id].set()
                return
        
        # Case 2: Message from Copilot (not a reply) - Copilot often replies to whoever
        # triggered it (e.g. user who forwarded), not to Stalker. Accept any Copilot
        # message in the group while we're waiting - it's almost certainly our answer.
        if not self._is_from_copilot(message):
            return
        if not self._pending_tests:
            return
        # Match to most recent pending test (we send one, wait, so typically one pending)
        latest_id = max(self._pending_tests.keys(), key=lambda k: self._pending_tests[k][1])
        if latest_id not in self._responses:  # Don't overwrite if we already got a reply
            self._responses[latest_id] = message
            if latest_id in self._response_events:
                self._response_events[latest_id].set()
    
    async def run_qa_suite(self, count: int = 20) -> DailySummary:
        """Run full QA test suite"""
        logger.info(f"Starting QA suite with {count} tests")
        self._running = True
        self._current_run_results = []
        
        try:
            tests = self.test_bank.get_daily_suite(count=count)
            
            for i, test_case in enumerate(tests, 1):
                logger.info(f"Running test {i}/{len(tests)}: {test_case.id}")
                
                result = await self._run_single_test(test_case)
                self._current_run_results.append(result)
                
                # Report failures immediately
                if not result.passed:
                    await self._report_failure(result)
                
                # Wait between tests (respect rate limits)
                if i < len(tests):
                    await asyncio.sleep(self.config.TEST_INTERVAL)
            
            # Generate and send daily summary
            summary = self._generate_summary(self._current_run_results)
            await self._send_summary(summary)
            
            return summary
            
        finally:
            self._running = False
    
    async def run_critical_tests(self, count: int = 5) -> list[GradeResult]:
        """Run critical tests only"""
        logger.info(f"Starting critical tests ({count})")
        self._running = True
        results = []
        
        try:
            tests = self.test_bank.get_critical_tests(count=count)
            
            for i, test_case in enumerate(tests, 1):
                logger.info(f"Critical test {i}/{len(tests)}: {test_case.id}")
                
                result = await self._run_single_test(test_case)
                results.append(result)
                
                # Report failures immediately
                if not result.passed:
                    await self._report_failure(result)
                
                if i < len(tests):
                    await asyncio.sleep(self.config.TEST_INTERVAL)
            
            return results
            
        finally:
            self._running = False
    
    async def run_spot_check(self, count: int = 2) -> list[GradeResult]:
        """Run quick spot check"""
        logger.info(f"Starting spot check ({count})")
        self._running = True
        results = []
        
        try:
            tests = self.test_bank.get_spot_checks(count=count)
            
            for test_case in tests:
                result = await self._run_single_test(test_case)
                results.append(result)
                
                if not result.passed:
                    await self._report_failure(result)
                
                await asyncio.sleep(self.config.TEST_INTERVAL)
            
            return results
            
        finally:
            self._running = False
    
    async def _run_single_test(self, test_case: TestCase) -> GradeResult:
        """Run a single test and grade the response"""
        # Send the question to group (for visibility/logging)
        question_with_mention = f"{test_case.question} @{self.config.COPILOT_BOT_USERNAME}"
        message_id = None
        
        try:
            sent_message = await self.bot.send_message(
                chat_id=self.config.QA_TEST_GROUP_ID,
                text=question_with_mention
            )
            message_id = sent_message.message_id
            sent_time = time.time()
            
            # DIRECT API: Telegram doesn't deliver bot-to-bot messages
            if self.config.COPILOT_QA_URL:
                logger.info(f"Using direct API for test {test_case.id}")
                result = await self._run_via_api(test_case, sent_time)
                return result
            
            # TELEGRAM: Wait for reply (when user quotes or Copilot responds)
            self._pending_tests[message_id] = (test_case, sent_time)
            self._response_events[message_id] = asyncio.Event()
            
            try:
                await asyncio.wait_for(
                    self._response_events[message_id].wait(),
                    timeout=self.config.RESPONSE_TIMEOUT
                )
                
                response_message = self._responses.get(message_id)
                response_time = time.time() - sent_time
                
                if response_message:
                    response_text = response_message.text
                    error_indicators = ["Something went wrong", "try again", "error", "timeout"]
                    is_error = any(ind.lower() in response_text.lower() for ind in error_indicators)
                    
                    if is_error and len(response_text) < 200:
                        result = self.grader.grade_error_response(
                            test_case, response_text, response_time
                        )
                    else:
                        result = self.grader.grade(
                            test_case, response_text, response_time,
                            message_id=response_message.message_id
                        )
                else:
                    result = self.grader.grade_timeout(test_case, self.config.RESPONSE_TIMEOUT)
            except asyncio.TimeoutError:
                result = self.grader.grade_timeout(test_case, self.config.RESPONSE_TIMEOUT)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running test {test_case.id}: {e}")
            return GradeResult(
                test_case=test_case,
                response=f"[ERROR: {str(e)}]",
                response_time=0,
                passed=False,
                score=0,
                issues=[f"Test execution error: {str(e)}"],
            )
        
        finally:
            if message_id:
                self._pending_tests.pop(message_id, None)
                self._response_events.pop(message_id, None)
                self._responses.pop(message_id, None)
    
    async def _run_via_api(self, test_case: TestCase, sent_time: float) -> GradeResult:
        """Call Copilot API directly - Telegram doesn't deliver bot-to-bot messages"""
        import aiohttp
        
        url = f"{self.config.COPILOT_QA_URL.rstrip('/')}/api/qa-query"
        payload = {"question": test_case.question}
        headers = {"Content-Type": "application/json"}
        if self.config.QA_API_SECRET:
            payload["api_key"] = self.config.QA_API_SECRET
            headers["X-Api-Key"] = self.config.QA_API_SECRET
        
        try:
            logger.info(f"Calling Copilot API: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=self.config.RESPONSE_TIMEOUT)) as resp:
                    response_time = time.time() - sent_time
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(f"API returned {resp.status}: {text[:200]}")
                        return GradeResult(
                            test_case=test_case,
                            response=f"[API {resp.status}]: {text[:500]}",
                            response_time=response_time,
                            passed=False,
                            score=0,
                            issues=[f"API returned {resp.status}"],
                        )
                    data = await resp.json()
                    answer = data.get("answer", "")
                    if not answer:
                        return GradeResult(
                            test_case=test_case,
                            response="[API: empty answer]",
                            response_time=response_time,
                            passed=False,
                            score=0,
                            issues=["API returned empty answer"],
                        )
                    return self.grader.grade(test_case, answer, response_time)
        except asyncio.TimeoutError:
            return self.grader.grade_timeout(test_case, self.config.RESPONSE_TIMEOUT)
        except Exception as e:
            response_time = time.time() - sent_time
            logger.error(f"API call failed for {test_case.id}: {e}", exc_info=True)
            return GradeResult(
                test_case=test_case,
                response=f"[API ERROR: {str(e)}]",
                response_time=response_time,
                passed=False,
                score=0,
                issues=[f"API call failed: {str(e)}"],
            )
    
    async def _report_failure(self, result: GradeResult) -> None:
        """Report a test failure"""
        try:
            # Save detailed report
            report_path = self.report_manager.save_report(result)
            logger.info(f"Saved failure report: {report_path}")
            
            # Send Telegram alert
            alert = self.reporter.format_failure_alert(result, report_path)
            await self.bot.send_message(
                chat_id=self.config.QA_TEST_GROUP_ID,
                text=alert,
            )
            
        except Exception as e:
            logger.error(f"Error reporting failure: {e}")
    
    def _generate_summary(self, results: list[GradeResult]) -> DailySummary:
        """Generate daily summary from results"""
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        
        # Calculate category stats
        category_stats = {}
        for result in results:
            cat = result.test_case.category
            if cat not in category_stats:
                category_stats[cat] = {"passed": 0, "total": 0}
            
            category_stats[cat]["total"] += 1
            if result.passed:
                category_stats[cat]["passed"] += 1
        
        for cat in category_stats:
            stats = category_stats[cat]
            stats["pass_rate"] = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        
        avg_time = sum(r.response_time for r in results) / len(results) if results else 0
        
        return DailySummary(
            date=datetime.now().strftime("%Y-%m-%d"),
            tests_run=len(results),
            tests_passed=len(passed),
            tests_failed=len(failed),
            pass_rate=len(passed) / len(results) if results else 0,
            avg_response_time=avg_time,
            failed_tests=failed,
            category_stats=category_stats,
        )
    
    async def _send_summary(self, summary: DailySummary) -> None:
        """Send daily summary to group"""
        try:
            # Save summary report
            report_path = self.report_manager.save_daily_summary(summary)
            logger.info(f"Saved daily summary: {report_path}")
            
            # Send to group
            msg = self.reporter.format_daily_summary(summary)
            await self.bot.send_message(
                chat_id=self.config.QA_TEST_GROUP_ID,
                text=msg,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
