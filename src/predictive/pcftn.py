from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _PCFTNSignal:
    fci: float = 0.0
    cm: float = 0.0
    pct: float = 0.0
    rci: float = 0.0
    csrs: float = 0.0
    marg: float = 0.0
    fci_lower: float = -1.0
    fci_upper: float = 1.0
    alert: bool = False
    direction: str = "neutral"
    confidence: float = 0.0
    horizon_s: int = 60
    regime: str = "NORMAL"
    entropy_micro: float = 0.0
    entropy_meso: float = 0.0
    entropy_macro: float = 0.0
    bond_dim: int = 8


class _PCFTNRegistry:
    """Compatibility registry used by engine import contract."""

    def __init__(self):
        self._last_signals: dict[str, _PCFTNSignal] = {"WETH": _PCFTNSignal()}

    def infer(self, features: dict) -> float:
        if not features:
            return 0.0
        numeric = [v for v in features.values() if isinstance(v, (int, float))]
        if not numeric:
            return 0.0
        return float(sum(numeric) / len(numeric))


pcftn_registry = _PCFTNRegistry()
