"""Simple web-service business logic used by the auto-repair demo.

The initial version intentionally keeps a zero-division bug so the Agent can
observe the traceback, patch this file, run tests, commit the change, and notify
Feishu/Lark.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatsRequest:
    total: float
    count: int


def compute_average(request: StatsRequest) -> float:
    """Return average value.

    BUG for demo: count == 0 raises ZeroDivisionError. The Agent should patch
    this line to return 0.0 when count is zero.
    """
    return request.total / request.count
