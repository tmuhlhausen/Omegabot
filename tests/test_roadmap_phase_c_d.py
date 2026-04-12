"""Unit coverage for remaining roadmap items (Phase C + Phase D).

Covers implementation matrix rows the release-critical gate doesn't track:

- IM-036 Reliability scorecards (Phase D)
- IM-043 API productization + telemetry exports (Phase C)
- IM-045 Plugin framework for external alpha (Phase C)
"""

from __future__ import annotations

import pytest

from src.core.modules import (
    AlphaPlugin,
    AlphaPluginRegistry,
    alpha_plugins as _alpha_plugins,
)
from src.monitoring.partykit_client import (
    TelemetryExport,
    TelemetryExporter,
    telemetry_exporter as _telemetry_exporter,
)
from src.monitoring.platform_reporter import (
    ReliabilityScorecard,
    ScorecardRegistry,
    scorecards as _scorecards,
)


# ─────────────────────────────────────────────────────────────────────────────
# IM-036 Reliability scorecards
# ─────────────────────────────────────────────────────────────────────────────


def test_scorecard_reports_rolling_success_rate():
    card = ReliabilityScorecard(module="router", slo_error_budget_pct=0.05, window=50)
    for _ in range(18):
        card.record(True)
    for _ in range(2):
        card.record(False)

    assert card.samples_seen == 20
    assert card.total_ok == 18
    assert card.total_err == 2
    assert card.error_rate == pytest.approx(0.10)
    assert card.success_rate == pytest.approx(0.90)


def test_scorecard_breaches_when_error_budget_exceeded():
    card = ReliabilityScorecard(module="strategy", slo_error_budget_pct=0.05, window=40)

    # 9 OK + 1 bad = 10% error rate → over a 5% budget → breach.
    for _ in range(9):
        card.record(True)
    card.record(False)

    assert card.breached is True

    # Recover by recording a stream of successes — the window slides and
    # drops the bad sample, clearing the breach.
    for _ in range(40):
        card.record(True)

    assert card.breached is False
    assert card.error_rate == pytest.approx(0.0)


def test_scorecard_requires_minimum_samples_before_flagging():
    # With only a few samples the scorecard should not flag a breach
    # even if every sample fails. Protects against noise on fresh streams.
    card = ReliabilityScorecard(module="bootstrap", slo_error_budget_pct=0.01)
    for _ in range(5):
        card.record(False)
    assert card.breached is False


def test_scorecard_registry_tracks_multiple_modules():
    reg = ScorecardRegistry()
    reg.register("router", slo_error_budget_pct=0.05)
    reg.register("executor", slo_error_budget_pct=0.02)

    # router: clean
    for _ in range(20):
        reg.record("router", True)
    # executor: 5% error rate in a 2% budget → breach
    for _ in range(19):
        reg.record("executor", True)
    for _ in range(1):
        reg.record("executor", False)

    breached = reg.breached()
    assert "executor" in breached
    assert "router" not in breached

    summary = reg.summary()
    assert set(summary.keys()) == {"router", "executor"}
    assert summary["router"]["breached"] is False
    assert summary["executor"]["breached"] is True


def test_scorecard_registry_singleton_exposed_at_module_level():
    # Just make sure the process-wide singleton is a ScorecardRegistry
    # and can be used by other subsystems without wiring.
    assert isinstance(_scorecards, ScorecardRegistry)


# ─────────────────────────────────────────────────────────────────────────────
# IM-043 API productization + telemetry exports
# ─────────────────────────────────────────────────────────────────────────────


def test_telemetry_export_redacts_sensitive_keys():
    export = TelemetryExport(
        stream="trades",
        entitlement="public",
        metrics={
            "gross_usd": 12.5,
            "api_key": "sk-should-not-leak",
            "user_secret": "nope",
            "tx_hash": "0xabc",
            "private_seed": "nope",
            "nonce_value": 42,
        },
    )
    sanitized = export.sanitized()
    assert "gross_usd" in sanitized
    assert "tx_hash" in sanitized
    assert "api_key" not in sanitized
    assert "user_secret" not in sanitized
    assert "private_seed" not in sanitized
    assert "nonce_value" not in sanitized


