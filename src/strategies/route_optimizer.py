from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RouteOption:
    name: str
    estimated_slippage_pct: float
    fee_usd: float
    latency_ms: float
    reliability: float  # 0..1


class RouteOptimizer:
    """Selects best route by blended slippage/fee/latency/reliability objective."""

    def choose(self, routes: list[RouteOption]) -> RouteOption:
        if not routes:
            raise ValueError("No routes provided")

        def score(r: RouteOption) -> float:
            return (
                0.45 * r.estimated_slippage_pct +
                0.25 * (r.fee_usd / 10) +
                0.20 * (r.latency_ms / 500) +
                0.10 * (1 - r.reliability)
            )

        return min(routes, key=score)
