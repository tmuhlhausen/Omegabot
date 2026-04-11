# Omegabot Modernization Program

## Phase A — Stabilize (Immediate)
- Restore import closure for engine runtime dependencies.
- Normalize strategy packaging under `src/` while keeping compatibility shims.
- Introduce shared dependency constraints.
- Add startup import health checks.

## Phase B — Harden
- Formalize env profiles (`dev`, `staging`, `production`).
- Enforce secret/config validation at startup.
- Expand security notes and threat model docs.

## Phase C — Scale
- Event-driven strategy registry + pluggable runners.
- Dedicated queue layer for scanner→executor backpressure.
- Split reporting and trade execution workers.

## Phase D — Operate
- CI quality gates: import smoke, tests, type checks, dependency drift checks.
- Structured release notes + migration changelog.
- SLO dashboards for latency, error rate, and trade throughput.

## Phase E — Grow
- Sandbox simulation harness for every strategy class.
- Feature flags and staged rollouts.
- Automated anomaly triage and recovery workflows.

## Compatibility Policy
- Prefer additive changes.
- Keep legacy entry points as aliases for at least one release cycle.
- Remove only when telemetry confirms no active usage.

## Strategy Import Deprecation Timeline
- **2026-04-11 (now):** `src/strategies/` is canonical. Root `strategies/` is shim-only and emits deprecation warnings.
- **2026-05-15:** CI blocks any new imports from `strategies.*` in `src/` and `tests/`.
- **2026-06-30:** Remove root `strategies/` shim package after one release cycle and migration verification.

## Cleanup Milestone
- **Milestone: 2026-06-30**
  - Delete `strategies/` shim modules.
  - Drop deprecated import checks once shim is removed and all callers are migrated.
  - Record migration completion in release notes.
