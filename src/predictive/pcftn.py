from __future__ import annotations


class _PCFTNRegistry:
    """Compatibility registry used by engine import contract."""

    def infer(self, features: dict) -> float:
        if not features:
            return 0.0
        numeric = [v for v in features.values() if isinstance(v, (int, float))]
        if not numeric:
            return 0.0
        return float(sum(numeric) / len(numeric))


pcftn_registry = _PCFTNRegistry()
