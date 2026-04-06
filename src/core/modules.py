"""
Core Modules — CircuitBreaker, ScalingFSM, RPCManager, BotScalingState
Sourced from project knowledge. Engine imports these directly.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

logger = logging.getLogger(__name__)

FREE_RPCS = {
    "arbitrum": [
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum.llamarpc.com",
        "https://rpc.ankr.com/arbitrum",
        "https://arbitrum-one.publicnode.com",
    ],
    "base": [
        "https://mainnet.base.org",
        "https://base.llamarpc.com",
        "https://rpc.ankr.com/base",
    ],
    "polygon": [
        "https://polygon-rpc.com",
        "https://polygon.llamarpc.com",
        "https://rpc.ankr.com/polygon",
    ],
    "optimism": [
        "https://mainnet.optimism.io",
        "https://optimism.llamarpc.com",
    ],
    "bsc": [
        "https://bsc-dataseed.binance.org",
        "https://rpc.ankr.com/bsc",
    ],
}

CHAIN_EXPANSION_ORDER = ["arbitrum", "base", "polygon", "optimism", "bsc", "ethereum"]
CHAIN_PROFIT_THRESHOLDS = {1: 500, 2: 2000, 3: 5000, 4: 10000, 5: 25000}
RPC_UPGRADE = {
    "free": {"profit_required": 50, "latency_ms": 15},
    "alchemy_growth": {"profit_required": 500, "latency_ms": 10},
}
MAX_PAIRS_BY_CHAINS = {1: 3, 2: 6, 3: 12, 4: 20, 5: 30, 6: 50}


@dataclass
class BotScalingState:
    total_profit_usd: float
    available_profit_usd: float
    current_borrow_usd: float
    active_chains: list
    active_pairs: list
    rpc_tier: str
    avg_rpc_latency_ms: float


class CircuitBreaker:
    """Auto-halts trading on dangerous conditions."""
    MAX_LOSS_USD = 50.0
    MAX_FAILURES = 3
    COOLDOWN_S = 120.0

    def __init__(self):
        self._paused = False
        self._pause_reason = ""
        self._pause_time = 0.0
        self._failures = 0
        self._loss_usd = 0.0

    def pause(self, reason: str) -> None:
        self._paused = True
        self._pause_reason = reason
        self._pause_time = time.time()
        logger.critical("CIRCUIT_BREAKER_PAUSED: %s", reason)

    def resume(self) -> None:
        self._paused = False
        self._pause_reason = ""
        self._failures = 0
        logger.info("CIRCUIT_BREAKER_RESUMED")

    async def check_and_maybe_pause(self) -> bool:
        if self._paused:
            if time.time() - self._pause_time > self.COOLDOWN_S:
                self.resume()
                return True
            return False
        return True

    def record_failure(self, loss_usd: float = 0.0) -> None:
        self._failures += 1
        self._loss_usd += loss_usd
        if self._failures >= self.MAX_FAILURES:
            self.pause(f"max_failures_{self._failures}")
        if self._loss_usd >= self.MAX_LOSS_USD:
            self.pause(f"max_loss_${self._loss_usd:.0f}")

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def stats(self) -> dict:
        return {
            "paused": self._paused,
            "reason": self._pause_reason,
            "failures": self._failures,
            "loss_usd": round(self._loss_usd, 2),
        }


class RPCManager:
    """Multi-endpoint RPC pool with latency-based routing."""

    def __init__(self):
        self._connections: dict = {}
        self._latencies: dict = {}

    async def initialize(self) -> None:
        for chain, urls in FREE_RPCS.items():
            self._connections[chain] = [
                AsyncWeb3(AsyncHTTPProvider(url, request_kwargs={"timeout": 5}))
                for url in urls
            ]
        await self._benchmark_all()

    async def get_fastest_rpc(self, chain: str) -> AsyncWeb3:
        conns = self._connections.get(chain, [])
        if not conns:
            raise ValueError(f"No RPC for chain: {chain}")
        return min(
            conns,
            key=lambda w3: self._latencies.get(str(w3.provider.endpoint_uri), 9999),
        )

    async def _benchmark_all(self) -> None:
        for chain, conns in self._connections.items():
            for w3 in conns:
                try:
                    t0 = time.perf_counter()
                    await w3.eth.block_number
                    ms = (time.perf_counter() - t0) * 1000
                    self._latencies[str(w3.provider.endpoint_uri)] = ms
                except Exception:
                    self._latencies[str(w3.provider.endpoint_uri)] = 9999

    @property
    def latency_map(self) -> dict:
        return {k[-40:]: round(v, 1) for k, v in self._latencies.items()}


class ScalingFSM:
    """
    Profit reinvestment state machine.
    Evaluates scaling decisions every 5 min in priority order:
      P1: Increase Aave borrow (profit ≥ 10% of borrow + HF ≥ 2.0)
      P2: Chain expansion (profit thresholds per chain count)
      P3: RPC upgrade (latency + profit thresholds)
      P4: Pair expansion (up to tier maximum)
    """

    def __init__(self, aave_client, rpc_manager):
        self.aave = aave_client
        self.rpc = rpc_manager

    async def evaluate_and_execute(self, state: BotScalingState) -> None:
        # P1: Aave borrow increase
        if await self._should_increase_borrow(state):
            await self._increase_borrow(state)
            return

        # P2: Chain expansion
        n = len(state.active_chains)
        threshold = CHAIN_PROFIT_THRESHOLDS.get(n, float("inf"))
        if state.total_profit_usd >= threshold:
            next_chain = CHAIN_EXPANSION_ORDER[min(n, len(CHAIN_EXPANSION_ORDER) - 1)]
            logger.info("SCALING_CHAIN: → %s at $%.0f", next_chain, state.total_profit_usd)
            return

        # P3: RPC upgrade
        rpc_cfg = RPC_UPGRADE.get(state.rpc_tier)
        if (rpc_cfg
                and state.available_profit_usd >= rpc_cfg["profit_required"]
                and state.avg_rpc_latency_ms >= rpc_cfg["latency_ms"]):
            logger.info("SCALING_RPC: upgrade from %s", state.rpc_tier)

    async def _should_increase_borrow(self, state: BotScalingState) -> bool:
        threshold = state.current_borrow_usd * 0.10
        hf = await self.aave.get_health_factor()
        return state.available_profit_usd >= threshold and hf >= 2.0

    async def _increase_borrow(self, state: BotScalingState) -> None:
        deposit_usd = state.available_profit_usd * 0.80
        new_borrow = state.current_borrow_usd * 1.20

        projected = await self.aave.simulate_health_factor(
            additional_collateral_usd=deposit_usd,
            additional_debt_usd=(new_borrow - state.current_borrow_usd),
        )
        if projected >= 1.8:
            await self.aave.supply_usdc(deposit_usd)
            await self.aave.borrow_usdc(new_borrow - state.current_borrow_usd)
            logger.info("SCALING_AAVE: borrow $%.0f→$%.0f", state.current_borrow_usd, new_borrow)
        else:
            logger.warning("SCALING_AAVE_SKIP: projected HF=%.2f", projected)
