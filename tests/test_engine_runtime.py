from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.engine_components.health.supervisor import RestartPolicy, TaskSupervisor
from src.core.engine_components.runtime import RuntimeComponent


class DummyTelemetry:
    def __init__(self):
        self.events = []

    def record(self, name, exc):
        self.events.append((name, str(exc)))


@pytest.mark.asyncio
async def test_task_supervisor_stop_cancels_running_task():
    telemetry = DummyTelemetry()
    supervisor = TaskSupervisor(telemetry)

    async def loop_forever():
        try:
            while True:
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            raise

    policy = RestartPolicy(max_restarts=0, backoff_seconds=0, failure_budget=0)
    supervisor.supervise("demo", loop_forever, policy)
    await asyncio.sleep(0.02)
    assert supervisor.is_running("demo") is True
    assert supervisor.stop("demo") is True
    await asyncio.sleep(0.02)
    assert supervisor.is_running("demo") is False


@pytest.mark.asyncio
async def test_runtime_enable_disable_strategy_starts_and_stops_named_task():
    telemetry = DummyTelemetry()
    supervisor = TaskSupervisor(telemetry)

    async def loop_forever():
        try:
            while True:
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            raise

    engine = MagicMock()
    engine._enabled = set()
    engine.market_loop = MagicMock(price_feed_loop=AsyncMock(), capital_monitor_loop=AsyncMock())
    engine.liq_scanner = MagicMock(start=AsyncMock())
    engine.strategy_loop = MagicMock(
        arb_scan_loop=AsyncMock(),
        mev_loop=loop_forever,
        gmx_loop=AsyncMock(),
        xchain_loop=AsyncMock(),
        yield_loop=AsyncMock(),
    )
    engine.execution_loop = MagicMock(
        profit_collect_loop=AsyncMock(),
        scaling_loop=AsyncMock(),
        nonce_resync_loop=AsyncMock(),
    )
    engine.reporting_loop = MagicMock(hud_state_loop=AsyncMock(), health_server=AsyncMock())
    engine.build_upgrade_tasks = MagicMock(return_value=[])
    engine.ensure_advanced_strategy = AsyncMock()
    available = {"mev_backrun": True, "gmx_funding": False, "cross_chain": False, "yield": False}
    engine.is_strategy_runtime_available = lambda name: available.get(name, False)

    runtime = RuntimeComponent(engine, supervisor)
    await runtime.enable_strategy("mev_backrun")
    await asyncio.sleep(0.02)
    assert "mev_backrun" in engine._enabled
    assert engine.ensure_advanced_strategy.await_count == 1
    assert supervisor.is_running("mev") is True

    runtime.disable_strategy("mev_backrun")
    await asyncio.sleep(0.02)
    assert "mev_backrun" not in engine._enabled
    assert supervisor.is_running("mev") is False
