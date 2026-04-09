from src.core.feature_flags import FeatureFlags
from src.risk.autonomous_risk_brain import AutonomousRiskBrain, RiskSnapshot
from src.simulation.digital_twin import DigitalTwin, ReplayEvent


def test_feature_flags_defaults():
    flags = FeatureFlags()
    data = flags.to_dict()
    assert "digital_twin" in data
    assert "autonomous_risk" in data


def test_autonomous_risk_brain_modes():
    brain = AutonomousRiskBrain()
    assert brain.classify(RiskSnapshot(0.1, 1.0, 0.1, 20)) == "NORMAL"
    assert brain.classify(RiskSnapshot(0.7, 30.0, 0.8, 500)) in {"DEFENSIVE", "CRISIS"}


def test_digital_twin_replay():
    twin = DigitalTwin()
    events = [ReplayEvent(ts=float(i), symbol="WETH", price=1000 + i, signal=0.3) for i in range(10)]
    result = twin.run(events)
    assert result.trades > 0
