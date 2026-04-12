# Changelog

All notable changes to NeuralBot OMEGA are tracked here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project's
implementation matrix IDs (`docs/IMPLEMENTATION_MATRIX.md`).

## [1.0.0] — 2026-04-12 — Final Build & Release

### Added

- **IM-014 / IM-040** — `BlastRadiusController` in `src/core/modules.py`:
  per-venue failure-domain isolation with quarantine, capital, and failure
  budgets.
- **IM-017** — Per-asset risk templates in `src/core/asset_universe.py`:
  category defaults plus per-asset overrides surfaced via
  `AssetUniverse.risk_template()`.
- **IM-027** — `CVaRController` adaptive cap controller in
  `src/core/risk_manager.py`: rolling tail-loss buffer that shrinks position
  size envelopes under tail pressure.
- **IM-028** — `StopPolicyController` in `src/governance/policy_engine.py`:
  self-adjusting stop-loss / take-profit resolved against drawdown,
  volatility, and risk mode.
- **IM-029** — `RiskDebtTracker` + `DeleverPlan` in
  `src/core/risk_manager.py`: tracks risk debt and emits forced delever
  proposals when policy is breached.
- **IM-037** — `RunbookRegistry` in `src/monitoring/hud_server.py`:
  registers self-remediation runbooks keyed by anomaly tag with execution
  history capture.
- **IM-038** — `CanaryController` in `src/core/feature_flags.py`: stages
  canary rollouts with auto-promote / auto-rollback semantics.
- **Test gate** — `tests/test_release_critical_matrix.py` covering 24
  release-critical behaviors across IM-008, IM-012, IM-014, IM-017, IM-021,
  IM-022, IM-023, IM-024, IM-025, IM-027, IM-028, IM-029, IM-037, IM-038,
  IM-040, and IM-042.

### Changed

- `scripts/release_gate.sh` now runs
  `scripts/check_implementation_matrix.py` as the seventh gate step so the
  release-critical IM rows are enforced before tagging.
- `docs/IMPLEMENTATION_MATRIX.md` updated to reflect partial-or-better
  status with unit coverage citations for every release-critical row.
- `src/core/modules.py`, `src/strategies/liquidation_executor.py`, and
  `backend/vault_client.py` now import optional `web3` /
  `eth_account` / `eth_abi` dependencies behind a fallback shim so unit
  tests run without the full on-chain stack.

### Release Gate Status

```
[1/7] deterministic unit test gate         ✅
[2/7] python compile verification          ✅
[3/7] packaging metadata validation        ✅
[4/7] dependency health check              ✅
[5/7] deprecated import policy             ✅
[6/7] release-critical implementation matrix ✅
[7/7] release gate complete                ✅
```

## [0.9.0] — 2026-04-11 — Stabilization Phase A

- Added implementation matrix and matrix-integrity gate (IM-049, IM-050).
- Added Alembic migrations and dev-only DB bootstrap (`scripts/dev_db_init.sh`).
- Refactored engine loops into supervised components.
- Refactored liquidation scanner lifecycle, queueing, and metrics.
- Enforced strategies import deprecation path and CI checks.
- Added risk-aware route optimizer calibration and feedback loop.
- Added degraded risk fail-safe for telemetry uncertainty.
