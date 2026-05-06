"""Traceback root-cause analyzer.

For the competition demo this module provides a deterministic fallback so the
recorded demo is stable. In production, the same interface can call an LLM and
return a FixPlan.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FixPlan:
    bug_summary: str
    target_file: str
    old_snippet: str
    new_snippet: str
    test_focus: str
    confidence: float = 1.0


class TracebackAnalyzer:
    def analyze(self, traceback_text: str) -> FixPlan:
        """Infer a repair plan from traceback/log text."""
        if "ZeroDivisionError" in traceback_text and "web_service.py" in traceback_text:
            return FixPlan(
                bug_summary="ZeroDivisionError when count == 0 in compute_average",
                target_file="app/web_service.py",
                old_snippet="return request.total / request.count",
                new_snippet="return 0.0 if request.count == 0 else request.total / request.count",
                test_focus="count=0 should return 0.0",
                confidence=0.98,
            )

        if "ZeroDivisionError" in traceback_text and "buggy_service.py" in traceback_text:
            return FixPlan(
                bug_summary="ZeroDivisionError when count == 0 in compute_ratio",
                target_file="app/buggy_service.py",
                old_snippet="return total / count",
                new_snippet="return 0.0 if count == 0 else total / count",
                test_focus="count=0 should return 0.0",
                confidence=0.95,
            )

        raise ValueError(
            "Unsupported traceback pattern. Add an analyzer rule or connect an LLM provider."
        )
