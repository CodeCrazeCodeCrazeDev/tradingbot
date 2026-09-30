"""Lightweight in-tree latency tracking helpers.

Replaces the archived ``infrastructure.performance_optimizer`` compat surface
(``measure_performance`` decorator + ``get_performance_monitor`` singleton)
without importing from ``trading_bot._archive``, which production code is not
allowed to touch (see tests/test_architectural_enforcement.py).
"""

import functools
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class LatencyMonitor:
    """In-memory per-operation latency recorder (legacy compat surface)."""

    def __init__(self, maxlen: int = 1000):
        self._latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=maxlen))
        self._lock = threading.Lock()

    def record_latency(self, operation: str, latency_seconds: float) -> None:
        with self._lock:
            self._latencies[operation].append(latency_seconds)

    def get_report(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            snapshot = {op: list(samples) for op, samples in self._latencies.items()}
        report = {}
        for op, data in snapshot.items():
            if not data:
                continue
            report[op] = {
                "count": len(data),
                "mean": statistics.fmean(data),
                "min": min(data),
                "max": max(data),
            }
        return report

    def reset(self) -> None:
        with self._lock:
            self._latencies.clear()


_monitor = LatencyMonitor()


def get_performance_monitor() -> LatencyMonitor:
    """Get the global latency monitor."""
    return _monitor


def measure_performance(operation_name: Optional[str] = None):
    """Decorator recording call latency into the global monitor."""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                _monitor.record_latency(op_name, time.perf_counter() - start)

        return wrapper
    return decorator
