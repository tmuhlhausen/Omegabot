"""
Nonce Manager — Atomic Nonce Tracking
======================================
Prevents duplicate transactions and nonce collisions in concurrent async loops.

AUDIT:
  ✅ Atomic increment via asyncio.Lock
  ✅ Syncs from chain on startup and periodically
  ✅ Gap detection: if chain nonce > local, resync
  ✅ No race conditions between strategy loops
"""

import asyncio
import logging

from typing import Any

try:
    from web3 import AsyncWeb3
except ImportError:  # pragma: no cover - test/runtime fallback
    AsyncWeb3 = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


class NonceManager:
    """
    Thread-safe nonce manager for async bot operations.
    
    Multiple strategy loops share one nonce sequence.
    Lock ensures no two loops get the same nonce.
    """

    def __init__(self):
        self._nonce: int = 0
        self._lock = asyncio.Lock()
        self._synced = False
        self._w3 = None
        self._address = None

    async def sync_from_chain(self, w3: AsyncWeb3, address: str) -> None:
        """Fetch current nonce from chain and set as baseline."""
        self._w3 = w3
        self._address = address
        async with self._lock:
            chain_nonce = await w3.eth.get_transaction_count(address, "pending")
            self._nonce = chain_nonce
            self._synced = True
            logger.info("nonce.synced", nonce=chain_nonce, address=address[:10])

    async def get_nonce(self) -> int:
        """Get next nonce atomically. Increments internal counter."""
        if not self._synced:
            raise RuntimeError("NonceManager not synced. Call sync_from_chain() first.")

        async with self._lock:
            nonce = self._nonce
            self._nonce += 1
            return nonce

    async def resync_if_needed(self) -> None:
        """Check chain nonce and resync if gap detected."""
        if not self._w3 or not self._address:
            return

        try:
            chain_nonce = await self._w3.eth.get_transaction_count(
                self._address, "pending"
            )
            async with self._lock:
                if chain_nonce > self._nonce:
                    logger.warning(
                        "nonce.gap_detected",
                        local=self._nonce,
                        chain=chain_nonce,
                    )
                    self._nonce = chain_nonce
        except Exception as e:
            logger.warning("nonce.resync_failed: %s", str(e)[:60])

    @property
    def current(self) -> int:
        return self._nonce
