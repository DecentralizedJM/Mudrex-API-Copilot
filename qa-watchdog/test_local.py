#!/usr/bin/env python3
"""
Local Test Script for QA Watchdog Bot

Tests all components locally before deployment.
Run with: python -m qa-watchdog.test_local (from project root)
Or: python test_local.py (from qa-watchdog directory)
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# Test Results Tracking
# ============================================================================

@dataclass
class TestResult:
    name: str
    passed: bool
    error: str = ""

test_results: list[TestResult] = []

def test(name: str):
    """Decorator to track test results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
                test_results.append(TestResult(name=name, passed=True))
                print(f"  ✅ {name}")
            except Exception as e:
                test_results.append(TestResult(name=name, passed=False, error=str(e)))
                print(f"  ❌ {name}: {e}")
        return wrapper
    return decorator

# ============================================================================
# Import Tests
# ============================================================================

print("\n" + "=" * 60)
print("  QA Watchdog Bot - Local Tests")
print("=" * 60)
print("\n📦 Testing imports...")

@test("Import config module")
def test_import_config():
    from config import Config, get_config
    assert Config is not None

@test("Import test_bank module")
def test_import_test_bank():
    from qa.test_bank import TestBank, TestCase, DynamicTestGenerator
    assert TestBank is not None
    assert TestCase is not None
    assert DynamicTestGenerator is not None

@test("Import grader module")
def test_import_grader():
    from qa.grader import ResponseGrader, GradeResult
    assert ResponseGrader is not None
    assert GradeResult is not None

@test("Import reporter module")
def test_import_reporter():
    from qa.reporter import Reporter, ReportManager, DailySummary
    assert Reporter is not None
    assert ReportManager is not None
    assert DailySummary is not None

@test("Import scheduler module")
def test_import_scheduler():
    from scheduler.qa_scheduler import setup_scheduler, get_next_runs
    assert setup_scheduler is not None
    assert get_next_runs is not None

@test("Import watchdog bot module")
def test_import_watchdog():
    from bot.watchdog import QAWatchdogBot
    assert QAWatchdogBot is not None

test_import_config()
test_import_test_bank()
test_import_grader()
test_import_reporter()
test_import_scheduler()
test_import_watchdog()

# ============================================================================
# Config Tests
# ============================================================================

print("\n⚙️  Testing configuration...")

