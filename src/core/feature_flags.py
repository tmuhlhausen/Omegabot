from __future__ import annotations

import os


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
