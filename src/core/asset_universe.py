from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AssetProfile:
    symbol: str
    category: str
    max_exposure_pct: float
    enabled: bool = True


class AssetUniverse:
    """Taxonomy and policy layer for crypto type expansion."""

    def __init__(self):
        self._assets: dict[str, AssetProfile] = {
            "WETH": AssetProfile("WETH", "bluechip", 0.35),
            "WBTC": AssetProfile("WBTC", "bluechip", 0.25),
            "USDC": AssetProfile("USDC", "stable", 0.60),
            "ARB": AssetProfile("ARB", "governance", 0.15),
            "GMX": AssetProfile("GMX", "protocol", 0.10),
        }

    def add_or_update(self, profile: AssetProfile) -> None:
        self._assets[profile.symbol.upper()] = profile

    def active_symbols(self) -> list[str]:
        return sorted([k for k, v in self._assets.items() if v.enabled])

    def by_category(self, category: str) -> list[AssetProfile]:
        return [v for v in self._assets.values() if v.category == category and v.enabled]
