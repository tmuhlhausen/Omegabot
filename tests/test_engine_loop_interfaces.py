import pytest
from unittest.mock import AsyncMock

from src.core.engine_components.bootstrap import BootstrapComponent
from src.core.engine_components.market_loop import MarketLoopComponent
from src.core.engine_components.strategy_loop import StrategyLoopComponent
from src.core.engine_components.execution_loop import ExecutionLoopComponent
from src.core.engine_components.reporting_loop import ReportingLoopComponent
from src.core.engine_components.health.supervisor import TaskSupervisor, RestartPolicy
from src.core.engine_components.telemetry import ErrorTelemetry


class DummyEngine:
    def __init__(self):
        self._initialize_impl = AsyncMock()
        self._init_advanced_strategies_impl = AsyncMock()
        self._price_feed_loop_impl = AsyncMock()
        self._capital_monitor_loop_impl = AsyncMock()
        self._arb_scan_loop_impl = AsyncMock()
        self._mev_loop_impl = AsyncMock()
        self._gmx_loop_impl = AsyncMock()
        self._xchain_loop_impl = AsyncMock()
        self._yield_loop_impl = AsyncMock()
        self._profit_collect_loop_impl = AsyncMock()
        self._nonce_resync_loop_impl = AsyncMock()
        self._scaling_loop_impl = AsyncMock()
        self._hud_state_loop_impl = AsyncMock()
        self._health_server_impl = AsyncMock()


@pytest.mark.asyncio
async def test_bootstrap_component_interface():
    engine = DummyEngine()
    c = BootstrapComponent(engine)
    await c.initialize()
    await c.init_advanced_strategies()
    engine._initialize_impl.assert_awaited_once()
    engine._init_advanced_strategies_impl.assert_awaited_once()


@pytest.mark.asyncio
async def test_market_component_interface():
    engine = DummyEngine()
    c = MarketLoopComponent(engine)
    await c.price_feed_loop()
    await c.capital_monitor_loop()
    engine._price_feed_loop_impl.assert_awaited_once()
    engine._capital_monitor_loop_impl.assert_awaited_once()


@pytest.mark.asyncio
async def test_strategy_component_interface():
    engine = DummyEngine()
    c = StrategyLoopComponent(engine)
    await c.arb_scan_loop()
    await c.mev_loop()
    await c.gmx_loop()
    await c.xchain_loop()
    await c.yield_loop()
    engine._arb_scan_loop_impl.assert_awaited_once()
    engine._mev_loop_impl.assert_awaited_once()
    engine._gmx_loop_impl.assert_awaited_once()
    engine._xchain_loop_impl.assert_awaited_once()
    engine._yield_loop_impl.assert_awaited_once()


@pytest.mark.asyncio
async def test_execution_component_interface():
    engine = DummyEngine()
    c = ExecutionLoopComponent(engine)
    await c.profit_collect_loop()
    await c.nonce_resync_loop()
    await c.scaling_loop()
    engine._profit_collect_loop_impl.assert_awaited_once()
    engine._nonce_resync_loop_impl.assert_awaited_once()
    engine._scaling_loop_impl.assert_awaited_once()


@pytest.mark.asyncio
async def test_reporting_component_interface():
    engine = DummyEngine()
    c = ReportingLoopComponent(engine)
    await c.hud_state_loop()
    await c.health_server()
    engine._hud_state_loop_impl.assert_awaited_once()
    engine._health_server_impl.assert_awaited_once()


@pytest.mark.asyncio
async def test_supervisor_restart_policy_budget():
    telemetry = ErrorTelemetry()
    sup = TaskSupervisor(telemetry)
    attempts = {"count": 0}

    async def flaky_loop():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient")

    task = sup.supervise("flaky", flaky_loop, RestartPolicy(max_restarts=4, backoff_seconds=0.0, failure_budget=4))
    await task
    assert attempts["count"] == 3
    assert telemetry.snapshot().get("flaky:RuntimeError", 0) == 2
