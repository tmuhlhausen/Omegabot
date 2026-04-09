from src.predictive.formula_provenance import FormulaProvenanceLedger
from src.strategies.route_optimizer import RouteOptimizer, RouteOption
from src.governance.policy_engine import PolicyEngine, PolicyContext


def test_formula_provenance_top():
    ledger = FormulaProvenanceLedger()
    ledger.upsert("a:1", "bot", 0.4)
    ledger.upsert("b:1", "bot", 0.8)
    assert ledger.top(1)[0].key == "b:1"


def test_route_optimizer_choose():
    opt = RouteOptimizer()
    winner = opt.choose([
        RouteOption("r1", 0.4, 1.2, 120, 0.95),
        RouteOption("r2", 0.2, 0.7, 200, 0.96),
    ])
    assert winner.name in {"r1", "r2"}


def test_policy_engine_blocks_crisis_large():
    pe = PolicyEngine()
    ok, reason = pe.evaluate(PolicyContext(operation="trade", risk_mode="CRISIS", amount_usd=500))
    assert ok is False
    assert reason == "blocked_in_crisis"
