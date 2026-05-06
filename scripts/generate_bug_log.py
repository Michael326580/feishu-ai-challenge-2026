"""Generate the traceback log used by run_agent_demo.py."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
(root / "logs").mkdir(exist_ok=True)
log_text = """Traceback (most recent call last):
  File "app/web_service.py", line 24, in compute_average
    return request.total / request.count
ZeroDivisionError: division by zero

Request payload: {"total": 10, "count": 0}
"""
(root / "logs" / "service_error.log").write_text(log_text, encoding="utf-8")
print("Wrote logs/service_error.log")
