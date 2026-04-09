from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class TradeRecord:
    strategy: str
    gross_usd: float
    net_usd: float
    tx_hash: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class _SharedState:
    start_time: float = 0.0
    total_profit: float = 0.0
    trades: int = 0


class HUDManager:
    def __init__(self):
        self.commands: dict[str, callable] = {}

    def register(self, name: str, handler):
        self.commands[name] = handler


shared_state = _SharedState()
manager = HUDManager()


async def run_hud_server(port: int = 8080) -> None:
    """Compatibility no-op server loop for environments without web stack."""
    while True:
        await asyncio.sleep(60)
