from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReplayEvent:
    ts: float
    symbol: str
    price: float
    signal: float


@dataclass
class ReplayResult:
    trades: int = 0
    pnl_usd: float = 0.0
    max_drawdown_pct: float = 0.0
    metadata: dict = field(default_factory=dict)


class DigitalTwin:
    """Deterministic replay scaffold for strategy shadow validation."""

    def run(self, events: list[ReplayEvent], threshold: float = 0.2) -> ReplayResult:
        pnl = 0.0
        peak = 0.0
        dd = 0.0
        trades = 0
        for e in events:
            if abs(e.signal) < threshold:
                continue
            trades += 1
            pnl += (e.signal * 0.01) * e.price
            peak = max(peak, pnl)
            if peak > 0:
                dd = max(dd, (peak - pnl) / peak)
        return ReplayResult(trades=trades, pnl_usd=round(pnl, 4), max_drawdown_pct=round(dd * 100, 4))
