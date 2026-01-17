"""Observability helpers: structured logging and metrics abstraction.

Provides:
- get_logger(name) -> logging.Logger
- metrics: object with increment(name, value=1) and observe(name, value)

Metrics attempts to use prometheus_client if available, otherwise falls back to a simple in-memory collector useful for tests.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    # Help static type checkers and linters (prometheus_client is optional at runtime)
    pass  # type: ignore


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"probe.{name}")


class DummyCounter:
    def __init__(self):
        self._value = 0

    def inc(self, v=1):
        self._value += v

    def get(self):
        return self._value


class DummyGauge:
    def __init__(self):
        self._values = []

    def observe(self, v):
        self._values.append(v)

    def get_all(self):
        return list(self._values)


class Metrics:
    def __init__(self):
        self._enabled = False
        self._counters: Dict[str, Any] = {}
        self._gauges: Dict[str, Any] = {}

        try:
            # Import via importlib to avoid static import-time lint errors when prometheus_client isn't present
            import importlib

            pc = importlib.import_module("prometheus_client")
            counter_cls = getattr(pc, "Counter")
            histogram_cls = getattr(pc, "Histogram")

            # create named metrics
            self.fetch_total = counter_cls("probe_fetch_total", "Total fetch attempts")
            self.fetch_failures = counter_cls("probe_fetch_failures", "Failed fetches")
            self.fetch_retries = counter_cls("probe_fetch_retries", "Fetch retries")
            self.fetch_duration = histogram_cls(
                "probe_fetch_duration_seconds", "Fetch duration seconds"
            )
            self.fetch_backoff = histogram_cls(
                "probe_fetch_backoff_seconds", "Backoff/wait seconds"
            )
            self._enabled = True
        except Exception:
            # Prometheus not available -> use dummy metrics
            self.fetch_total = DummyCounter()
            self.fetch_failures = DummyCounter()
            self.fetch_retries = DummyCounter()
            self.fetch_duration = DummyGauge()
            self.fetch_backoff = DummyGauge()

    def increment(self, name: str, value: int = 1):
        if name == "fetch_total":
            self.fetch_total.inc(value)
        elif name == "fetch_failures":
            self.fetch_failures.inc(value)
        elif name == "fetch_retries":
            self.fetch_retries.inc(value)

    def observe(self, name: str, value: float):
        if name == "fetch_duration_seconds":
            # histograms use observe; dummy uses observe too
            try:
                self.fetch_duration.observe(value)
            except Exception:
                self.fetch_duration.observe(value)
        elif name == "fetch_backoff_seconds":
            try:
                self.fetch_backoff.observe(value)
            except Exception:
                self.fetch_backoff.observe(value)


# singleton metrics instance
metrics = Metrics()
