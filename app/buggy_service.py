"""Backward-compatible wrapper for old demo imports."""

from __future__ import annotations

from app.web_service import StatsRequest, compute_average


def compute_ratio(total: float, count: int) -> float:
    return compute_average(StatsRequest(total=total, count=count))
