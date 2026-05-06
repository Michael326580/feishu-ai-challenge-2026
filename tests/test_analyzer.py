import unittest

from agent.llm_analyzer import TracebackAnalyzer


TRACEBACK = """Traceback (most recent call last):
  File "app/web_service.py", line 24, in compute_average
    return request.total / request.count
ZeroDivisionError: division by zero
"""


class AnalyzerTest(unittest.TestCase):
    def test_analyze_zero_division_bug(self):
        plan = TracebackAnalyzer().analyze(TRACEBACK)
        self.assertEqual(plan.target_file, "app/web_service.py")
        self.assertIn("ZeroDivisionError", plan.bug_summary)
        self.assertIn("request.count == 0", plan.new_snippet)


if __name__ == "__main__":
    unittest.main()
