"""
Unit tests for structured troubleshooting tools and query planner known-error detection
"""
import pytest
from unittest.mock import patch, MagicMock

from src.rag.tools.troubleshooting import (
    troubleshoot_500_error,
    troubleshoot_pnl_discrepancy,
    troubleshoot_auth_error,
    troubleshoot_rate_limit,
    troubleshoot_order_error,
    troubleshoot_http_202,
    troubleshoot_http_405,
    TROUBLESHOOTING_TOOLS,
)
from src.rag.query_planner import QueryPlanner, QueryType


# ==================== Tool Function Tests ====================

class TestTroubleshootingTools:
    """Verify each tool returns deterministic, non-empty content with key details."""

    @pytest.mark.unit
    def test_500_error_mentions_sl_tp(self):
        result = troubleshoot_500_error("getting 500 when placing SL")
        assert "500" in result
        assert "SL" in result or "slTriggerPrice" in result
        assert "riskorder" in result

    @pytest.mark.unit
    def test_500_error_mentions_precision(self):
        result = troubleshoot_500_error("500 internal server error")
        assert "Precision" in result or "precision" in result
        assert "tickSize" in result

    @pytest.mark.unit
    def test_pnl_discrepancy_mentions_funding(self):
        result = troubleshoot_pnl_discrepancy("pnl mismatch")
        assert "Funding" in result or "funding" in result

    @pytest.mark.unit
    def test_pnl_discrepancy_mentions_fees(self):
        result = troubleshoot_pnl_discrepancy("pnl is wrong")
        assert "fee" in result.lower()

    @pytest.mark.unit
    def test_auth_error_mentions_header(self):
        result = troubleshoot_auth_error("401 auth fail")
        assert "X-Authentication" in result

    @pytest.mark.unit
    def test_auth_error_no_hmac(self):
        result = troubleshoot_auth_error("403 forbidden")
        assert "HMAC" in result or "signing" in result.lower()

    @pytest.mark.unit
    def test_rate_limit_mentions_limit(self):
        result = troubleshoot_rate_limit("429 too many requests")
        assert "2 requests per second" in result

    @pytest.mark.unit
    def test_rate_limit_mentions_backoff(self):
        result = troubleshoot_rate_limit("rate limited")
        assert "backoff" in result.lower() or "Backoff" in result

    @pytest.mark.unit
    def test_order_error_mentions_precision(self):
        result = troubleshoot_order_error("-1111 precision")
        assert "stepSize" in result or "tickSize" in result

    @pytest.mark.unit
    def test_order_error_mentions_symbol_format(self):
        result = troubleshoot_order_error("-1121 invalid symbol")
        assert "BTCUSDT" in result

    @pytest.mark.unit
    def test_tools_list_has_all_seven(self):
        assert len(TROUBLESHOOTING_TOOLS) == 7
        names = {fn.__name__ for fn in TROUBLESHOOTING_TOOLS}
        assert names == {
            "troubleshoot_500_error",
            "troubleshoot_pnl_discrepancy",
            "troubleshoot_auth_error",
            "troubleshoot_rate_limit",
            "troubleshoot_order_error",
            "troubleshoot_http_202",
            "troubleshoot_http_405",
        }

    @pytest.mark.unit
    def test_http_202_explains_success(self):
        result = troubleshoot_http_202("failed: 202")
        assert "SUCCESS" in result or "success" in result
        assert "202" in result
        assert "Accepted" in result or "accepted" in result

    @pytest.mark.unit
    def test_http_202_mentions_fix(self):
        result = troubleshoot_http_202("error 202")
        assert "response.ok" in result or "200, 201, 202" in result

    @pytest.mark.unit
    def test_http_405_mentions_post(self):
        result = troubleshoot_http_405("405 method not allowed")
        assert "POST" in result
        assert "asset" in result.lower() or "ETHUSDT" in result

    @pytest.mark.unit
    def test_all_tools_have_docstrings(self):
        for fn in TROUBLESHOOTING_TOOLS:
            assert fn.__doc__, f"{fn.__name__} is missing a docstring"


# ==================== Query Planner Known-Error Detection ====================

