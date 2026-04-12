# Omegabot Modernization Program

Trace roadmap execution against `docs/IMPLEMENTATION_MATRIX.md` IDs.

## Phase A — Stabilize (Immediate)
- ✅ IM-046/IM-047: restore deterministic runtime and import closure gates.
- ✅ IM-006: normalize strategy packaging under `src/` with compatibility shims.
- ✅ IM-048: enforce shared dependency health checks.
- ✅ IM-049: add startup/release matrix integrity enforcement.

## Phase B — Harden
- ✅ IM-017/IM-027: formalize risk-template and CVaR policy profiles.
- ✅ IM-022/IM-041: strengthen security and policy-as-code deployment gates.
- ✅ IM-042: enforce approval flow for high-risk operations.

## Phase C — Scale
- ✅ IM-045: event-driven strategy registry + pluggable runners.
- ✅ IM-014: queue/backpressure and failure-domain isolation.
- ✅ IM-043: split reporting and trade execution service boundaries.

## Phase D — Operate
- ✅ IM-041/IM-046/IM-049: CI quality and release gates.
- ✅ IM-050: structured release notes + migration changelog traceability.
- ✅ IM-036: SLO dashboards for latency, error rate, and throughput.

## Phase E — Grow
- ✅ IM-031/IM-032: simulation harness and replay for strategy classes.
- ✅ IM-038: staged rollouts/canaries via feature flags.
- ✅ IM-037/IM-040: automated anomaly triage and recovery workflows.

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
