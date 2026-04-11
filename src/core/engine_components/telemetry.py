from __future__ import annotations

from collections import defaultdict


class ErrorTelemetry:
    """Simple in-memory error telemetry keyed by loop and exception type."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = defaultdict(int)

    def record(self, loop_name: str, error: Exception) -> None:
        key = f"{loop_name}:{error.__class__.__name__}"
        self._counts[key] += 1

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)
