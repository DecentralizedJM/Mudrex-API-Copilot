"""
Response Grader

Uses Gemini to evaluate copilot responses like a Senior QA Engineer.
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from google import genai
from google.genai import types

from .test_bank import TestCase


@dataclass
class GradeResult:
    """Result of grading a response"""
    test_case: TestCase
    response: str
    response_time: float  # seconds
    message_id: Optional[int] = None
    
    # Grading results
    passed: bool = False
    score: int = 0  # 0-100
    
    # Keyword analysis
    keywords_found: list[str] = field(default_factory=list)
    keywords_missing: list[str] = field(default_factory=list)
    forbidden_found: list[str] = field(default_factory=list)
    
    # Gemini analysis
    accuracy_score: float = 0.0
    mudrex_specific: bool = False
    code_quality: float = 0.0
    hallucination_risk: float = 0.0
    
    # Issues and suggestions
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    
    # Metadata
    graded_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "test_case": {
                "id": self.test_case.id,
                "question": self.test_case.question,
                "category": self.test_case.category,
                "severity": self.test_case.severity,
                "expected_keywords": self.test_case.expected_keywords,
                "forbidden_keywords": self.test_case.forbidden_keywords,
            },
            "response": self.response,
            "response_time": self.response_time,
            "message_id": self.message_id,
            "passed": self.passed,
            "score": self.score,
            "keywords_found": self.keywords_found,
            "keywords_missing": self.keywords_missing,
            "forbidden_found": self.forbidden_found,
            "accuracy_score": self.accuracy_score,
            "mudrex_specific": self.mudrex_specific,
            "code_quality": self.code_quality,
            "hallucination_risk": self.hallucination_risk,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "graded_at": self.graded_at.isoformat(),
        }


class ResponseGrader:
    """Grades copilot responses using keyword checks and Gemini analysis"""
    
    # Passing threshold
    PASS_THRESHOLD = 60
    
    def __init__(self, gemini_api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=gemini_api_key)
        self.model = model
    
    def grade(
        self,
        test_case: TestCase,
        response: str,
        response_time: float,
        message_id: Optional[int] = None
    ) -> GradeResult:
        """
        Grade a copilot response.
        
        Args:
            test_case: The test case that was run
            response: The copilot's response text
            response_time: Time taken to respond (seconds)
            message_id: Telegram message ID (optional)
        
        Returns:
            GradeResult with pass/fail, score, and detailed analysis
        """
        result = GradeResult(
            test_case=test_case,
            response=response,
            response_time=response_time,
            message_id=message_id,
        )
        
        # Step 1: Keyword checks (fast, no API call)
        self._check_keywords(result)
        
        # Step 2: Gemini evaluation for quality/accuracy
        self._gemini_analysis(result)
        
        # Step 3: Calculate final score
        self._calculate_score(result)
        
        return result
    
    def _check_keywords(self, result: GradeResult) -> None:
        """Check for expected and forbidden keywords"""
        response_lower = result.response.lower()
        
        # Check expected keywords
        for keyword in result.test_case.expected_keywords:
            if keyword.lower() in response_lower:
                result.keywords_found.append(keyword)
            else:
                result.keywords_missing.append(keyword)
        
        # Check forbidden keywords
        for keyword in result.test_case.forbidden_keywords:
            if keyword.lower() in response_lower:
                result.forbidden_found.append(keyword)
                result.issues.append(f"Found forbidden phrase: '{keyword}'")
    
    def _gemini_analysis(self, result: GradeResult) -> None:
        """Use Gemini to analyze response quality"""
        prompt = f"""You are a Senior QA Engineer reviewing an API copilot's response. Grade it critically.

## Test Case
**Question:** {result.test_case.question}
**Category:** {result.test_case.category}
**Severity:** {result.test_case.severity}

## Copilot Response
{result.response}

## Grading Criteria
1. **Accuracy (0.0-1.0)**: Does it correctly answer the question?
2. **Mudrex-specific (true/false)**: Does it cite Mudrex documentation or just give generic advice?
3. **Code Quality (0.0-1.0)**: Are code examples correct, complete, and runnable?
4. **Hallucination Risk (0.0-1.0)**: Does it make up information or claim things not in docs?

## Expected Keywords
The response SHOULD contain: {result.test_case.expected_keywords}

## Forbidden Phrases
The response should NOT contain: {result.test_case.forbidden_keywords}

