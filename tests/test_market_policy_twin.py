from src.governance.policy_engine import ApprovalWorkflow, PolicyConfig, PolicyContext, PolicyEngine, TierThreshold
from src.predictive.market_intel import ChainTelemetry, MarketIntelligenceHub
from src.simulation.digital_twin import DigitalTwin, ReplayEvent


def test_market_intel_signal_fusion_fields():
    hub = MarketIntelligenceHub()
    sig = hub.process_tick(
        "WETH",
        bid=1999.0,
        ask=2001.0,
        trade_imbalance=0.6,
        chain_telemetry=ChainTelemetry(gas_gwei=35.0, pending_txs=55_000, mev_risk=0.35),
    )
    assert sig.regime in {"NORMAL", "BULL", "VOLATILE", "CRISIS", "BEAR"}
    assert -1.0 <= sig.ofi <= 1.0
    assert 0.01 <= sig.kelly_fraction <= 0.25
    assert 0.0 <= sig.chain_stress <= 1.0


def test_policy_engine_tier_and_workflow_decisions():
    pe = PolicyEngine(
        PolicyConfig(
            tiers={
                "default": TierThreshold(max_amount_usd=1_000, crisis_max_amount_usd=150),
                "operator": TierThreshold(max_amount_usd=4_000, crisis_max_amount_usd=500),
            },
            workflows=(ApprovalWorkflow(operation="expand_chain", min_amount_usd=200, approvers_required=2),),
        )
    )

    blocked = pe.evaluate(PolicyContext(operation="trade", risk_mode="CRISIS", amount_usd=200, actor_tier="default"))
    assert blocked == (False, "blocked_in_crisis")

    wf = pe.evaluate(PolicyContext(operation="expand_chain", risk_mode="NORMAL", amount_usd=250, actor_tier="operator"))
    assert wf == (False, "approval_required:2")

    allowed = pe.evaluate(PolicyContext(operation="trade", risk_mode="NORMAL", amount_usd=100, actor_tier="default"))
    assert allowed == (True, "allowed")


def test_digital_twin_replay_deterministic_for_trace():
    twin = DigitalTwin()
    events = [
        ReplayEvent(ts=1_700_000_000 + i, symbol="WETH", price=1000 + i * 2, signal=((i % 4) - 1.5) / 3)
        for i in range(12)
    ]

    result_a = twin.run(events, threshold=0.2, seed=99, strategy="momentum")
    result_b = twin.run(events, threshold=0.2, seed=99, strategy="momentum")

    assert result_a.pnl_usd == result_b.pnl_usd
    assert result_a.trades == result_b.trades
    assert result_a.max_drawdown_pct == result_b.max_drawdown_pct
    assert result_a.metadata["equity_curve"] == result_b.metadata["equity_curve"]
