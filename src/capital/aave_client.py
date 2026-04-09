from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AaveAccountState:
    health_factor: float = 99.0
    collateral_usd: float = 0.0
    debt_usd: float = 0.0
    available_borrow_usd: float = 0.0

    @property
    def is_healthy(self) -> bool:
        return self.health_factor >= 1.3

    @property
    def is_critical(self) -> bool:
        return self.health_factor < 1.05


class AaveClient:
    """Minimal async Aave client used by engine/risk/scaling paths."""

    def __init__(self, w3=None, account=None, nonce_manager=None):
        self.w3 = w3
        self.account = account
        self.nonce_manager = nonce_manager
        self._state = AaveAccountState(health_factor=2.5, collateral_usd=1000.0, debt_usd=400.0, available_borrow_usd=250.0)

    async def initialize(self) -> None:
        return None

    async def get_account_state(self, force: bool = False) -> AaveAccountState:
        return self._state

    async def get_health_factor(self) -> float:
        return self._state.health_factor

    async def simulate_health_factor(
        self,
        additional_collateral_usd: float,
        additional_debt_usd: float,
    ) -> float:
        debt = max(1e-9, self._state.debt_usd + max(0.0, additional_debt_usd))
        collateral = self._state.collateral_usd + max(0.0, additional_collateral_usd)
        return collateral / debt

    async def supply_usdc(self, amount_usd: float) -> None:
        self._state.collateral_usd += max(0.0, amount_usd)

    async def borrow_usdc(self, amount_usd: float) -> None:
        self._state.debt_usd += max(0.0, amount_usd)

    async def emergency_repay(self) -> bool:
        self._state.debt_usd = max(0.0, self._state.debt_usd - 50.0)
        return True

    async def soft_rebalance(self) -> bool:
        self._state.health_factor = max(self._state.health_factor, 1.8)
        return True