Return ONLY valid JSON (no markdown):
{{
  "accuracy": 0.0-1.0,
  "mudrex_specific": true/false,
  "code_quality": 0.0-1.0,
  "hallucination_risk": 0.0-1.0,
  "issues": ["list of problems found"],
  "suggestions": ["list of improvements for the copilot"],
  "summary": "one sentence summary of the grade"
}}"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low for consistent grading
                    max_output_tokens=1000
                )
            )
            
            # Parse JSON response
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            
            data = json.loads(text)
            
            result.accuracy_score = float(data.get("accuracy", 0))
            result.mudrex_specific = bool(data.get("mudrex_specific", False))
            result.code_quality = float(data.get("code_quality", 0))
            result.hallucination_risk = float(data.get("hallucination_risk", 0))
            
            # Add issues and suggestions from Gemini
            result.issues.extend(data.get("issues", []))
            result.suggestions.extend(data.get("suggestions", []))
            
        except Exception as e:
            result.issues.append(f"Gemini analysis failed: {str(e)}")
            # Set default scores
            result.accuracy_score = 0.5
            result.mudrex_specific = False
            result.code_quality = 0.5
            result.hallucination_risk = 0.5
    
    def _calculate_score(self, result: GradeResult) -> None:
        """Calculate final score and pass/fail"""
        # Base score from Gemini analysis
        score = 0
        
        # Accuracy: 30 points
        score += result.accuracy_score * 30
        
        # Mudrex-specific: 20 points
        if result.mudrex_specific:
            score += 20
        
        # Code quality: 20 points
        score += result.code_quality * 20
        
        # Keyword coverage: 15 points
        if result.test_case.expected_keywords:
            keyword_ratio = len(result.keywords_found) / len(result.test_case.expected_keywords)
            score += keyword_ratio * 15
        else:
            score += 15  # Full points if no expected keywords
        
        # No forbidden keywords: 15 points
        if not result.forbidden_found:
            score += 15
        else:
            # Deduct based on severity of forbidden keywords
            deduction = min(15, len(result.forbidden_found) * 5)
            score += (15 - deduction)
        
        # Hallucination penalty
        if result.hallucination_risk > 0.5:
            score -= (result.hallucination_risk - 0.5) * 20
        
        # Response time bonus/penalty
        if result.response_time < 3:
            score += 5  # Fast response bonus
        elif result.response_time > 30:
            score -= 5  # Slow response penalty
        
        # Ensure score is in range
        result.score = max(0, min(100, int(score)))
        
        # Determine pass/fail
        result.passed = result.score >= self.PASS_THRESHOLD
        
        # Add summary issue if failed
        if not result.passed:
            if result.forbidden_found:
                result.issues.insert(0, f"FAILED: Contains forbidden phrases: {result.forbidden_found}")
            elif result.score < 50:
                result.issues.insert(0, f"FAILED: Low quality score ({result.score}/100)")
            else:
                result.issues.insert(0, f"FAILED: Score below threshold ({result.score}/100, need {self.PASS_THRESHOLD})")
    
    def grade_timeout(self, test_case: TestCase, timeout: float) -> GradeResult:
        """Create a failed grade result for timeout"""
        result = GradeResult(
            test_case=test_case,
            response="[TIMEOUT - No response received]",
            response_time=timeout,
            passed=False,
            score=0,
            issues=[f"TIMEOUT: Copilot did not respond within {timeout} seconds"],
            suggestions=["Check if copilot is running", "Check rate limiting", "Review health endpoint"],
        )
        return result
    
    def grade_error_response(self, test_case: TestCase, response: str, response_time: float) -> GradeResult:
        """Grade a response that appears to be an error message"""
        result = GradeResult(
            test_case=test_case,
            response=response,
            response_time=response_time,
            passed=False,
            score=20,
        )
        
        # Check for common error patterns
        error_patterns = [
            ("Something went wrong", "Internal error in copilot"),
            ("try again", "Transient error - may need retry"),
            ("rate limit", "Rate limiting triggered"),
            ("Conflict:", "Multiple bot instances running"),
        ]
        
        for pattern, issue in error_patterns:
            if pattern.lower() in response.lower():
                result.issues.append(issue)
        
        if not result.issues:
            result.issues.append("Response appears to be an error message")
        
        result.suggestions.append("Check copilot logs for errors")
        result.suggestions.append("Verify copilot health endpoint")
        
        return result
