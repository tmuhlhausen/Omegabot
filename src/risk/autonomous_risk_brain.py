from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskSnapshot:
    volatility: float
    drawdown_pct: float
    liquidation_risk: float
    latency_ms: float


class AutonomousRiskBrain:
    """Computes adaptive risk mode from unified telemetry."""

    def classify(self, snap: RiskSnapshot) -> str:
        score = (
            0.35 * snap.volatility +
            0.30 * (snap.drawdown_pct / 100) +
            0.25 * snap.liquidation_risk +
            0.10 * min(1.0, snap.latency_ms / 1000)
        )
        if score >= 0.65:
            return "CRISIS"
        if score >= 0.40:
            return "DEFENSIVE"
        return "NORMAL"

    def max_position_multiplier(self, mode: str) -> float:
        return {"CRISIS": 0.25, "DEFENSIVE": 0.60, "NORMAL": 1.0}.get(mode, 0.50)