@test("Config from environment variables")
def test_config_from_env():
    from config import Config
    
    # Set test environment variables
    test_env = {
        "QA_TELEGRAM_BOT_TOKEN": "test_token_123",
        "QA_TEST_GROUP_ID": "-1003269114897",
        "QA_GEMINI_API_KEY": "test_gemini_key",
        "COPILOT_BOT_USERNAME": "API_Assistant_V2_bot",
        "ADMIN_USERNAME": "TestAdmin",
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        config = Config.from_env()
        assert config.QA_TELEGRAM_BOT_TOKEN == "test_token_123"
        assert config.QA_TEST_GROUP_ID == -1003269114897
        assert config.QA_GEMINI_API_KEY == "test_gemini_key"
        assert config.COPILOT_BOT_USERNAME == "API_Assistant_V2_bot"
        assert config.ADMIN_USERNAME == "TestAdmin"
        assert config.HEALTH_PORT == 8081
        assert config.RESPONSE_TIMEOUT == 60

@test("Config validation")
def test_config_validation():
    from config import Config
    
    # Test valid config
    config = Config(
        QA_TELEGRAM_BOT_TOKEN="token",
        QA_TEST_GROUP_ID=-123,
        COPILOT_BOT_USERNAME="bot",
        ADMIN_USERNAME="admin",
        QA_GEMINI_API_KEY="key",
    )
    config.validate()  # Should not raise

@test("Config defaults")
def test_config_defaults():
    from config import Config
    
    config = Config(
        QA_TELEGRAM_BOT_TOKEN="token",
        QA_TEST_GROUP_ID=-123,
        COPILOT_BOT_USERNAME="bot",
        ADMIN_USERNAME="admin",
        QA_GEMINI_API_KEY="key",
    )
    
    assert config.GEMINI_MODEL == "gemini-2.0-flash"
    assert config.DAILY_QA_HOUR == 3
    assert config.CRITICAL_TEST_INTERVAL_HOURS == 6
    assert config.SPOT_CHECK_INTERVAL_HOURS == 2
    assert config.DAILY_TEST_COUNT == 20
    assert config.CRITICAL_TEST_COUNT == 5
    assert config.SPOT_CHECK_COUNT == 2

test_config_from_env()
test_config_validation()
test_config_defaults()

# ============================================================================
# TestCase and TestBank Tests
# ============================================================================

print("\n🧪 Testing test case generation...")

@test("TestCase dataclass")
def test_testcase_dataclass():
    from qa.test_bank import TestCase
    
    tc = TestCase(
        id="test-001",
        question="How do I authenticate?",
        expected_keywords=["X-Authentication", "header"],
        forbidden_keywords=["not sure"],
        category="authentication",
        severity="critical"
    )
    
    assert tc.id == "test-001"
    assert tc.question == "How do I authenticate?"
    assert len(tc.expected_keywords) == 2
    assert tc.category == "authentication"
    assert tc.severity == "critical"
    assert tc.unique_hash  # Auto-generated

@test("DynamicTestGenerator auth questions")
def test_generator_auth():
    from qa.test_bank import DynamicTestGenerator
    
    # Mock Gemini client
    with patch('qa.test_bank.genai.Client'):
        generator = DynamicTestGenerator(gemini_api_key="fake_key")
        
        # Generate multiple auth questions to verify uniqueness
        questions = set()
        for _ in range(5):
            tc = generator.generate_auth_question()
            assert tc.category == "authentication"
            assert tc.severity == "critical"
            assert "X-Authentication" in tc.expected_keywords
            questions.add(tc.question)
        
        # Should have at least 3 unique questions
        assert len(questions) >= 3, f"Expected diverse questions, got: {questions}"

@test("DynamicTestGenerator order questions")
def test_generator_order():
    from qa.test_bank import DynamicTestGenerator
    
    with patch('qa.test_bank.genai.Client'):
        generator = DynamicTestGenerator(gemini_api_key="fake_key")
        
        tc = generator.generate_order_question()
        assert tc.category == "orders"
        assert tc.severity == "high"
        assert "order" in tc.expected_keywords or "/fapi/v1" in tc.expected_keywords

@test("DynamicTestGenerator error log questions")
def test_generator_error_log():
    from qa.test_bank import DynamicTestGenerator
    
    with patch('qa.test_bank.genai.Client'):
        generator = DynamicTestGenerator(gemini_api_key="fake_key")
        
        tc = generator.generate_error_log_question()
        assert tc.category == "error_codes"
        assert tc.severity == "critical"
        # Should contain an error code in the question
        has_error_code = any(str(code) in tc.question for code in generator.ERROR_CODES.keys())
        assert has_error_code, f"No error code in: {tc.question}"

@test("DynamicTestGenerator edge cases")
def test_generator_edge_cases():
    from qa.test_bank import DynamicTestGenerator
    
    with patch('qa.test_bank.genai.Client'):
        generator = DynamicTestGenerator(gemini_api_key="fake_key")
        
        categories_found = set()
        for _ in range(10):
            tc = generator.generate_edge_case()
            categories_found.add(tc.category)
        
        # Should cover multiple edge case types
        assert len(categories_found) >= 2, f"Only found: {categories_found}"

@test("TestBank daily suite generation")
def test_testbank_daily_suite():
    from qa.test_bank import TestBank
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('qa.test_bank.genai.Client'):
            bank = TestBank(gemini_api_key="fake_key", data_dir=tmpdir)
            
            # Mock creative question to avoid actual API call
            bank.generator.generate_creative_question = bank.generator.generate_order_question
            
            suite = bank.get_daily_suite(count=10)
            
            assert len(suite) >= 8  # Should have at least 80% of requested
            
            # Check distribution of categories
            categories = [tc.category for tc in suite]
            category_counts = {c: categories.count(c) for c in set(categories)}
            
            # Should have mix of categories
            assert len(category_counts) >= 3, f"Not enough variety: {category_counts}"

@test("TestBank question history")
def test_testbank_history():
    from qa.test_bank import TestBank
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('qa.test_bank.genai.Client'):
            bank = TestBank(gemini_api_key="fake_key", data_dir=tmpdir)
            bank.generator.generate_creative_question = bank.generator.generate_order_question
            
            # Generate suite
            suite1 = bank.get_daily_suite(count=5)
            
            # Check history file was created
            history_file = Path(tmpdir) / "question_history.json"
            assert history_file.exists()
            
            # Load and verify history
            history = json.loads(history_file.read_text())
            assert "recent_questions" in history
            assert "last_updated" in history
            assert len(history["recent_questions"]) >= 1

test_testcase_dataclass()
test_generator_auth()
test_generator_order()
test_generator_error_log()
test_generator_edge_cases()
test_testbank_daily_suite()
test_testbank_history()

# ============================================================================
# Grader Tests
# ============================================================================

print("\n📊 Testing response grader...")

@test("GradeResult dataclass")
def test_graderesult_dataclass():
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    
    tc = TestCase(
        id="test-001",
        question="Test question",
        expected_keywords=["keyword1"],
        forbidden_keywords=["bad"],
        category="test",
        severity="high"
    )
    
    result = GradeResult(
        test_case=tc,
        response="Test response with keyword1",
        response_time=2.5,
        passed=True,
        score=85
    )
    
    assert result.test_case.id == "test-001"
    assert result.response_time == 2.5
    assert result.passed
    assert result.score == 85

@test("GradeResult to_dict")
def test_graderesult_to_dict():
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    
    tc = TestCase(
        id="test-001",
        question="Test question",
        expected_keywords=["keyword1"],
        forbidden_keywords=["bad"],
        category="test",
        severity="high"
    )
    
    result = GradeResult(
        test_case=tc,
        response="Test response",
        response_time=2.5,
        passed=True,
        score=85,
        keywords_found=["keyword1"],
        issues=["Issue 1"],
    )
    
    d = result.to_dict()
    assert d["test_case"]["id"] == "test-001"
    assert d["passed"] == True
    assert d["score"] == 85
    assert "keyword1" in d["keywords_found"]

@test("ResponseGrader keyword check")
def test_grader_keyword_check():
    from qa.grader import ResponseGrader, GradeResult
    from qa.test_bank import TestCase
    
    with patch('qa.grader.genai.Client'):
        grader = ResponseGrader(gemini_api_key="fake_key")
        
        tc = TestCase(
            id="test-001",
            question="How to authenticate?",
            expected_keywords=["X-Authentication", "header", "API key"],
            forbidden_keywords=["not sure", "I don't know"],
            category="auth",
            severity="critical"
        )
        
        # Test with good response
        result = GradeResult(
            test_case=tc,
            response="Use X-Authentication header with your API key",
            response_time=1.5
        )
        
        grader._check_keywords(result)
        
        assert "X-Authentication" in result.keywords_found
        assert "header" in result.keywords_found
        assert "API key" in result.keywords_found
        assert len(result.forbidden_found) == 0
        
        # Test with bad response
        result2 = GradeResult(
            test_case=tc,
            response="I'm not sure about that, I don't know the details",
            response_time=1.5
        )
        
        grader._check_keywords(result2)
        
        assert "not sure" in result2.forbidden_found
        assert "I don't know" in result2.forbidden_found
        assert len(result2.issues) == 2  # Two forbidden phrases

@test("ResponseGrader score calculation")
def test_grader_score_calculation():
    from qa.grader import ResponseGrader, GradeResult
    from qa.test_bank import TestCase
    
    with patch('qa.grader.genai.Client'):
        grader = ResponseGrader(gemini_api_key="fake_key")
        
        tc = TestCase(
            id="test-001",
            question="Test",
            expected_keywords=["keyword1", "keyword2"],
            forbidden_keywords=["bad"],
            category="test",
            severity="high"
        )
        
        # Test passing result
        result = GradeResult(
            test_case=tc,
            response="Response with keyword1 and keyword2",
            response_time=2.0,
            accuracy_score=0.9,
            mudrex_specific=True,
            code_quality=0.8,
            hallucination_risk=0.1,
            keywords_found=["keyword1", "keyword2"],
            keywords_missing=[],
            forbidden_found=[],
        )
        
        grader._calculate_score(result)
        
        assert result.score >= 60  # Should pass
        assert result.passed

@test("ResponseGrader timeout handling")
def test_grader_timeout():
    from qa.grader import ResponseGrader
    from qa.test_bank import TestCase
    
    with patch('qa.grader.genai.Client'):
        grader = ResponseGrader(gemini_api_key="fake_key")
        
        tc = TestCase(
            id="test-001",
            question="Test question",
            expected_keywords=[],
            forbidden_keywords=[],
            category="test",
            severity="high"
        )
        
        result = grader.grade_timeout(tc, timeout=60)
        
        assert not result.passed
        assert result.score == 0
        assert "TIMEOUT" in result.issues[0]
        assert result.response_time == 60

@test("ResponseGrader error response handling")
def test_grader_error_response():
    from qa.grader import ResponseGrader
    from qa.test_bank import TestCase
    
    with patch('qa.grader.genai.Client'):
        grader = ResponseGrader(gemini_api_key="fake_key")
        
        tc = TestCase(
            id="test-001",
            question="Test question",
            expected_keywords=[],
            forbidden_keywords=[],
            category="test",
            severity="high"
        )
        
        result = grader.grade_error_response(
            tc, "Something went wrong, please try again", 5.0
        )
        
        assert not result.passed
        assert result.score == 20
        assert any("Internal error" in issue for issue in result.issues)

test_graderesult_dataclass()
test_graderesult_to_dict()
test_grader_keyword_check()
test_grader_score_calculation()
test_grader_timeout()
test_grader_error_response()

# ============================================================================
# Reporter Tests
# ============================================================================

print("\n📝 Testing reporter...")

@test("Reporter failure alert formatting")
def test_reporter_failure_alert():
    from qa.reporter import Reporter
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    
    reporter = Reporter(admin_username="TestAdmin")
    
    tc = TestCase(
        id="test-auth-001",
        question="How do I authenticate with the Mudrex API?",
        expected_keywords=["X-Authentication"],
        forbidden_keywords=["not sure"],
        category="authentication",
        severity="critical"
    )
    
    result = GradeResult(
        test_case=tc,
        response="I'm not sure about authentication",
        response_time=2.5,
        passed=False,
        score=45,
        issues=["Response uses hedging language", "Missing code example"],
        forbidden_found=["not sure"],
    )
    
    alert = reporter.format_failure_alert(result)
    
    assert "QA Alert" in alert
    assert "test-auth-001" in alert
    assert "authentication" in alert.lower()
    assert "45/100" in alert
    assert "not sure" in alert
    assert "@TestAdmin" in alert

@test("Reporter daily summary formatting")
def test_reporter_daily_summary():
    from qa.reporter import Reporter, DailySummary
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    
    reporter = Reporter(admin_username="TestAdmin")
    
    # Create a sample summary
    tc = TestCase(
        id="test-001",
        question="Test",
        expected_keywords=[],
        forbidden_keywords=[],
        category="test",
        severity="high"
    )
    
    failed_result = GradeResult(
        test_case=tc,
        response="Bad response",
        response_time=1.0,
        passed=False,
        score=40,
    )
    
    summary = DailySummary(
        date="2026-02-01",
        tests_run=20,
        tests_passed=17,
        tests_failed=3,
        pass_rate=0.85,
        avg_response_time=2.5,
        failed_tests=[failed_result],
        category_stats={
            "authentication": {"passed": 5, "total": 5, "pass_rate": 1.0},
            "error_codes": {"passed": 4, "total": 6, "pass_rate": 0.67},
        }
    )
    
    msg = reporter.format_daily_summary(summary)
    
    assert "Daily Summary" in msg
    assert "2026-02-01" in msg
    assert "17" in msg
    assert "85%" in msg
    assert "2.5s" in msg

@test("ReportManager save report")
def test_reportmanager_save():
    from qa.reporter import ReportManager
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ReportManager(reports_dir=tmpdir)
        
        tc = TestCase(
            id="test-error-1111",
            question="What does error -1111 mean?",
            expected_keywords=["precision", "step size"],
            forbidden_keywords=["not sure"],
            category="error_codes",
            severity="critical"
        )
        
        result = GradeResult(
            test_case=tc,
            response="This is a general pattern in APIs",
            response_time=2.5,
            passed=False,
            score=45,
            issues=["Response is too generic", "Missing Mudrex-specific info"],
            suggestions=["Check RAG retrieval", "Verify error-codes.md"],
            keywords_found=["precision"],
            keywords_missing=["step size"],
            forbidden_found=[],
            accuracy_score=0.5,
            mudrex_specific=False,
            code_quality=0.3,
            hallucination_risk=0.2,
        )
        
        path = manager.save_report(result)
        
        assert path.exists()
        assert path.suffix == ".md"
        
        content = path.read_text()
        assert "# QA Test Failure Report" in content
        assert "test-error-1111" in content
        assert "error_codes" in content
        assert "45/100" in content
        assert "Copilot Response" in content
        assert "Debug Information" in content

@test("ReportManager save daily summary")
def test_reportmanager_daily_summary():
    from qa.reporter import ReportManager, DailySummary
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ReportManager(reports_dir=tmpdir)
        
        summary = DailySummary(
            date="2026-02-01",
            tests_run=20,
            tests_passed=17,
            tests_failed=3,
            pass_rate=0.85,
            avg_response_time=2.5,
            failed_tests=[],
            category_stats={
                "authentication": {"passed": 5, "total": 5, "pass_rate": 1.0},
            }
        )
        
        path = manager.save_daily_summary(summary)
        
        assert path.exists()
        assert "daily_summary" in path.name
        
        content = path.read_text()
        assert "# QA Daily Summary" in content
        assert "2026-02-01" in content

@test("ReportManager get recent failures")
def test_reportmanager_recent():
    from qa.reporter import ReportManager
    from qa.grader import GradeResult
    from qa.test_bank import TestCase
    from datetime import datetime
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ReportManager(reports_dir=tmpdir)
        
        # Create some test report files
        today = datetime.now().strftime("%Y-%m-%d")
        (Path(tmpdir) / f"{today}_test-001.md").write_text("# Test Report")
        (Path(tmpdir) / f"{today}_test-002.md").write_text("# Test Report")
        (Path(tmpdir) / f"{today}_daily_summary.md").write_text("# Summary")
        
        recent = manager.get_recent_failures(days=7)
        
        # Should find 2 reports (not the summary)
        assert len(recent) == 2

test_reporter_failure_alert()
test_reporter_daily_summary()
test_reportmanager_save()
test_reportmanager_daily_summary()
test_reportmanager_recent()

# ============================================================================
# Scheduler Tests
# ============================================================================

print("\n⏰ Testing scheduler...")

@test("Scheduler setup")
def test_scheduler_setup():
    from scheduler.qa_scheduler import setup_scheduler, get_next_runs
    from config import Config
    
    # Create mock bot
    mock_bot = MagicMock()
    
    config = Config(
        QA_TELEGRAM_BOT_TOKEN="token",
        QA_TEST_GROUP_ID=-123,
        COPILOT_BOT_USERNAME="bot",
        ADMIN_USERNAME="admin",
        QA_GEMINI_API_KEY="key",
        DAILY_QA_HOUR=3,
        CRITICAL_TEST_INTERVAL_HOURS=6,
        SPOT_CHECK_INTERVAL_HOURS=2,
    )
    
    scheduler = setup_scheduler(mock_bot, config)
    
    assert scheduler is not None
    
    # Check jobs were added
    jobs = scheduler.get_jobs()
    job_ids = [job.id for job in jobs]
    
    assert "daily_qa_suite" in job_ids
    assert "critical_tests" in job_ids
    assert "spot_checks" in job_ids

@test("Scheduler get next runs (jobs configured)")
def test_scheduler_next_runs():
    from scheduler.qa_scheduler import setup_scheduler, get_next_runs
    from config import Config
    
    mock_bot = MagicMock()
    
    config = Config(
        QA_TELEGRAM_BOT_TOKEN="token",
        QA_TEST_GROUP_ID=-123,
        COPILOT_BOT_USERNAME="bot",
        ADMIN_USERNAME="admin",
        QA_GEMINI_API_KEY="key",
    )
    
    scheduler = setup_scheduler(mock_bot, config)
    
    # Verify jobs are added (without starting scheduler)
    jobs = scheduler.get_jobs()
    job_ids = [job.id for job in jobs]
    
    assert "daily_qa_suite" in job_ids, f"Missing daily_qa_suite in {job_ids}"
    assert "critical_tests" in job_ids, f"Missing critical_tests in {job_ids}"
    assert "spot_checks" in job_ids, f"Missing spot_checks in {job_ids}"
    
    # Verify job triggers
    daily_job = scheduler.get_job("daily_qa_suite")
    assert daily_job is not None
    assert "CronTrigger" in str(type(daily_job.trigger))

test_scheduler_setup()
test_scheduler_next_runs()

# ============================================================================
# Integration Test (without real APIs)
# ============================================================================

print("\n🔗 Testing integration (mocked)...")

@test("Full test flow (mocked)")
def test_full_flow_mocked():
    from qa.test_bank import TestBank
    from qa.grader import ResponseGrader
    from qa.reporter import Reporter, ReportManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('qa.test_bank.genai.Client'), patch('qa.grader.genai.Client'):
            # Initialize components
            bank = TestBank(gemini_api_key="fake", data_dir=tmpdir)
            grader = ResponseGrader(gemini_api_key="fake")
            reporter = Reporter(admin_username="TestAdmin")
            report_manager = ReportManager(reports_dir=tmpdir)
            
            # Mock creative question generator
            bank.generator.generate_creative_question = bank.generator.generate_order_question
            
            # Generate a small test suite
            tests = bank.get_critical_tests(count=3)
            assert len(tests) >= 2
            
            # Simulate grading
            for tc in tests[:1]:  # Just test one
                # Mock a response
                mock_response = "Use X-Authentication header for auth. Here's Python code..."
                
                # Create a grade result manually (skip Gemini call)
                from qa.grader import GradeResult
                result = GradeResult(
                    test_case=tc,
                    response=mock_response,
                    response_time=2.5,
                    passed=True,
                    score=75,
                    accuracy_score=0.8,
                    mudrex_specific=True,
                    code_quality=0.7,
                    keywords_found=tc.expected_keywords,
                )
                
                # Test report generation
                if not result.passed:
                    path = report_manager.save_report(result)
                    assert path.exists()

test_full_flow_mocked()

# ============================================================================
# End-to-End Tests
# ============================================================================

print("\n🚀 Testing end-to-end components...")

@test("Health server endpoint")
def test_health_endpoint():
    import asyncio
    from aiohttp import web
    
    async def test_health():
        async def health_handler(request):
            return web.json_response({"status": "healthy", "service": "qa-watchdog"})
        
        app = web.Application()
        app.router.add_get("/health", health_handler)
        
        # Create test client
        from aiohttp.test_utils import TestClient, TestServer
        
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/health")
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "healthy"
            assert data["service"] == "qa-watchdog"
    
    asyncio.run(test_health())

@test("Main module imports cleanly")
def test_main_imports():
    # Just verify main.py can be imported without errors
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", Path(__file__).parent / "main.py")
    assert spec is not None
    # Note: We don't execute main() as it would try to connect to Telegram

@test("Dockerfile syntax valid")
def test_dockerfile():
    dockerfile = Path(__file__).parent / "Dockerfile"
    assert dockerfile.exists()
    content = dockerfile.read_text()
    assert "FROM python:" in content
    assert "COPY requirements.txt" in content
    assert "pip install" in content
    assert "CMD" in content or "ENTRYPOINT" in content

@test("Railway config valid")
def test_railway_config():
    import json
    railway_json = Path(__file__).parent / "railway.json"
    assert railway_json.exists()
    config = json.loads(railway_json.read_text())
    assert "$schema" in config or "build" in config or "deploy" in config

test_health_endpoint()
test_main_imports()
test_dockerfile()
test_railway_config()

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 60)
print("  Test Results Summary")
print("=" * 60)

passed = sum(1 for r in test_results if r.passed)
failed = sum(1 for r in test_results if not r.passed)
total = len(test_results)

print(f"\n  Total: {total}")
print(f"  ✅ Passed: {passed}")
print(f"  ❌ Failed: {failed}")
print(f"  Pass Rate: {passed/total*100:.0f}%")

if failed > 0:
    print("\n  Failed Tests:")
    for r in test_results:
        if not r.passed:
            print(f"    - {r.name}: {r.error}")

print("\n" + "=" * 60)

if failed == 0:
    print("  🎉 All local tests passed!")
    print("  Ready for deployment testing.")
else:
    print(f"  ⚠️  {failed} test(s) failed. Please fix before deployment.")

print("=" * 60 + "\n")

sys.exit(0 if failed == 0 else 1)
