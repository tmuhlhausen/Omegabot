from src.predictive.market_intel import MarketIntelFeatures, MarketIntelligenceHub


def test_score_features_is_deterministic_for_identical_input():
    hub = MarketIntelligenceHub()
    features = MarketIntelFeatures(
        ret_1m=0.018,
        spread_bps=7.0,
        depth_imbalance=0.35,
        gas_gwei=12.0,
        latency_ms=45.0,
    )

    scores = [hub.score_features(features) for _ in range(5)]
    assert scores == [scores[0]] * 5


def test_score_features_clips_and_stays_in_expected_range():
    hub = MarketIntelligenceHub()
    extreme = MarketIntelFeatures(
        ret_1m=5.0,
        spread_bps=10_000.0,
        depth_imbalance=999.0,
        gas_gwei=10_000.0,
        latency_ms=1_000_000.0,
    )

    score = hub.score_features(extreme)
    assert 0.0 <= score <= 1.0


def test_identical_hubs_return_identical_scores_for_same_features():
    f = MarketIntelFeatures(
        ret_1m=0.01,
        spread_bps=9.0,
        depth_imbalance=-0.15,
        gas_gwei=30.0,
        latency_ms=80.0,
    )

    hub_a = MarketIntelligenceHub()
    hub_b = MarketIntelligenceHub()

    assert hub_a.score_features(f) == hub_b.score_features(f)
