from __future__ import annotations

import os
from dataclasses import dataclass, field


class FeatureFlags:
    """Additive-first rollout flags for revolutionary roadmap modules."""

    def __init__(self):
        self.digital_twin = os.getenv("FF_DIGITAL_TWIN", "0") == "1"
        self.autonomous_risk = os.getenv("FF_AUTONOMOUS_RISK", "1") == "1"
        self.strategy_discovery = os.getenv("FF_STRATEGY_DISCOVERY", "0") == "1"
        self.cross_chain_mesh = os.getenv("FF_CROSS_CHAIN_MESH", "0") == "1"

    def to_dict(self) -> dict:
        return {
            "digital_twin": self.digital_twin,
            "autonomous_risk": self.autonomous_risk,
            "strategy_discovery": self.strategy_discovery,
            "cross_chain_mesh": self.cross_chain_mesh,
        }


@dataclass
class CanaryRelease:
    """Single canary release entry tracked by ``CanaryController``."""

    name: str
    rollout_pct: float
    health_score: float = 1.0
    failures: int = 0
    promoted: bool = False
    rolled_back: bool = False

    def is_active(self) -> bool:
        return not self.rolled_back and not self.promoted


class CanaryController:
    """Stage canary releases for strategy/formula rollouts.

    Behaviors:
      - Register a candidate at low rollout percentage.
      - Record outcomes; auto-rollback if health drops below ``rollback_threshold``.
      - Auto-promote to 100% when health stays above ``promote_threshold`` for
        ``promote_after`` consecutive successful samples.

    The controller is intentionally side-effect free so callers (engine + SRE
    automation) can inspect the state and route accordingly.
    """

    def __init__(
        self,
        *,
        rollback_threshold: float = 0.6,
        promote_threshold: float = 0.9,
        promote_after: int = 5,
    ) -> None:
        self.rollback_threshold = rollback_threshold
        self.promote_threshold = promote_threshold
        self.promote_after = promote_after
        self._releases: dict[str, CanaryRelease] = {}
        self._streaks: dict[str, int] = {}

    def register(self, name: str, rollout_pct: float = 5.0) -> CanaryRelease:
        release = CanaryRelease(name=name, rollout_pct=rollout_pct)
        self._releases[name] = release
        self._streaks[name] = 0
        return release

    def record(self, name: str, success: bool, health: float) -> CanaryRelease:
        release = self._releases.get(name)
        if release is None:
            release = self.register(name)
        if release.rolled_back or release.promoted:
            return release

        release.health_score = max(0.0, min(1.0, health))
        if not success:
            release.failures += 1
            self._streaks[name] = 0
        else:
            self._streaks[name] += 1

        if release.health_score < self.rollback_threshold:
            release.rolled_back = True
            release.rollout_pct = 0.0
            return release

        if (
            self._streaks[name] >= self.promote_after
            and release.health_score >= self.promote_threshold
        ):
            release.promoted = True
            release.rollout_pct = 100.0

        return release

    def status(self, name: str) -> CanaryRelease | None:
        return self._releases.get(name)

    def active(self) -> list[CanaryRelease]:
        return [r for r in self._releases.values() if r.is_active()]
