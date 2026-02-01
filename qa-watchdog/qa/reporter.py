"""
Error Reporter

Generates human-readable alerts for Telegram and detailed markdown reports for Cursor debugging.
"""
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .grader import GradeResult


@dataclass
class DailySummary:
    """Daily QA summary"""
    date: str
    tests_run: int
    tests_passed: int
    tests_failed: int
    pass_rate: float
    avg_response_time: float
    failed_tests: list[GradeResult]
    category_stats: dict[str, dict]


class Reporter:
    """Formats alerts for Telegram"""
    
    def __init__(self, admin_username: str):
        self.admin_username = admin_username
    
    def format_failure_alert(self, result: GradeResult, report_path: Optional[Path] = None) -> str:
        """Format a failure alert for Telegram (plain text to avoid parse errors)"""
        q = result.test_case.question[:100] + ('...' if len(result.test_case.question) > 100 else '')
        alert = f"""⚠️ QA Alert: Test Failed

Test: {result.test_case.id}
Question: {q}
Category: {result.test_case.category.title()} ({result.test_case.severity.upper()})
Score: {result.score}/100

Issues:"""
        for issue in result.issues[:3]:
            alert += f"\n• {issue}"
        
        if result.forbidden_found:
            alert += f"\n\nForbidden phrases found: {', '.join(result.forbidden_found)}"
        
        if report_path:
            alert += f"\n\n📄 Full report: {report_path.name}"
        
        alert += f"\n\n@{self.admin_username} please review"
        
        return alert
    
    def format_critical_run_summary(self, results: list[GradeResult]) -> str:
        """Format end-of-run summary for critical tests (plain text)"""
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total = len(results)
        if failed == 0:
            return f"✅ Critical tests complete: {passed}/{total} passed"
        return f"⚠️ Critical tests: {passed} passed, {failed} failed. See failure alerts above."

    def format_timeout_alert(self, result: GradeResult) -> str:
        """Format a timeout alert"""
        return f"""🚨 *QA Alert: Response Timeout*

*Test:* `{result.test_case.id}`
*Question:* _{result.test_case.question[:100]}_
*Timeout:* {result.response_time}s

The copilot did not respond in time. This could indicate:
• Bot is down or unresponsive
• Rate limiting is blocking requests
• Internal error in processing

@{self.admin_username} please check copilot status"""
    
    def format_daily_summary(self, summary: DailySummary) -> str:
        """Format daily summary for Telegram"""
        status_emoji = "✅" if summary.pass_rate >= 0.8 else "⚠️" if summary.pass_rate >= 0.6 else "❌"
        
        msg = f"""{status_emoji} *QA Daily Summary - {summary.date}*

*Overview:*
• Tests Run: {summary.tests_run}
• Passed: {summary.tests_passed} ({summary.pass_rate*100:.0f}%)
• Failed: {summary.tests_failed}
• Avg Response Time: {summary.avg_response_time:.1f}s

"""
        
        if summary.failed_tests:
            msg += "*Failed Tests:*\n"
            for result in summary.failed_tests[:5]:  # Max 5 in summary
                msg += f"• `{result.test_case.id}` ({result.test_case.category}) - {result.score}/100\n"
            
            if len(summary.failed_tests) > 5:
                msg += f"  _...and {len(summary.failed_tests) - 5} more_\n"
        
        msg += "\n*Category Breakdown:*\n"
        for category, stats in summary.category_stats.items():
            emoji = "✅" if stats["pass_rate"] >= 0.8 else "⚠️" if stats["pass_rate"] >= 0.6 else "❌"
            msg += f"{emoji} {category.title()}: {stats['passed']}/{stats['total']} ({stats['pass_rate']*100:.0f}%)\n"
        
        if summary.pass_rate < 0.8:
            msg += f"\n@{self.admin_username} ^"
        
        return msg


