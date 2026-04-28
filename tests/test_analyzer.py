import unittest

from agent.llm_analyzer import TracebackAnalyzer


TRACEBACK = """Traceback (most recent call last):
  File \"app/buggy_service.py\", line 5, in compute_ratio
    return total / count
ZeroDivisionError: division by zero
"""


class AnalyzerTest(unittest.TestCase):
    def test_analyze_zero_division_bug(self):
        plan = TracebackAnalyzer().analyze(TRACEBACK)
        self.assertEqual(plan.target_file, "app/buggy_service.py")
        self.assertIn("ZeroDivisionError", plan.bug_summary)


if __name__ == "__main__":
    unittest.main()