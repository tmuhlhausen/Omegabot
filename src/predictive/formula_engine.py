from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class FormulaSpec:
    name: str
    version: str
    fn: Callable[[dict], float]
    tier_required: int = 0
    tags: list[str] = field(default_factory=list)


class FormulaEngine:
    """Versioned formula registry with tier-aware evaluation."""

    def __init__(self):
        self._formulas: dict[str, FormulaSpec] = {}

    def register(self, spec: FormulaSpec) -> None:
        self._formulas[f"{spec.name}:{spec.version}"] = spec

    def evaluate(self, key: str, features: dict, tier: int = 0) -> float:
        spec = self._formulas[key]
        if tier < spec.tier_required:
            raise PermissionError(f"Formula {key} requires tier {spec.tier_required}")
        return float(spec.fn(features))

    def list_available(self, tier: int) -> list[str]:
        return sorted(k for k, v in self._formulas.items() if v.tier_required <= tier)


def build_default_formula_engine() -> FormulaEngine:
    eng = FormulaEngine()
    eng.register(FormulaSpec(
        name="micro_momentum",
        version="1.0.0",
        tier_required=0,
        tags=["momentum", "microstructure"],
        fn=lambda x: 0.4 * float(x.get("ofi", 0.0)) + 0.6 * float(x.get("ret_1m", 0.0)),
    ))
    eng.register(FormulaSpec(
        name="volatility_guard",
        version="1.0.0",
        tier_required=1,
        tags=["risk", "volatility"],
        fn=lambda x: max(0.0, 1.0 - float(x.get("vol_5m", 0.0))),
    ))
    return eng
