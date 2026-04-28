"""LLM-style root-cause analyzer.

This module keeps a deterministic fallback for offline environments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FixPlan:
    bug_summary: str
    target_file: str
    old_snippet: str
    new_snippet: str
    test_focus: str


class TracebackAnalyzer:
    def analyze(self, traceback_text: str) -> FixPlan:
        """Infer a fix-plan from traceback/log text.

        In production this method can call an actual LLM.
        """
        if "ZeroDivisionError" in traceback_text and "buggy_service.py" in traceback_text:
            return FixPlan(
                bug_summary="ZeroDivisionError when count == 0 in compute_ratio",
                target_file="app/buggy_service.py",
                old_snippet="return total / count",
                new_snippet="return 0.0 if count == 0 else total / count",
                test_focus="count=0 should return 0.0",
            )
        raise ValueError("Unsupported traceback pattern; add a new analyzer rule or LLM prompt.")