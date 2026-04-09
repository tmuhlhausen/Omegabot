from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MarketSignal:
    regime: str = "NORMAL"
    gas_gwei: float = 0.1
    ofi: float = 0.0
    kelly_fraction: float = 0.05


class MarketIntelligenceHub:
    """Lightweight market intel placeholder with deterministic interface."""

    def __init__(self):
        self._last_signal = MarketSignal()

    def score(self, symbol: str, price: float) -> float:
        if price <= 0:
            return 0.0
        base = (hash(symbol.upper()) % 100) / 1000
        return min(1.0, 0.5 + base)
