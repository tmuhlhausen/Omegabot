from __future__ import annotations


class ReportingLoopComponent:
    def __init__(self, engine):
        self.engine = engine

    async def hud_state_loop(self) -> None:
        await self.engine._hud_state_loop_impl()

    async def health_server(self) -> None:
        await self.engine._health_server_impl()