class TestQueryPlannerKnownErrors:
    """Verify _is_known_error pattern matching and plan() routing."""

    @pytest.fixture
    def planner(self):
        return QueryPlanner()

    # --- Pattern matching ---

    @pytest.mark.unit
    def test_500_sl_detected(self, planner):
        assert planner._is_known_error("getting 500 error on sl order") == "troubleshoot_500_error"

    @pytest.mark.unit
    def test_500_tp_detected(self, planner):
        assert planner._is_known_error("500 when setting tp") == "troubleshoot_500_error"

    @pytest.mark.unit
    def test_500_stop_loss_detected(self, planner):
        assert planner._is_known_error("500 stop loss issue") == "troubleshoot_500_error"

    @pytest.mark.unit
    def test_500_internal_detected(self, planner):
        assert planner._is_known_error("500 internal server error on order") == "troubleshoot_500_error"

    @pytest.mark.unit
    def test_pnl_discrepancy_detected(self, planner):
        assert planner._is_known_error("pnl discrepancy on btcusdt") == "troubleshoot_pnl_discrepancy"

    @pytest.mark.unit
    def test_pnl_mismatch_detected(self, planner):
        assert planner._is_known_error("p&l mismatch between ui and api") == "troubleshoot_pnl_discrepancy"

    @pytest.mark.unit
    def test_pnl_wrong_detected(self, planner):
        assert planner._is_known_error("my pnl is wrong") == "troubleshoot_pnl_discrepancy"

    @pytest.mark.unit
    def test_401_detected(self, planner):
        assert planner._is_known_error("getting 401 unauthorized") == "troubleshoot_auth_error"

    @pytest.mark.unit
    def test_403_detected(self, planner):
        assert planner._is_known_error("403 forbidden error") == "troubleshoot_auth_error"

    @pytest.mark.unit
    def test_auth_fail_detected(self, planner):
        assert planner._is_known_error("authentication failed on request") == "troubleshoot_auth_error"

    @pytest.mark.unit
    def test_429_detected(self, planner):
        assert planner._is_known_error("429 too many requests") == "troubleshoot_rate_limit"

    @pytest.mark.unit
    def test_rate_limit_detected(self, planner):
        assert planner._is_known_error("hitting the rate limit") == "troubleshoot_rate_limit"

    @pytest.mark.unit
    def test_minus_1111_detected(self, planner):
        assert planner._is_known_error("error -1111 on order") == "troubleshoot_order_error"

    @pytest.mark.unit
    def test_minus_1121_detected(self, planner):
        assert planner._is_known_error("error -1121 invalid symbol") == "troubleshoot_order_error"

    @pytest.mark.unit
    def test_step_size_error_detected(self, planner):
        assert planner._is_known_error("step size error on quantity") == "troubleshoot_order_error"

    @pytest.mark.unit
    def test_202_failed_detected(self, planner):
        assert planner._is_known_error("❌ failed: 202") == "troubleshoot_http_202"

    @pytest.mark.unit
    def test_202_error_detected(self, planner):
        assert planner._is_known_error("error 202 what is this") == "troubleshoot_http_202"

    @pytest.mark.unit
    def test_405_detected(self, planner):
        assert planner._is_known_error("getting 405 method not allowed") == "troubleshoot_http_405"

    @pytest.mark.unit
    def test_generic_error_not_detected(self, planner):
        """Generic error queries should NOT match known-error patterns."""
        assert planner._is_known_error("something is not working") is None

    @pytest.mark.unit
    def test_greeting_not_detected(self, planner):
        assert planner._is_known_error("hello") is None

    # --- plan() routing ---

    @pytest.mark.unit
    def test_plan_routes_known_error(self, planner):
        plan = planner.plan("getting 500 error on SL order")
        assert plan.query_type == QueryType.KNOWN_ERROR
        assert plan.use_tool_calling is True
        assert plan.skip_retrieval is True
        assert plan.skip_validation is True
        assert plan.skip_rerank is True
        assert plan.tool_hint == "troubleshoot_500_error"

    @pytest.mark.unit
    def test_plan_routes_generic_error_to_error_debug(self, planner):
        """Errors that don't match a known pattern should fall through to ERROR_DEBUG."""
        plan = planner.plan("my bot is broken and shows an error")
        assert plan.query_type == QueryType.ERROR_DEBUG

    @pytest.mark.unit
    def test_plan_greeting_unchanged(self, planner):
        plan = planner.plan("hello!")
        assert plan.query_type == QueryType.GREETING
        assert plan.use_tool_calling is False

    @pytest.mark.unit
    def test_plan_routes_202_to_tool_calling(self, planner):
        plan = planner.plan('❌ FAILED: 202\nError Details: {"success":true,"data":{"leverage":"1"}}')
        assert plan.query_type == QueryType.KNOWN_ERROR
        assert plan.use_tool_calling is True
        assert plan.tool_hint == "troubleshoot_http_202"


# ==================== Bot-Architecture False Positive Tests ====================

class TestBotArchitectureFalsePositive:
    """Ensure pasted error logs with 'leverage' don't trigger bot-architecture reply."""

    @pytest.fixture
    def pipeline(self):
        """Create a minimal pipeline to test _get_bot_architecture_reply."""
        from unittest.mock import MagicMock
        from src.rag.pipeline import RAGPipeline
        with patch.object(RAGPipeline, '__init__', lambda self: None):
            p = RAGPipeline.__new__(RAGPipeline)
            return p

    @pytest.mark.unit
    def test_leverage_json_not_detected_as_bot_arch(self, pipeline):
        """'leverage' in JSON should NOT trigger bot-architecture reply (rag substring)."""
        msg = (
            'I am getting this errror\n'
            '📡 Executing: OPEN LONG | Qty: 0.010 ETH\n'
            '❌ FAILED: 202\n'
            'Error Details: {"success":true,"data":{"leverage":"1","amount":"20.1087"}}'
        )
        assert pipeline._get_bot_architecture_reply(msg) is None

    @pytest.mark.unit
    def test_actual_rag_question_still_detected(self, pipeline):
        """Genuine 'rag' question should still be detected."""
        assert pipeline._get_bot_architecture_reply("how does your rag pipeline work") is not None

    @pytest.mark.unit
    def test_error_with_http_code_not_detected(self, pipeline):
        """Messages with HTTP status codes should not be bot-architecture."""
        assert pipeline._get_bot_architecture_reply("getting error 500 on my order") is None

    @pytest.mark.unit
    def test_check_this_not_detected(self, pipeline):
        """'Can u check this' should not be bot-architecture."""
        assert pipeline._get_bot_architecture_reply("Can u check this") is None
