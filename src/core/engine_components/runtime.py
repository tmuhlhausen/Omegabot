from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable

from .health.supervisor import RestartPolicy, TaskSupervisor


@dataclass(frozen=True)
class TaskSpec:
    name: str
    factory: Callable[[], Awaitable[None]]
    policy: RestartPolicy


class RuntimeComponent:
    """Builds, starts, and toggles supervised engine tasks."""

    def __init__(self, engine, supervisor: TaskSupervisor):
        self.engine = engine
        self.supervisor = supervisor
        self._base_policy = RestartPolicy(max_restarts=5, backoff_seconds=2.0, failure_budget=8)
        self._upgrade_tasks = []

    def start(self) -> None:
        for spec in self.base_tasks():
            self.supervisor.supervise(spec.name, spec.factory, spec.policy)
        self.sync_strategy_tasks()
        self._upgrade_tasks = self.engine.build_upgrade_tasks()

    def base_tasks(self) -> list[TaskSpec]:
        return [
            TaskSpec("price_feed", self.engine.market_loop.price_feed_loop, RestartPolicy(max_restarts=8, backoff_seconds=3.0, failure_budget=20)),
            TaskSpec("liq_scanner", self.engine.liq_scanner.start, self._base_policy),
            TaskSpec("arb_scan", self.engine.strategy_loop.arb_scan_loop, self._base_policy),
            TaskSpec("capital", self.engine.market_loop.capital_monitor_loop, self._base_policy),
            TaskSpec("profit_collect", self.engine.execution_loop.profit_collect_loop, self._base_policy),
            TaskSpec("scaling", self.engine.execution_loop.scaling_loop, self._base_policy),
            TaskSpec("hud_state", self.engine.reporting_loop.hud_state_loop, RestartPolicy(max_restarts=10, backoff_seconds=1.0, failure_budget=25)),
            TaskSpec("health", self.engine.reporting_loop.health_server, self._base_policy),
            TaskSpec("nonce_resync", self.engine.execution_loop.nonce_resync_loop, self._base_policy),
        ]

    def _strategy_specs(self) -> dict[str, TaskSpec]:
        return {
            "mev_backrun": TaskSpec("mev", self.engine.strategy_loop.mev_loop, self._base_policy),
            "gmx_funding": TaskSpec("gmx", self.engine.strategy_loop.gmx_loop, self._base_policy),
            "cross_chain": TaskSpec("xchain", self.engine.strategy_loop.xchain_loop, self._base_policy),
            "yield": TaskSpec("yield", self.engine.strategy_loop.yield_loop, self._base_policy),
        }

    def sync_strategy_tasks(self) -> None:
        for strategy, spec in self._strategy_specs().items():
            if self.engine.is_strategy_runtime_available(strategy) and strategy in self.engine._enabled:
                self.supervisor.supervise(spec.name, spec.factory, spec.policy)
            else:
                self.supervisor.stop(spec.name)

    async def enable_strategy(self, strategy: str) -> None:
        await self.engine.ensure_advanced_strategy(strategy)
        self.engine._enabled.add(strategy)
        self.sync_strategy_tasks()

    def disable_strategy(self, strategy: str) -> None:
        self.engine._enabled.discard(strategy)
        self.sync_strategy_tasks()

    async def wait(self) -> None:
        if self._upgrade_tasks:
            await asyncio.gather(self.supervisor.wait(), *self._upgrade_tasks, return_exceptions=True)
        else:
            await self.supervisor.wait()
