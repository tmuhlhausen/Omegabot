from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MarketSignal:
    regime: str = "NORMAL"
    gas_gwei: float = 0.1
    ofi: float = 0.0
    kelly_fraction: float = 0.05


@dataclass(frozen=True)
class MarketIntelFeatures:
    """Explicit feature schema used by market intelligence scoring."""

    ret_1m: float = 0.0
    spread_bps: float = 10.0
    depth_imbalance: float = 0.0
    gas_gwei: float = 0.1
    latency_ms: float = 120.0


class MarketIntelligenceHub:
    """Deterministic market-intel scoring with stable normalized feature transforms."""

    def __init__(self):
        self._last_signal = MarketSignal()

    @staticmethod
    def _clip(value: float, lower: float, upper: float) -> float:
        return min(upper, max(lower, value))

    @classmethod
    def _normalize(cls, value: float, lower: float, upper: float) -> float:
        if upper <= lower:
            return 0.0
        clipped = cls._clip(value, lower, upper)
        return (clipped - lower) / (upper - lower)

    @classmethod
    def _score_from_features(cls, features: MarketIntelFeatures) -> float:
        """Compute a stable score in [0, 1] from an explicit feature vector."""
        ret_component = cls._normalize(abs(features.ret_1m), 0.0, 0.10)
        spread_component = 1.0 - cls._normalize(features.spread_bps, 0.0, 50.0)
        imbalance_component = (features.depth_imbalance + 1.0) / 2.0
        imbalance_component = cls._clip(imbalance_component, 0.0, 1.0)
        gas_component = 1.0 - cls._normalize(features.gas_gwei, 0.0, 250.0)
        latency_component = 1.0 - cls._normalize(features.latency_ms, 0.0, 2000.0)

        raw_score = (
            0.25 * ret_component
            + 0.20 * spread_component
            + 0.20 * imbalance_component
            + 0.20 * gas_component
            + 0.15 * latency_component
        )
        return cls._clip(raw_score, 0.0, 1.0)

    def score_features(self, features: MarketIntelFeatures) -> float:
        return self._score_from_features(features)

    def score(self, symbol: str, price: float) -> float:
        # Backward-compatible wrapper retained for existing call-sites.
        if price <= 0:
            return 0.0
        features = MarketIntelFeatures(
            ret_1m=0.0,
            spread_bps=10.0,
            depth_imbalance=0.0,
            gas_gwei=self._last_signal.gas_gwei,
            latency_ms=120.0,
        )
        return self._score_from_features(features)
