from __future__ import annotations


class _GarchModel:
    def __init__(self):
        self._vol = 0.02

    def update(self, ret: float) -> float:
        self._vol = max(1e-6, 0.94 * self._vol + 0.06 * abs(ret))
        return self._vol


class GarchRegistry:
    """Simple symbol->model registry used by engine hot paths."""

    def __init__(self):
        self._models: dict[str, _GarchModel] = {}

    def get(self, symbol: str) -> _GarchModel:
        key = symbol.upper()
        if key not in self._models:
            self._models[key] = _GarchModel()
        return self._models[key]
