from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


class RiskMode(str, Enum):
    NORMAL = "NORMAL"
    DEFENSIVE = "DEFENSIVE"
    CRISIS = "CRISIS"


@dataclass
class FeatureScales:
    slippage_pct: float = 1.0
    fee_usd: float = 10.0
    latency_ms: float = 500.0
    reliability_gap: float = 1.0


@dataclass
class WeightProfile:
    slippage: float
    fee: float
    latency: float
    reliability: float


@dataclass
class ReliabilityFeedback:
    historical_reliability: float = 1.0
    execution_quality: float = 1.0


@dataclass
class CalibrationSample:
    risk_mode: RiskMode
    slippage_pct: float
    fee_usd: float
    latency_ms: float
    reliability: float
    realized_cost: float


@dataclass
class RouteOption:
    name: str
    estimated_slippage_pct: float
    fee_usd: float
    latency_ms: float
    reliability: float  # 0..1


@dataclass
class RouteOptimizerConfig:
    scales: FeatureScales = field(default_factory=FeatureScales)
    weight_profiles: dict[RiskMode, WeightProfile] = field(default_factory=lambda: {
        RiskMode.NORMAL: WeightProfile(0.45, 0.25, 0.20, 0.10),
        RiskMode.DEFENSIVE: WeightProfile(0.35, 0.20, 0.15, 0.30),
        RiskMode.CRISIS: WeightProfile(0.20, 0.15, 0.10, 0.55),
    })
    reliability_alpha: float = 0.25
    quality_alpha: float = 0.20


class RouteOptimizer:
    """Selects best route by normalized objective, risk-aware weights, and live feedback."""

    def __init__(self, config: RouteOptimizerConfig | None = None) -> None:
        self.config = config or RouteOptimizerConfig()
        self._exchange_feedback: dict[str, ReliabilityFeedback] = {}

    def choose(self, routes: list[RouteOption], risk_mode: str | RiskMode = RiskMode.NORMAL) -> RouteOption:
        if not routes:
            raise ValueError("No routes provided")
        mode = risk_mode if isinstance(risk_mode, RiskMode) else RiskMode(risk_mode)
        return min(routes, key=lambda r: self.score(r, mode))

    def score(self, route: RouteOption, risk_mode: RiskMode = RiskMode.NORMAL) -> float:
        weights = self.config.weight_profiles.get(risk_mode, self.config.weight_profiles[RiskMode.NORMAL])
        scales = self.config.scales
        fb = self._exchange_feedback.get(route.name, ReliabilityFeedback())
        effective_reliability = max(0.0, min(1.0, route.reliability * fb.historical_reliability * fb.execution_quality))

        return (
            weights.slippage * (route.estimated_slippage_pct / max(scales.slippage_pct, 1e-9)) +
            weights.fee * (route.fee_usd / max(scales.fee_usd, 1e-9)) +
            weights.latency * (route.latency_ms / max(scales.latency_ms, 1e-9)) +
            weights.reliability * ((1 - effective_reliability) / max(scales.reliability_gap, 1e-9))
        )

    def update_execution_feedback(self, exchange: str, success: bool, quality_score: float) -> ReliabilityFeedback:
        current = self._exchange_feedback.get(exchange, ReliabilityFeedback())
        target_rel = 1.0 if success else 0.0
        rel = (1 - self.config.reliability_alpha) * current.historical_reliability + self.config.reliability_alpha * target_rel
        q = max(0.0, min(1.0, quality_score))
        quality = (1 - self.config.quality_alpha) * current.execution_quality + self.config.quality_alpha * q
        updated = ReliabilityFeedback(historical_reliability=rel, execution_quality=quality)
        self._exchange_feedback[exchange] = updated
        return updated

    def calibrate_offline(self, samples: list[CalibrationSample], persist_path: str | Path | None = None) -> dict[str, float]:
        if not samples:
            return {}

        # Inverse-realized-cost weighting: features correlated with cheaper execution get larger weights.
        eps = 1e-9
        accum = {"slippage": 0.0, "fee": 0.0, "latency": 0.0, "reliability": 0.0}
        for s in samples:
            cost_factor = 1.0 / max(abs(s.realized_cost), eps)
            accum["slippage"] += abs(s.slippage_pct) * cost_factor
            accum["fee"] += abs(s.fee_usd) * cost_factor
            accum["latency"] += abs(s.latency_ms) * cost_factor
            accum["reliability"] += abs(1 - s.reliability) * cost_factor

        total = sum(accum.values()) or 1.0
        tuned = {k: v / total for k, v in accum.items()}

        normal = WeightProfile(
            slippage=tuned["slippage"],
            fee=tuned["fee"],
            latency=tuned["latency"],
            reliability=tuned["reliability"],
        )
        self.config.weight_profiles[RiskMode.NORMAL] = normal
        self.config.weight_profiles[RiskMode.DEFENSIVE] = WeightProfile(
            slippage=normal.slippage * 0.85,
            fee=normal.fee * 0.85,
            latency=normal.latency * 0.75,
            reliability=min(1.0, normal.reliability * 1.55),
        )
        self.config.weight_profiles[RiskMode.CRISIS] = WeightProfile(
            slippage=normal.slippage * 0.70,
            fee=normal.fee * 0.70,
            latency=normal.latency * 0.60,
            reliability=min(1.0, normal.reliability * 2.0),
        )

        if persist_path:
            self.persist_coefficients(persist_path)
        return tuned

    def persist_coefficients(self, path: str | Path) -> None:
        payload = {
            "scales": asdict(self.config.scales),
            "weight_profiles": {mode.value: asdict(profile) for mode, profile in self.config.weight_profiles.items()},
            "feedback": {name: asdict(data) for name, data in self._exchange_feedback.items()},
        }
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_coefficients(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        scales = data.get("scales", {})
        self.config.scales = FeatureScales(**{**asdict(self.config.scales), **scales})

        profiles = data.get("weight_profiles", {})
        for mode_text, values in profiles.items():
            mode = RiskMode(mode_text)
            self.config.weight_profiles[mode] = WeightProfile(**values)

        feedback = data.get("feedback", {})
        self._exchange_feedback = {
            name: ReliabilityFeedback(**values)
            for name, values in feedback.items()
        }