class ReportManager:
    """Manages detailed markdown reports for Cursor debugging"""
    
    def __init__(self, reports_dir: str = "qa-watchdog/reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def save_report(self, result: GradeResult) -> Path:
        """Save a detailed failure report as markdown"""
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_{result.test_case.id}.md"
        path = self.reports_dir / filename
        path.write_text(self._format_detailed_report(result))
        return path
    
    def _format_detailed_report(self, result: GradeResult) -> str:
        """Format a detailed markdown report for Cursor"""
        status = "PASSED" if result.passed else "FAILED"
        
        # Keyword check table
        keyword_table = "| Keyword | Expected | Found |\n|---------|----------|-------|\n"
        for kw in result.test_case.expected_keywords:
            found = "✅ Yes" if kw in result.keywords_found else "❌ No"
            keyword_table += f"| {kw} | Yes | {found} |\n"
        
        for kw in result.forbidden_found:
            keyword_table += f"| {kw} | No | ⚠️ VIOLATION |\n"
        
        # Gemini analysis JSON
        gemini_json = json.dumps({
            "accuracy": result.accuracy_score,
            "mudrex_specific": result.mudrex_specific,
            "code_quality": result.code_quality,
            "hallucination_risk": result.hallucination_risk,
            "issues": result.issues,
            "suggestions": result.suggestions,
        }, indent=2)
        
        report = f"""# QA Test Failure Report

**Test ID:** {result.test_case.id}
**Timestamp:** {result.graded_at.isoformat()}Z
**Category:** {result.test_case.category.title()}
**Severity:** {result.test_case.severity.upper()}
**Score:** {result.score}/100
**Status:** {status}

---

## Test Case

**Question:**
> {result.test_case.question}

**Expected Keywords:** `{result.test_case.expected_keywords}`
**Forbidden Keywords:** `{result.test_case.forbidden_keywords}`

---

## Copilot Response

```
{result.response}
```

**Response Time:** {result.response_time:.1f}s
**Message ID:** {result.message_id or 'N/A'}

---

## Grading Analysis

### Keyword Check

{keyword_table}

### Gemini Analysis

```json
{gemini_json}
```

---

## Debug Information

### Relevant Files to Check

Based on the test category `{result.test_case.category}`, check these files:

"""
        
        # Add category-specific file suggestions
        file_suggestions = self._get_file_suggestions(result.test_case.category, result.issues)
        for suggestion in file_suggestions:
            report += f"- `{suggestion}`\n"
        
        report += f"""
### Suggested Cursor Commands

```bash
# Search for related code
rg "{result.test_case.category}" src/

# Check validation logic
rg "validate_document_relevancy" src/

# Verify vector store
python scripts/verify_rag.py

# Check recent logs (if available)
# tail -f logs/copilot.log | grep -i error
```

---

## Action Items

"""
        # Generate action items based on issues
        action_items = self._generate_action_items(result)
        for i, item in enumerate(action_items, 1):
            report += f"{i}. [ ] {item}\n"
        
        report += f"""
---

*Generated by QA Watchdog Bot v1.0.0 at {result.graded_at.isoformat()}*
"""
        
        return report
    
    def _get_file_suggestions(self, category: str, issues: list[str]) -> list[str]:
        """Get relevant file paths based on category and issues"""
        suggestions = []
        
        # Common files
        suggestions.append("src/rag/pipeline.py")
        suggestions.append("src/rag/gemini_client.py")
        
        # Category-specific
        if category == "error_codes":
            suggestions.extend([
                "src/rag/pipeline.py - _looks_like_error_log()",
                "docs/legacy/error-codes.md",
                "docs/training_materials/error-codes.md",
            ])
        elif category == "authentication":
            suggestions.extend([
                "docs/training_materials/authentication-rate-limits.md",
                "src/rag/query_planner.py",
            ])
        elif category in ["orders", "positions"]:
            suggestions.extend([
                "docs/training_materials/orders.md",
                "docs/training_materials/positions.md",
            ])
        
        # Issue-specific
        issues_str = " ".join(issues).lower()
        if "validation" in issues_str or "rejected" in issues_str:
            suggestions.append("src/rag/gemini_client.py - validate_document_relevancy()")
        if "cache" in issues_str:
            suggestions.append("src/rag/semantic_cache.py")
            suggestions.append("src/rag/cache.py")
        if "general pattern" in issues_str or "generic" in issues_str:
            suggestions.append("src/rag/gemini_client.py - SYSTEM_INSTRUCTION")
        
        return list(dict.fromkeys(suggestions))  # Remove duplicates, preserve order
    
    def _generate_action_items(self, result: GradeResult) -> list[str]:
        """Generate action items based on the failure"""
        items = []
        
        # Based on issues
        issues_str = " ".join(result.issues).lower()
        
        if result.forbidden_found:
            items.append(f"Review system instruction for hedging language (found: {result.forbidden_found})")
        
        if "validation" in issues_str:
            items.append("Check if documents are being rejected by validation step")
        
        if "cache" in issues_str:
            items.append("Clear semantic cache and retest: /clearcache")
        
        if "timeout" in issues_str:
            items.append("Check copilot health endpoint and logs")
        
        if result.test_case.category == "error_codes":
            items.append("Verify error-codes.md is being retrieved (check similarity score)")
            items.append("Confirm _looks_like_error_log() regex matches this query")
            items.append("Check if error docs are excluded from legacy flag")
        
        if not result.mudrex_specific:
            items.append("Review why response is generic instead of Mudrex-specific")
            items.append("Check document retrieval scores in logs")
        
        if result.accuracy_score < 0.5:
            items.append("Review RAG retrieval - correct documents may not be indexed")
        
        # Always include
        items.append("Review copilot logs for this timestamp")
        items.append("Retest after fixes to confirm resolution")
        
        return items
    
    def save_daily_summary(self, summary: DailySummary) -> Path:
        """Save daily summary as markdown"""
        filename = f"{summary.date}_daily_summary.md"
        path = self.reports_dir / filename
        
        report = f"""# QA Daily Summary - {summary.date}

## Overview

| Metric | Value |
|--------|-------|
| Tests Run | {summary.tests_run} |
| Passed | {summary.tests_passed} ({summary.pass_rate*100:.0f}%) |
| Failed | {summary.tests_failed} |
| Avg Response Time | {summary.avg_response_time:.1f}s |

## Category Breakdown

| Category | Passed | Total | Pass Rate |
|----------|--------|-------|-----------|
"""
        
        for category, stats in summary.category_stats.items():
            report += f"| {category.title()} | {stats['passed']} | {stats['total']} | {stats['pass_rate']*100:.0f}% |\n"
        
        if summary.failed_tests:
            report += """
## Failed Tests

| Test ID | Category | Score | Primary Issue |
|---------|----------|-------|---------------|
"""
            for result in summary.failed_tests:
                primary_issue = result.issues[0] if result.issues else "Unknown"
                primary_issue = primary_issue[:50] + "..." if len(primary_issue) > 50 else primary_issue
                report += f"| {result.test_case.id} | {result.test_case.category} | {result.score} | {primary_issue} |\n"
        
        report += f"""
## Recommendations

"""
        # Generate recommendations based on patterns
        recommendations = self._generate_recommendations(summary)
        for rec in recommendations:
            report += f"- {rec}\n"
        
        report += f"""
---

*Full reports for each failed test are in this directory.*
*Generated at {datetime.utcnow().isoformat()}*
"""
        
        path.write_text(report)
        return path
    
    def _generate_recommendations(self, summary: DailySummary) -> list[str]:
        """Generate recommendations based on summary patterns"""
        recs = []
        
        # Check category patterns
        for category, stats in summary.category_stats.items():
            if stats["pass_rate"] < 0.5:
                recs.append(f"Critical: {category.title()} tests failing frequently - review {category} implementation")
        
        # Check common issues across failures
        all_issues = []
        for result in summary.failed_tests:
            all_issues.extend(result.issues)
        
        issues_str = " ".join(all_issues).lower()
        
        if issues_str.count("forbidden") > 2:
            recs.append("Multiple tests found forbidden phrases - review system instruction")
        
        if issues_str.count("timeout") > 1:
            recs.append("Multiple timeouts detected - check copilot performance/health")
        
        if issues_str.count("generic") > 2 or issues_str.count("mudrex") > 2:
            recs.append("Responses are too generic - review RAG retrieval and validation")
        
        if summary.avg_response_time > 10:
            recs.append(f"Average response time is slow ({summary.avg_response_time:.1f}s) - optimize pipeline")
        
        if not recs:
            if summary.pass_rate >= 0.9:
                recs.append("Excellent pass rate! Consider adding more edge case tests.")
            else:
                recs.append("Review failed test reports for specific issues.")
        
        return recs
    
    def get_recent_failures(self, days: int = 7) -> list[Path]:
        """Get failure reports from last N days"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        reports = []
        
        for path in self.reports_dir.glob("*.md"):
            if path.name.endswith("_daily_summary.md"):
                continue
            
            try:
                # Parse date from filename
                date_str = path.name.split("_")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date >= cutoff:
                    reports.append(path)
            except Exception:
                continue
        
        return sorted(reports, reverse=True)
