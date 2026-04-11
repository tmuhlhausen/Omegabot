from __future__ import annotations


class BootstrapComponent:
    """Initialization/bootstrap pipeline extracted from TradingEngine."""

    def __init__(self, engine):
        self.engine = engine

    async def initialize(self) -> None:
        await self.engine._initialize_impl()

    async def init_advanced_strategies(self) -> None:
        await self.engine._init_advanced_strategies_impl()