def test_telemetry_exporter_respects_entitlement_tiers():
    exporter = TelemetryExporter()
    public_records: list[dict] = []
    pro_records: list[dict] = []
    enterprise_records: list[dict] = []

    exporter.subscribe("public", public_records.append)
    exporter.subscribe("pro", pro_records.append)
    exporter.subscribe("enterprise", enterprise_records.append)

    # public record → all three tiers receive it
    exporter.publish(TelemetryExport(stream="health", entitlement="public", metrics={"ok": 1}))
    # pro record → pro + enterprise receive, public does not
    exporter.publish(TelemetryExport(stream="pnl", entitlement="pro", metrics={"pnl": 2.0}))
    # enterprise record → only enterprise
    exporter.publish(
        TelemetryExport(stream="attribution", entitlement="enterprise", metrics={"signal": "x"})
    )

    assert len(public_records) == 1
    assert len(pro_records) == 2
    assert len(enterprise_records) == 3

    assert exporter.stats["published"] == 3
    assert exporter.stats["last_export"]["stream"] == "attribution"


def test_telemetry_exporter_rejects_unknown_tier():
    exporter = TelemetryExporter()
    with pytest.raises(ValueError):
        exporter.subscribe("vip", lambda _r: None)


def test_telemetry_exporter_singleton_exposed_at_module_level():
    assert isinstance(_telemetry_exporter, TelemetryExporter)


# ─────────────────────────────────────────────────────────────────────────────
# IM-045 Plugin framework for external alpha
# ─────────────────────────────────────────────────────────────────────────────


def test_alpha_plugin_registry_invokes_handler_with_context():
    reg = AlphaPluginRegistry()
    reg.register("momentum", lambda ctx: ctx["price"] - ctx["ref"])

    score = reg.invoke("momentum", {"price": 12.0, "ref": 10.0})
    assert score == pytest.approx(2.0)

    plugin = reg.get("momentum")
    assert isinstance(plugin, AlphaPlugin)
    assert plugin.invocations == 1
    assert plugin.last_score == pytest.approx(2.0)
    assert plugin.enabled is True


def test_alpha_plugin_disabled_after_repeated_failures():
    reg = AlphaPluginRegistry()

    def bad_handler(_ctx):
        raise RuntimeError("boom")

    reg.register("flaky", bad_handler, max_failures=3)

    for _ in range(3):
        result = reg.invoke("flaky", {})
        assert result is None

    plugin = reg.get("flaky")
    assert plugin is not None
    assert plugin.failures == 3
    assert plugin.enabled is False
    assert "boom" in plugin.last_error

    # Further invocations short-circuit — no handler call.
    assert reg.invoke("flaky", {}) is None

    # Reset brings it back (useful for operator re-enable flow).
    reg.reset("flaky")
    plugin_after = reg.get("flaky")
    assert plugin_after is not None
    assert plugin_after.enabled is True
    assert plugin_after.failures == 0


def test_alpha_plugin_invoke_all_returns_enabled_scores_only():
    reg = AlphaPluginRegistry()
    reg.register("a", lambda _c: 1.0)
    reg.register("b", lambda _c: 2.0)

    def broken(_c):
        raise ValueError("broken")

    reg.register("c", broken, max_failures=1)

    results = reg.invoke_all({})
    # 'a' and 'b' run cleanly, 'c' fails and disables itself.
    assert results == {"a": 1.0, "b": 2.0}
    assert reg.get("c").enabled is False
    assert "c" not in reg.enabled_names()
    assert set(reg.enabled_names()) == {"a", "b"}


def test_alpha_plugin_singleton_exposed_at_module_level():
    assert isinstance(_alpha_plugins, AlphaPluginRegistry)
