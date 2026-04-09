from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExpansionState:
    cumulative_profit_usd: float


class ExpansionRouter:
    """Profit-gated unlock router for bridges/exchanges/chains."""

    TIERS = {
        0: {"min_profit": 0, "chains": ["arbitrum"], "exchanges": ["uniswap", "camelot", "sushi"]},
        1: {"min_profit": 500, "chains": ["arbitrum", "base", "polygon"], "exchanges": ["uniswap", "camelot", "sushi", "aerodrome"]},
        2: {"min_profit": 5000, "chains": ["arbitrum", "base", "polygon", "optimism", "bsc"], "exchanges": ["uniswap", "camelot", "sushi", "aerodrome", "pancake"]},
        3: {"min_profit": 50000, "chains": ["arbitrum", "base", "polygon", "optimism", "bsc", "ethereum"], "exchanges": ["uniswap", "camelot", "sushi", "aerodrome", "pancake", "curve"]},
    }

    def resolve_tier(self, state: ExpansionState) -> int:
        profit = state.cumulative_profit_usd
        if profit >= self.TIERS[3]["min_profit"]:
            return 3
        if profit >= self.TIERS[2]["min_profit"]:
            return 2
        if profit >= self.TIERS[1]["min_profit"]:
            return 1
        return 0

    def allowed(self, state: ExpansionState) -> dict:
        tier = self.resolve_tier(state)
        return {"tier": tier, **self.TIERS[tier]}
