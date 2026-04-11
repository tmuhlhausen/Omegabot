from __future__ import annotations


class ExecutionLoopComponent:
    def __init__(self, engine):
        self.engine = engine

    async def profit_collect_loop(self) -> None:
        await self.engine._profit_collect_loop_impl()

    async def nonce_resync_loop(self) -> None:
        await self.engine._nonce_resync_loop_impl()

    async def scaling_loop(self) -> None:
        await self.engine._scaling_loop_impl()
