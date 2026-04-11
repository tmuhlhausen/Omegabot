from pathlib import Path

from src.strategies.route_optimizer import (
    CalibrationSample,
    FeatureScales,
    RiskMode,
    RouteOptimizer,
    RouteOptimizerConfig,
    RouteOption,
)


def test_route_optimizer_normalization_and_risk_profiles(tmp_path: Path):
    opt = RouteOptimizer(
        RouteOptimizerConfig(
            scales=FeatureScales(slippage_pct=1.0, fee_usd=10.0, latency_ms=500.0, reliability_gap=1.0)
        )
    )
    r1 = RouteOption("ex_a", 0.3, 1.5, 200, 0.99)
    r2 = RouteOption("ex_b", 0.2, 0.8, 190, 0.80)

    normal = opt.choose([r1, r2], risk_mode=RiskMode.NORMAL)
    crisis = opt.choose([r1, r2], risk_mode=RiskMode.CRISIS)

    assert normal.name in {"ex_a", "ex_b"}
    assert crisis.name == "ex_a"


def test_feedback_loop_and_persistence(tmp_path: Path):
    opt = RouteOptimizer()
    before = opt.score(RouteOption("dex_x", 0.2, 1.0, 150, 0.95), RiskMode.NORMAL)
    opt.update_execution_feedback("dex_x", success=False, quality_score=0.2)
    after = opt.score(RouteOption("dex_x", 0.2, 1.0, 150, 0.95), RiskMode.NORMAL)

    assert after > before

    coeffs = tmp_path / "route_optimizer_coeffs.json"
    opt.persist_coefficients(coeffs)
    restored = RouteOptimizer()
    restored.load_coefficients(coeffs)
    restored_score = restored.score(RouteOption("dex_x", 0.2, 1.0, 150, 0.95), RiskMode.NORMAL)
    assert restored_score == after


def test_offline_calibration_persists_tuned_coefficients(tmp_path: Path):
    opt = RouteOptimizer()
    tuned = opt.calibrate_offline(
        [
            CalibrationSample(RiskMode.NORMAL, 0.4, 1.0, 180.0, 0.97, realized_cost=1.5),
            CalibrationSample(RiskMode.NORMAL, 0.2, 0.8, 120.0, 0.99, realized_cost=0.6),
            CalibrationSample(RiskMode.DEFENSIVE, 0.5, 0.7, 220.0, 0.92, realized_cost=1.8),
        ],
        persist_path=tmp_path / "calibration.json",
    )

    assert set(tuned.keys()) == {"slippage", "fee", "latency", "reliability"}
    assert abs(sum(tuned.values()) - 1.0) < 1e-9
    assert (tmp_path / "calibration.json").exists()
