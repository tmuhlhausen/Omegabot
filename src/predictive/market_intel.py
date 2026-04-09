from __future__ import annotations


class MarketIntelligenceHub:
    """Lightweight market intel placeholder with deterministic interface."""

    def score(self, symbol: str, price: float) -> float:
        if price <= 0:
            return 0.0
        base = (hash(symbol.upper()) % 100) / 1000
        return min(1.0, 0.5 + base)
