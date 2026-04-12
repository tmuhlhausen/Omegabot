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


class HUDState:
    """Flexible state container used by the engine HUD loops."""

    def __init__(self):
        self.start_time = 0.0
        self.total_profit = 0.0
        self.trades_total = 0
        self.wins_total = 0
        self.active_bots = 1
        self.chain = "arbitrum"
        self.health_factor = 99.0
        self.collateral_usd = 0.0
        self.debt_usd = 0.0
        self.available_borrow = 0.0
        self.gas_gwei = 0.0
        self.regime = "UNKNOWN"
        self.prices: dict[str, float] = {}
        self.recent_trades: list[dict] = []

    def add_trade(self, trade: TradeRecord) -> None:
        self.recent_trades.append({
            "strategy": trade.strategy,
            "gross_usd": trade.gross_usd,
            "net_usd": trade.net_usd,
            "tx_hash": trade.tx_hash,
            "timestamp": trade.timestamp,
        })
        self.recent_trades = self.recent_trades[-50:]

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class HUDManager:
    def __init__(self):
        self.commands: dict[str, callable] = {}

    def register(self, name: str, handler):
        self.commands[name] = handler

    def register_command(self, name: str, handler):
        self.commands[name] = handler


@dataclass
class Runbook:
    """Self-remediation runbook entry."""

    name: str
    triggers: tuple[str, ...]
    handler: callable
    description: str = ""


@dataclass
class RunbookExecution:
    """Result of executing a runbook handler."""

    name: str
    triggered_by: str
    success: bool
    message: str
    timestamp: float = field(default_factory=time.time)


class RunbookRegistry:
    """Self-remediation runbook registry (IM-037).

    The engine + monitoring stack publish anomaly tags via ``trigger``. Each
    registered runbook with a matching trigger is executed and the result is
    captured for the HUD timeline. Handlers must be idempotent and side-effect
    contained.
    """

    def __init__(self) -> None:
        self._runbooks: dict[str, Runbook] = {}
        self._history: list[RunbookExecution] = []

    def register(
        self,
        name: str,
        triggers: tuple[str, ...],
        handler: callable,
        description: str = "",
    ) -> Runbook:
        rb = Runbook(name=name, triggers=triggers, handler=handler, description=description)
        self._runbooks[name] = rb
        return rb

    def trigger(self, tag: str, **payload) -> list[RunbookExecution]:
        results: list[RunbookExecution] = []
        for rb in self._runbooks.values():
            if tag not in rb.triggers:
                continue
            try:
                outcome = rb.handler(tag, **payload)
                msg = str(outcome) if outcome is not None else "ok"
                exec_result = RunbookExecution(
                    name=rb.name, triggered_by=tag, success=True, message=msg
                )
            except Exception as exc:  # pragma: no cover - exercised via test
                exec_result = RunbookExecution(
                    name=rb.name,
                    triggered_by=tag,
                    success=False,
                    message=str(exc)[:200],
                )
            self._history.append(exec_result)
            results.append(exec_result)
        return results

    @property
    def history(self) -> list[RunbookExecution]:
        return list(self._history)

    @property
    def names(self) -> list[str]:
        return sorted(self._runbooks.keys())


shared_state = HUDState()
manager = HUDManager()
runbooks = RunbookRegistry()


def run_hud_server(port: int = 8080):
    """Non-blocking compatibility shim; returns task if loop is available."""
    async def _idle_server():
        while True:
            await asyncio.sleep(60)

    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(_idle_server())
    except RuntimeError:
        return None
