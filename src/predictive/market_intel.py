from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import fmean, pstdev


@dataclass(frozen=True)
class ChainTelemetry:
    gas_gwei: float = 0.1
    pending_txs: int = 0
    mev_risk: float = 0.0


@dataclass
class MarketSignal:
    regime: str = "NORMAL"
    gas_gwei: float = 0.1
    ofi: float = 0.0
    kelly_fraction: float = 0.05
    volatility: float = 0.0
    microstructure_pressure: float = 0.0
    chain_stress: float = 0.0
    confidence: float = 0.5


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

    def __init__(self, history_size: int = 120):
        self._last_signal = MarketSignal()
        self._mid_history: dict[str, deque[float]] = {}
        self._history_size = max(16, history_size)

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _history_for(self, symbol: str) -> deque[float]:
        key = symbol.upper()
        if key not in self._mid_history:
            self._mid_history[key] = deque(maxlen=self._history_size)
        return self._mid_history[key]

    def process_tick(
        self,
        symbol: str,
        bid: float,
        ask: float,
        *,
        trade_imbalance: float = 0.0,
        chain_telemetry: ChainTelemetry | None = None,
    ) -> MarketSignal:
        if bid <= 0 or ask <= 0 or ask < bid:
            return self._last_signal

        telemetry = chain_telemetry or ChainTelemetry(gas_gwei=self._last_signal.gas_gwei)
        mid = (bid + ask) / 2.0
        spread = max(ask - bid, 1e-9)
        history = self._history_for(symbol)
        history.append(mid)

        returns: list[float] = []
        hist = list(history)
        for i in range(1, len(hist)):
            prev = hist[i - 1]
            if prev > 0:
                returns.append((hist[i] - prev) / prev)
        realized_vol = pstdev(returns) if len(returns) > 1 else 0.0

        spread_pressure = spread / mid
        micro_pressure = self._clamp((trade_imbalance * 0.7) - (spread_pressure * 20.0), -1.0, 1.0)
        ofi = self._clamp((trade_imbalance * 0.8) + (micro_pressure * 0.2), -1.0, 1.0)

        pending_component = min(1.0, telemetry.pending_txs / 200_000)
        chain_stress = self._clamp((telemetry.mev_risk * 0.55) + (pending_component * 0.25) + (telemetry.gas_gwei / 500.0 * 0.2), 0.0, 1.0)

        if realized_vol > 0.02 or chain_stress > 0.75:
            regime = "CRISIS"
        elif realized_vol > 0.008 or chain_stress > 0.45:
            regime = "VOLATILE"
        elif fmean(returns[-5:]) > 0.001 if returns else False:
            regime = "BULL"
        elif fmean(returns[-5:]) < -0.001 if returns else False:
            regime = "BEAR"
        else:
            regime = "NORMAL"

        edge_strength = abs(ofi) * (1.0 - self._clamp(realized_vol * 25.0, 0.0, 0.8))
        capital_guard = 1.0 - chain_stress
        kelly_fraction = self._clamp(0.02 + (edge_strength * capital_guard * 0.22), 0.01, 0.25)

        confidence = self._clamp(
            0.4 + (abs(ofi) * 0.25) + (self._clamp(0.02 - realized_vol, 0.0, 0.02) * 8.0) + ((1.0 - chain_stress) * 0.15),
            0.0,
            1.0,
        )

        self._last_signal = MarketSignal(
            regime=regime,
            gas_gwei=float(telemetry.gas_gwei),
            ofi=round(ofi, 6),
            kelly_fraction=round(kelly_fraction, 6),
            volatility=round(realized_vol, 8),
            microstructure_pressure=round(micro_pressure, 6),
            chain_stress=round(chain_stress, 6),
            confidence=round(confidence, 6),
        )
        return self._last_signal

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
