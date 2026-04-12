"""
Platform Reporter — Unified Trade Reporting Pipeline
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Optional, List

try:
    import aiohttp
except ImportError:  # pragma: no cover - test/runtime fallback
    aiohttp = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    strategy: str
    chain: str
    gross_usd: float
    gas_usd: float
    net_usd: float
    tx_hash: str
    token_symbol: str
    token_price: float
    success: bool
    latency_ms: float
    pair: str = ""
    block_number: int = 0
    timestamp: float = field(default_factory=time.time)
    trade_id: str = ""

    @property
    def user_usd(self) -> float:
        return self.net_usd * 0.25

    @property
    def platform_usd(self) -> float:
        return self.net_usd * 0.75

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "strategy": self.strategy,
            "chain": self.chain,
            "gross_usd": round(self.gross_usd, 6),
            "gas_usd": round(self.gas_usd, 6),
            "net_usd": round(self.net_usd, 6),
            "user_usd": round(self.user_usd, 6),
            "platform_usd": round(self.platform_usd, 6),
            "tx_hash": self.tx_hash,
            "token_symbol": self.token_symbol,
            "token_price": self.token_price,
            "success": self.success,
            "latency_ms": round(self.latency_ms, 1),
            "pair": self.pair,
            "block_number": self.block_number,
            "timestamp": self.timestamp,
        }


class PlatformReporter:
    def __init__(
        self,
        vault_client=None,
        http_session: Optional[aiohttp.ClientSession] = None,
        api_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ):
        self.vault_client = vault_client
        self._session = http_session
        self._api_url = api_url or os.environ.get("PLATFORM_API_URL", "")
        self._bot_api_token = bot_token or os.environ.get("BOT_API_TOKEN", "")
        self._tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._tg_chat_id = telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

        self._trades_reported = 0
        self._total_gross = 0.0
        self._total_gas = 0.0
        self._api_errors = 0
        self._vault_deposits = 0

        self._queue: asyncio.Queue[TradeResult] = asyncio.Queue(maxsize=2000)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

        self._batch_size = int(os.environ.get("REPORT_BATCH_SIZE", "25"))
        self._batch_flush_interval_s = float(os.environ.get("REPORT_BATCH_INTERVAL_S", "2"))
        self._max_retries = int(os.environ.get("REPORT_API_MAX_RETRIES", "3"))

    async def start(self) -> None:
        if aiohttp is None:
            raise RuntimeError("aiohttp is required to start PlatformReporter")
        if self._session is None:
            self._session = aiohttp.ClientSession()
        self._running = True
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())
        logger.info("reporter.started")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("reporter.stopped", trades=self._trades_reported)

    async def report_trade(self, result: TradeResult) -> None:
        self._trades_reported += 1
        self._total_gross += result.gross_usd
        self._total_gas += result.gas_usd

        if self._running:
            try:
                self._queue.put_nowait(result)
            except asyncio.QueueFull:
                self._api_errors += 1
                logger.warning("reporter.queue_full")

        if self.vault_client and result.net_usd > 0.50:
            asyncio.create_task(self._deposit_to_vault(result))

        if result.gross_usd > 5.0 and self._tg_token:
            asyncio.create_task(self._notify_telegram(result))

    async def _worker(self) -> None:
        batch: list[TradeResult] = []
        while self._running:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=self._batch_flush_interval_s)
                batch.append(item)
                if len(batch) >= self._batch_size:
                    await self._flush_batch(batch)
                    batch.clear()
            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch.clear()
            except asyncio.CancelledError:
                if batch:
                    await self._flush_batch(batch)
                raise

    async def _flush_batch(self, trades: List[TradeResult]) -> None:
        for trade in trades:
            await self._report_to_api(trade)

    async def _report_to_api(self, result: TradeResult) -> None:
        if not self._api_url or not self._bot_api_token:
            return

        url = f"{self._api_url.rstrip('/')}/internal/trade"
        payload = result.to_dict()

        for attempt in range(self._max_retries + 1):
            try:
                async with self._session.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._bot_api_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        return
                    self._api_errors += 1
            except Exception:
                self._api_errors += 1

            if attempt < self._max_retries:
                delay = min(5.0, (2 ** attempt) + random.random())
                await asyncio.sleep(delay)

    async def _deposit_to_vault(self, result: TradeResult) -> None:
        try:
            if hasattr(self.vault_client, "deposit_profit"):
                await self.vault_client.deposit_profit(
                    amount_usd=result.net_usd,
                    token=result.token_symbol,
                    tx_hash=result.tx_hash,
                )
                self._vault_deposits += 1
        except Exception as e:
            logger.warning("reporter.vault_deposit_failed", error=str(e)[:60])

    async def _notify_telegram(self, result: TradeResult) -> None:
        if not self._tg_token or not self._tg_chat_id:
            return

        text = (
            f"● *{result.strategy.upper()}*\n"
            f"Net: ${result.net_usd:.2f}\n"
            f"Trade: `{(result.trade_id or result.tx_hash)[:18]}...`"
        )
        try:
            url = f"https://api.telegram.org/bot{self._tg_token}/sendMessage"
            async with self._session.post(
                url,
                json={"chat_id": self._tg_chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=aiohttp.ClientTimeout(total=5),
            ):
                return
        except Exception:
            return

    @property
    def stats(self) -> dict:
        return {
            "trades_reported": self._trades_reported,
            "total_gross": round(self._total_gross, 4),
            "total_gas": round(self._total_gas, 4),
            "total_net": round(self._total_gross - self._total_gas, 4),
            "api_errors": self._api_errors,
            "vault_deposits": self._vault_deposits,
            "queue_depth": self._queue.qsize(),
        }


def init_reporter(vault_client=None, http_session=None) -> PlatformReporter:
    return PlatformReporter(vault_client=vault_client, http_session=http_session)


# ─────────────────────────────────────────────────────────────────────────────
# Reliability scorecards (IM-036)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ReliabilityScorecard:
    """Rolling SLO attainment record for a single module.

    ``slo_error_budget_pct`` is the maximum fraction of failing samples
    tolerated before the module is flagged as *breached*. A window of
    recent samples is kept so the controller can recover as the module
    stabilizes.
    """

    module: str
    slo_error_budget_pct: float = 0.01  # 99% success budget
    window: int = 200
    samples: List[bool] = field(default_factory=list)
    total_ok: int = 0
    total_err: int = 0

    def record(self, success: bool) -> None:
        self.samples.append(bool(success))
        if len(self.samples) > self.window:
            # Drop the oldest sample so the rolling window stays bounded.
            dropped = self.samples.pop(0)
            if dropped:
                self.total_ok = max(0, self.total_ok - 1)
            else:
                self.total_err = max(0, self.total_err - 1)
        if success:
            self.total_ok += 1
        else:
            self.total_err += 1

    @property
    def samples_seen(self) -> int:
        return len(self.samples)

    @property
    def error_rate(self) -> float:
        n = len(self.samples)
        if n == 0:
            return 0.0
        return sum(1 for s in self.samples if not s) / n

    @property
    def success_rate(self) -> float:
        return 1.0 - self.error_rate

    @property
    def breached(self) -> bool:
        # Don't flag on <10 samples — too noisy to be meaningful.
        if len(self.samples) < 10:
            return False
        return self.error_rate > self.slo_error_budget_pct

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "samples_seen": self.samples_seen,
            "success_rate": round(self.success_rate, 4),
            "error_rate": round(self.error_rate, 4),
            "slo_error_budget_pct": self.slo_error_budget_pct,
            "breached": self.breached,
            "total_ok": self.total_ok,
            "total_err": self.total_err,
        }


class ScorecardRegistry:
    """Registry of ReliabilityScorecards keyed by module name.

    Production wiring: each long-running module calls ``record(module, ok)``
    after every operation, and the platform reporter publishes ``summary()``
    on its periodic flush. The ``breached`` flag is used by the release gate
    + HUD so SREs see policy violations in the same feed as trades.
    """

    def __init__(self) -> None:
        self._cards: dict[str, ReliabilityScorecard] = {}

    def register(
        self,
        module: str,
        *,
        slo_error_budget_pct: float = 0.01,
        window: int = 200,
    ) -> ReliabilityScorecard:
        card = ReliabilityScorecard(
            module=module,
            slo_error_budget_pct=slo_error_budget_pct,
            window=window,
        )
        self._cards[module] = card
        return card

    def record(self, module: str, success: bool) -> ReliabilityScorecard:
        card = self._cards.get(module)
        if card is None:
            card = self.register(module)
        card.record(success)
        return card

    def get(self, module: str) -> Optional[ReliabilityScorecard]:
        return self._cards.get(module)

    def breached(self) -> List[str]:
        return [name for name, card in self._cards.items() if card.breached]

    def summary(self) -> dict:
        return {name: card.to_dict() for name, card in self._cards.items()}


# Module-level singleton so any subsystem can publish reliability samples
# without plumbing the registry through the engine constructor.
scorecards = ScorecardRegistry()
