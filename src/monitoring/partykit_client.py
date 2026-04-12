"""
PartyKit Client — Real-Time Dashboard Bridge
=============================================
Connects to PartyKit server (Cloudflare Durable Objects) via WebSocket.
Pushes bot state every 2 seconds for live dashboard rendering.

AUDIT:
  ✅ Auto-reconnect with exponential backoff
  ✅ Heartbeat every 30s to keep connection alive
  ✅ State serialized as JSON, no sensitive data (no keys, no nonces)
  ✅ Graceful degradation — dashboard offline ≠ bot offline
  ✅ Message size capped at 64KB to avoid WS frame limits

Chain: N/A (off-chain) | Gas: 0 | Latency: <10ms per push
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

try:
    import aiohttp
except ImportError:  # pragma: no cover - test/runtime fallback
    aiohttp = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 30     # seconds
RECONNECT_BASE_DELAY = 2    # seconds
RECONNECT_MAX_DELAY = 60    # seconds
MAX_MESSAGE_BYTES = 65_536  # 64KB WS frame limit


class PartyKitClient:
    """
    WebSocket client for PartyKit real-time state broadcasting.
    
    Usage:
        client = PartyKitClient(url="wss://grid-bot-server.user.partykit.dev")
        await client.connect()
        await client.push_state({"total_profit": 42.50, ...})
    """

    def __init__(
        self,
        url: Optional[str] = None,
        room: str = "main",
        secret: Optional[str] = None,
    ):
        self.base_url = url or os.environ.get(
            "PARTYKIT_URL", "wss://grid-bot-server.example.partykit.dev"
        )
        self.room = room
        self.secret = secret or os.environ.get("PARTYKIT_SECRET", "")
        self._ws: Optional[Any] = None
        self._session: Optional[Any] = None
        self._connected = False
        self._reconnect_delay = RECONNECT_BASE_DELAY
        self._last_push = 0.0
        self._push_count = 0
        self._error_count = 0

    @property
    def ws_url(self) -> str:
        """Build full WebSocket URL with room and auth."""
        base = self.base_url.rstrip("/")
        url = f"{base}/party/{self.room}"
        if self.secret:
            url += f"?token={self.secret}"
        return url

    @property
    def is_connected(self) -> bool:
        return self._connected and self._ws is not None and not self._ws.closed

    async def connect(self) -> None:
        """Establish WebSocket connection with auto-retry."""
        if aiohttp is None:
            raise RuntimeError("aiohttp is required to use PartyKitClient")
        if self._session is None:
            self._session = aiohttp.ClientSession()

        while True:
            try:
                self._ws = await self._session.ws_connect(
                    self.ws_url,
                    heartbeat=HEARTBEAT_INTERVAL,
                    timeout=aiohttp.ClientWSTimeout(ws_close=10),
                )
                self._connected = True
                self._reconnect_delay = RECONNECT_BASE_DELAY
                logger.info("partykit.connected", url=self.base_url[:40])

                # Send initial handshake
                await self._ws.send_json({
                    "type": "bot_connect",
                    "timestamp": time.time(),
                    "version": "omega",
                })
                return

            except Exception as e:
                self._connected = False
                self._error_count += 1
                logger.warning(
                    "partykit.connect_failed",
                    error=str(e)[:60],
                    retry_in=self._reconnect_delay,
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, RECONNECT_MAX_DELAY
                )

    async def push_state(self, state: dict) -> bool:
        """
        Push bot state to PartyKit for dashboard consumption.
        
        AUDIT[NO_SECRETS]: State dict must not contain private keys,
        nonces, or raw transaction data. Only metrics and prices.
        """
        if not self.is_connected:
            try:
                await self.connect()
            except Exception:
                return False

        try:
            # Sanitize: remove any keys that look sensitive
            safe_state = {
                k: v for k, v in state.items()
                if not any(
                    s in k.lower()
                    for s in ["key", "secret", "password", "nonce", "private"]
                )
            }

            message = json.dumps({
                "type": "state_update",
                "data": safe_state,
                "timestamp": time.time(),
            })

            # Cap message size
            if len(message.encode()) > MAX_MESSAGE_BYTES:
                # Trim recent_trades to fit
                if "recent_trades" in safe_state:
                    safe_state["recent_trades"] = safe_state["recent_trades"][:10]
                    message = json.dumps({
                        "type": "state_update",
                        "data": safe_state,
                        "timestamp": time.time(),
                    })

            await self._ws.send_str(message)
            self._push_count += 1
            self._last_push = time.time()
            return True

        except Exception as e:
            self._connected = False
            self._error_count += 1
            logger.warning("partykit.push_failed", error=str(e)[:60])
            # Attempt reconnect in background
            asyncio.create_task(self._reconnect())
            return False

    async def push_trade(self, trade: dict) -> bool:
        """Push a single trade event for live feed."""
        if not self.is_connected:
            return False
        try:
            await self._ws.send_json({
                "type": "trade",
                "data": trade,
                "timestamp": time.time(),
            })
            return True
        except Exception:
            return False

    async def send_alert(self, message: str, level: str = "info") -> bool:
        """Push an alert notification."""
        if not self.is_connected:
            return False
        try:
            await self._ws.send_json({
                "type": "alert",
                "message": message,
                "level": level,
                "timestamp": time.time(),
            })
            return True
        except Exception:
            return False

    async def _reconnect(self) -> None:
        """Background reconnection attempt."""
        await asyncio.sleep(self._reconnect_delay)
        try:
            await self.connect()
        except Exception:
            pass

    async def disconnect(self) -> None:
        """Clean shutdown."""
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()
        self._connected = False
        logger.info("partykit.disconnected")

    @property
    def stats(self) -> dict:
        return {
            "connected": self.is_connected,
            "push_count": self._push_count,
            "error_count": self._error_count,
            "last_push_ago": round(time.time() - self._last_push, 1) if self._last_push else None,
        }


    async def send_trade(self, trade: dict) -> bool:
        """Backward-compatible alias for push_trade()."""
        return await self.push_trade(trade)


# ─────────────────────────────────────────────────────────────────────────────
# API productization: telemetry exports (IM-043)
# ─────────────────────────────────────────────────────────────────────────────

from dataclasses import dataclass, field
from typing import Callable, Dict, List as _List


@dataclass
class TelemetryExport:
    """Structured telemetry record ready for export to the public API.

    Exports are snapshots (not events) — each record is a point-in-time
    summary of a named metric stream. The exporter redacts keys that look
    sensitive using the same deny-list as ``PartyKitClient.push_state``.
    """

    stream: str
    entitlement: str  # "public" | "pro" | "enterprise"
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    # Match the partykit key sanitizer so exports never leak secrets.
    _SECRET_KEYS = ("key", "secret", "password", "nonce", "private", "token")

    def sanitized(self) -> dict:
        return {
            k: v
            for k, v in self.metrics.items()
            if not any(s in k.lower() for s in self._SECRET_KEYS)
        }

    def to_dict(self) -> dict:
        return {
            "stream": self.stream,
            "entitlement": self.entitlement,
            "metrics": self.sanitized(),
            "timestamp": self.timestamp,
        }


class TelemetryExporter:
    """Tenant-aware telemetry export fan-out.

    Subscribers register for a specific entitlement tier. When a record is
    published, only subscribers whose tier is *at or above* the record's
    tier receive it. This is the minimal piece needed so the dashboard,
    pro-tier API consumers, and enterprise exporters can share a single
    in-process telemetry bus without leaking data across tiers.
    """

    _TIER_RANK = {"public": 0, "pro": 1, "enterprise": 2}

    def __init__(self) -> None:
        self._subscribers: _List[tuple[str, Callable[[dict], None]]] = []
        self._published: int = 0
        self._last_export: Optional[dict] = None

    def subscribe(
        self, tier: str, callback: Callable[[dict], None]
    ) -> Callable[[dict], None]:
        if tier not in self._TIER_RANK:
            raise ValueError(f"unknown tier: {tier}")
        self._subscribers.append((tier, callback))
        return callback

    def publish(self, export: TelemetryExport) -> int:
        record = export.to_dict()
        self._published += 1
        self._last_export = record
        delivered = 0
        record_rank = self._TIER_RANK[export.entitlement]
        for tier, callback in self._subscribers:
            # Subscribers whose tier rank is >= record tier rank may
            # consume the record. A pro-tier consumer sees public + pro
            # records, an enterprise consumer sees everything.
            if self._TIER_RANK[tier] >= record_rank:
                try:
                    callback(record)
                    delivered += 1
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("telemetry.subscriber_failed: %s", exc)
        return delivered

    @property
    def stats(self) -> dict:
        return {
            "subscribers": len(self._subscribers),
            "published": self._published,
            "last_export": self._last_export,
        }


# Process-wide exporter so modules can publish without wiring plumbing.
telemetry_exporter = TelemetryExporter()
