from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReplayEvent:
    ts: float
    symbol: str
    price: float
    signal: float


@dataclass(frozen=True)
class ExecutionModel:
    name: str = "baseline"
    fee_bps: float = 4.0
    slippage_bps: float = 1.0
    size_multiplier: float = 1.0


@dataclass
class ReplayResult:
    trades: int = 0
    pnl_usd: float = 0.0
    max_drawdown_pct: float = 0.0
    metadata: dict = field(default_factory=dict)


class DigitalTwin:
    """Deterministic replay framework for strategy shadow validation.

    Engine interface contract (from ``src/core/engine.py`` call sites):
      - ``run(events, threshold, seed, strategy) -> ReplayResult``.
      - ReplayResult must contain ``trades``, ``pnl_usd``, ``max_drawdown_pct`` fields.
      - Events are sorted by timestamp/symbol and consumed without mutating source input.
      - Invalid events are skipped (never raise) to keep command workflows resilient.
    """

    _MODELS = {
        "baseline": ExecutionModel(name="baseline", fee_bps=4.0, slippage_bps=1.0, size_multiplier=1.0),
        "momentum": ExecutionModel(name="momentum", fee_bps=3.0, slippage_bps=1.5, size_multiplier=1.2),
        "mean_reversion": ExecutionModel(name="mean_reversion", fee_bps=4.5, slippage_bps=0.8, size_multiplier=0.9),
    }

    @staticmethod
    def _stable_symbol_salt(symbol: str) -> int:
        return sum((idx + 1) * ord(ch) for idx, ch in enumerate(symbol.upper()))

    def run(
        self,
        events: list[ReplayEvent],
        threshold: float = 0.2,
        *,
        seed: int = 7,
        strategy: str = "baseline",
    ) -> ReplayResult:
        model = self._MODELS.get(strategy, self._MODELS["baseline"])

        pnl = 0.0
        peak = 0.0
        dd = 0.0
        trades = 0
        equity_curve: list[float] = []
        replay_events = sorted(events, key=lambda e: (e.ts, e.symbol))

        for idx, event in enumerate(replay_events):
            if abs(event.signal) < threshold or event.price <= 0:
                continue

            rng = random.Random(seed + idx + self._stable_symbol_salt(event.symbol))
            slippage_noise = (rng.random() - 0.5) * model.slippage_bps
            effective_slippage_bps = model.slippage_bps + slippage_noise
            gross_return = event.signal * 0.01
            execution_penalty = (model.fee_bps + abs(effective_slippage_bps)) / 10_000
            net_return = gross_return - execution_penalty

            pnl += event.price * net_return * model.size_multiplier
            trades += 1
            peak = max(peak, pnl)
            if peak > 0:
                dd = max(dd, (peak - pnl) / peak)
            equity_curve.append(round(pnl, 6))

        return ReplayResult(
            trades=trades,
            pnl_usd=round(pnl, 4),
            max_drawdown_pct=round(dd * 100, 4),
            metadata={
                "seed": seed,
                "strategy": model.name,
                "threshold": threshold,
                "event_count": len(replay_events),
                "start_ts": replay_events[0].ts if replay_events else None,
                "end_ts": replay_events[-1].ts if replay_events else None,
                "equity_curve": equity_curve,
            },
        )
