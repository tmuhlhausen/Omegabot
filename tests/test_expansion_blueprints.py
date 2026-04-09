from src.predictive.formula_engine import build_default_formula_engine
from src.strategies.expansion_router import ExpansionRouter, ExpansionState
from src.core.asset_universe import AssetUniverse, AssetProfile


def test_formula_engine_tiers():
    eng = build_default_formula_engine()
    v = eng.evaluate("micro_momentum:1.0.0", {"ofi": 0.5, "ret_1m": 0.1}, tier=0)
    assert isinstance(v, float)
    assert "micro_momentum:1.0.0" in eng.list_available(0)


def test_expansion_router_unlocks():
    router = ExpansionRouter()
    assert router.allowed(ExpansionState(100))["tier"] == 0
    assert router.allowed(ExpansionState(700))["tier"] == 1
    assert router.allowed(ExpansionState(7000))["tier"] == 2


def test_asset_universe_taxonomy():
    u = AssetUniverse()
    u.add_or_update(AssetProfile(symbol="PENDLE", category="yield", max_exposure_pct=0.08))
    assert "PENDLE" in u.active_symbols()
    assert any(a.symbol == "PENDLE" for a in u.by_category("yield"))
