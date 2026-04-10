"""
NeuralBot OMEGA — Core Test Suite
==================================
Tests for all critical subsystems.
Run: pytest tests/ -v

Uses mocks for Web3, Aave, and external services.
No real blockchain calls. No real money. No real keys.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_w3():
    w3 = AsyncMock()
    w3.eth.gas_price = 100_000_000  # 0.1 gwei
    w3.eth.get_transaction_count = AsyncMock(return_value=0)
    w3.eth.block_number = 250_000_000
    w3.eth.send_raw_transaction = AsyncMock(return_value=b"\x00" * 32)
    w3.eth.wait_for_transaction_receipt = AsyncMock(return_value={"status": 1})
    w3.eth.contract = MagicMock()
    return w3


@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = "0x742d35Cc6634C0532925a3b8D4C9C1BC0a1b5E92"
    account.sign_transaction = MagicMock(return_value=MagicMock(
        raw_transaction=b"\x00" * 100
    ))
    return account


@pytest.fixture
def mock_nonce_mgr():
    nm = AsyncMock()
    nm.get_nonce = AsyncMock(return_value=0)
    nm.sync_from_chain = AsyncMock()
    nm.resync_if_needed = AsyncMock()
    return nm


@pytest.fixture
def mock_aave_state():
    state = MagicMock()
    state.health_factor = 2.5
    state.collateral_usd = 1000.0
    state.debt_usd = 400.0
    state.available_borrow_usd = 250.0
    state.is_critical = False
    state.is_healthy = True
    return state


@pytest.fixture
def mock_aave_client(mock_aave_state):
    client = AsyncMock()
    client.get_account_state = AsyncMock(return_value=mock_aave_state)
    client.get_health_factor = AsyncMock(return_value=2.5)
    return client


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: RiskManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskManager:
    """Tests for src/core/risk_manager.py"""

    def _make_rm(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        from src.core.risk_manager import RiskManager
        return RiskManager(
            w3=mock_w3, account=mock_account,
            nonce_manager=mock_nonce_mgr, aave_client=mock_aave_client,
        )

    @pytest.mark.asyncio
    async def test_clear_trade_allowed(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)
        # Mock gas price
        mock_w3.eth.gas_price = 100_000_000  # 0.1 gwei

        result = await rm.clear_trade(
            strategy="arb", expected_profit=5.0, flash_amount_usd=10000
        )
        assert result.allowed is True
        assert result.reason == "CLEARED"

    @pytest.mark.asyncio
    async def test_clear_trade_blocked_when_paused(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)
        rm.pause("test_pause")

        result = await rm.clear_trade(
            strategy="arb", expected_profit=5.0, flash_amount_usd=10000
        )
        assert result.allowed is False
        assert "PAUSED" in result.reason

    @pytest.mark.asyncio
    async def test_clear_trade_blocked_low_profit(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)
        mock_w3.eth.gas_price = 100_000_000

        result = await rm.clear_trade(
            strategy="arb", expected_profit=0.001, flash_amount_usd=10000
        )
        assert result.allowed is False
        assert "Profit" in result.reason

    def test_record_trade_updates_state(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)

        rm.record_trade(profit_usd=10.0, success=True, strategy="arb")
        assert rm.state.daily_trades == 1
        assert rm.state.consecutive_failures == 0
        assert rm.state.total_profit_usd == 10.0

    def test_consecutive_failures_trigger_pause(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)

        for _ in range(3):
            rm.record_trade(profit_usd=-1.0, success=False, strategy="arb")

        assert rm.state.consecutive_failures == 3

    def test_pause_resume_cycle(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)

        rm.pause("test")
        assert rm.is_paused is True
        assert rm.state.paused is True

        rm.resume()
        assert rm.is_paused is False

    def test_force_pause_alias(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)

        rm.force_pause("emergency")
        assert rm.is_paused is True

        rm.force_resume()
        assert rm.is_paused is False

    def test_price_anomaly_detection(self, mock_w3, mock_account, mock_nonce_mgr, mock_aave_client):
        rm = self._make_rm(mock_w3, mock_account, mock_nonce_mgr, mock_aave_client)

        # Normal price movement
        rm.check_price_anomaly("WETH", 3400)
        rm.check_price_anomaly("WETH", 3410)  # 0.3% — normal
        assert rm.is_paused is False

        # Anomalous price movement (>10%)
        rm.check_price_anomaly("WETH", 3800)  # ~11.4% jump
        assert rm.is_paused is True


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: KeyManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestKeyManager:
    """Tests for src/vault/key_manager.py"""

    def test_load_from_env(self):
        with patch.dict("os.environ", {"PRIVATE_KEY": "0x" + "a" * 64}):
            from src.vault.key_manager import KeyVault
            kv = KeyVault()
            account = kv.load()
            assert account.address.startswith("0x")
            assert len(account.address) == 42

    def test_missing_key_raises(self):
        with patch.dict("os.environ", {"PRIVATE_KEY": ""}, clear=True):
            from src.vault.key_manager import KeyVault
            kv = KeyVault()
            with pytest.raises(EnvironmentError):
                kv.load()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: NonceManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestNonceManager:
    """Tests for src/vault/nonce_manager.py"""

    @pytest.mark.asyncio
    async def test_sync_and_get(self, mock_w3):
        from src.vault.nonce_manager import NonceManager
        nm = NonceManager()

        mock_w3.eth.get_transaction_count = AsyncMock(return_value=42)
        await nm.sync_from_chain(mock_w3, "0x" + "0" * 40)

        nonce = await nm.get_nonce()
        assert nonce == 42

        nonce2 = await nm.get_nonce()
        assert nonce2 == 43  # Incremented

    @pytest.mark.asyncio
    async def test_unsync_raises(self):
        from src.vault.nonce_manager import NonceManager
        nm = NonceManager()

        with pytest.raises(RuntimeError):
            await nm.get_nonce()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: PlatformReporter
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlatformReporter:
    """Tests for src/monitoring/platform_reporter.py"""

    def test_trade_result_split(self):
        from src.monitoring.platform_reporter import TradeResult
        tr = TradeResult(
            strategy="arb", chain="arbitrum",
            gross_usd=10.0, gas_usd=0.5, net_usd=9.5,
            tx_hash="0xabc", token_symbol="USDC",
            token_price=1.0, success=True, latency_ms=15.0,
        )
        assert tr.user_usd == pytest.approx(2.375, rel=0.01)  # 25% of 9.5
        assert tr.platform_usd == pytest.approx(7.125, rel=0.01)  # 75% of 9.5
        assert tr.user_usd + tr.platform_usd == pytest.approx(tr.net_usd, rel=0.01)

    def test_trade_result_to_dict(self):
        from src.monitoring.platform_reporter import TradeResult
        tr = TradeResult(
            strategy="liquidation", chain="arbitrum",
            gross_usd=50.0, gas_usd=1.0, net_usd=49.0,
            tx_hash="0xdef", token_symbol="USDC",
            token_price=1.0, success=True, latency_ms=8.0,
        )
        d = tr.to_dict()
        assert d["strategy"] == "liquidation"
        assert d["user_usd"] == pytest.approx(12.25, rel=0.01)
        assert "tx_hash" in d


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: Advanced Strategies
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvancedStrategies:
    """Tests for strategies/advanced_strategies.py"""

    def test_yield_optimizer_min_capital(self):
        from src.strategies.advanced_strategies import YieldOptimizer
        yo = YieldOptimizer(w3=MagicMock(), account=MagicMock(), risk_mgr=MagicMock())

        # Below minimum
        result = yo.find_best_yield(50.0)
        assert result is None

        # Above minimum
        result = yo.find_best_yield(1000.0)
        assert result is not None
        assert result.apy_total > 0

    def test_cross_chain_bridge_routes(self):
        from src.strategies.advanced_strategies import CrossChainArbStrategy
        assert ("arbitrum", "base") in CrossChainArbStrategy.BRIDGE_ROUTES
        assert ("arbitrum", "polygon") in CrossChainArbStrategy.BRIDGE_ROUTES

    def test_mev_min_swap_threshold(self):
        from src.strategies.advanced_strategies import MIN_BACKRUN_SWAP_USD
        assert MIN_BACKRUN_SWAP_USD == 50_000

    def test_gmx_markets_defined(self):
        from src.strategies.advanced_strategies import GMXFundingStrategy
        assert "ETH-USD" in GMXFundingStrategy.MARKETS
        assert "BTC-USD" in GMXFundingStrategy.MARKETS


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: PartyKitClient
# ═══════════════════════════════════════════════════════════════════════════════

class TestPartyKitClient:
    """Tests for src/monitoring/partykit_client.py"""

    def test_ws_url_construction(self):
        from src.monitoring.partykit_client import PartyKitClient
        pk = PartyKitClient(url="wss://test.partykit.dev", room="main", secret="abc")
        assert "party/main" in pk.ws_url
        assert "token=abc" in pk.ws_url

    def test_not_connected_initially(self):
        from src.monitoring.partykit_client import PartyKitClient
        pk = PartyKitClient()
        assert pk.is_connected is False


# ═══════════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
