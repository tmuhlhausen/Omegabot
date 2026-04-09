from __future__ import annotations

from dataclasses import dataclass, field
import time


@dataclass
class FormulaRecord:
    key: str
    author: str
    created_at: float = field(default_factory=time.time)
    benchmark_score: float = 0.0
    active: bool = True


class FormulaProvenanceLedger:
    """Tracks formula metadata, score drift and activation status."""

    def __init__(self):
        self._records: dict[str, FormulaRecord] = {}

    def upsert(self, key: str, author: str, benchmark_score: float) -> FormulaRecord:
        rec = self._records.get(key)
        if rec is None:
            rec = FormulaRecord(key=key, author=author, benchmark_score=benchmark_score)
            self._records[key] = rec
        else:
            rec.benchmark_score = benchmark_score
        return rec

    def deactivate(self, key: str) -> bool:
        rec = self._records.get(key)
        if not rec:
            return False
        rec.active = False
        return True

    def top(self, n: int = 5) -> list[FormulaRecord]:
        return sorted(self._records.values(), key=lambda r: r.benchmark_score, reverse=True)[:n]
