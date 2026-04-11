from __future__ import annotations


class StrategyLoopComponent:
    def __init__(self, engine):
        self.engine = engine

    async def arb_scan_loop(self) -> None:
        await self.engine._arb_scan_loop_impl()

    async def mev_loop(self) -> None:
        await self.engine._mev_loop_impl()

    async def gmx_loop(self) -> None:
        await self.engine._gmx_loop_impl()

    async def xchain_loop(self) -> None:
        await self.engine._xchain_loop_impl()

    async def yield_loop(self) -> None:
        await self.engine._yield_loop_impl()
