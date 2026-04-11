from __future__ import annotations


class MarketLoopComponent:
    def __init__(self, engine):
        self.engine = engine

    async def price_feed_loop(self) -> None:
        await self.engine._price_feed_loop_impl()

    async def capital_monitor_loop(self) -> None:
        await self.engine._capital_monitor_loop_impl()
