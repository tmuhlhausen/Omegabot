from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskTemplate:
    """Per-asset risk template (IM-017)."""

    max_position_usd: float
    max_leverage: float
    stop_loss_pct: float
    cooldown_seconds: int


@dataclass
class AssetProfile:
    symbol: str
    category: str
    max_exposure_pct: float
    enabled: bool = True
    risk_template: RiskTemplate | None = None


# Category defaults — used when an asset profile omits a custom template.
CATEGORY_RISK_TEMPLATES: dict[str, RiskTemplate] = {
    "stable": RiskTemplate(
        max_position_usd=20_000.0, max_leverage=3.0, stop_loss_pct=0.005, cooldown_seconds=30
    ),
    "bluechip": RiskTemplate(
        max_position_usd=10_000.0, max_leverage=2.0, stop_loss_pct=0.02, cooldown_seconds=60
    ),
    "governance": RiskTemplate(
        max_position_usd=2_500.0, max_leverage=1.0, stop_loss_pct=0.04, cooldown_seconds=120
    ),
    "protocol": RiskTemplate(
        max_position_usd=1_500.0, max_leverage=1.0, stop_loss_pct=0.05, cooldown_seconds=180
    ),
}


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

    def get(self, symbol: str) -> AssetProfile | None:
        return self._assets.get(symbol.upper())

    def risk_template(self, symbol: str) -> RiskTemplate:
        """Resolve the risk template for ``symbol``.

        Lookup order:
          1. Asset-specific override on ``AssetProfile.risk_template``.
          2. Category default from ``CATEGORY_RISK_TEMPLATES``.
          3. Conservative fallback template (``protocol`` defaults).
        """
        profile = self._assets.get(symbol.upper())
        if profile is None:
            return CATEGORY_RISK_TEMPLATES["protocol"]
        if profile.risk_template is not None:
            return profile.risk_template
        return CATEGORY_RISK_TEMPLATES.get(profile.category, CATEGORY_RISK_TEMPLATES["protocol"])
