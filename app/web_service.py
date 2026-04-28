"""Intentionally buggy service for agent auto-repair simulation."""


def compute_ratio(total: float, count: int) -> float:
    # BUG: should guard count == 0
    return total / count