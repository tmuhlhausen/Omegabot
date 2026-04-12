# Omegabot Implementation Matrix

Status legend: `scaffold` | `partial` | `prod`.

| ID | Capability | Code path | Status | Test coverage | Operational metric | Owner | Release critical |
|---|---|---|---|---|---|---|---|
| IM-001 | Formula registry with provenance lifecycle | `src/predictive/formula_engine.py`, `src/predictive/formula_provenance.py` | partial | unit (`tests/test_expansion_blueprints.py`, `tests/test_roadmap_slice2.py`) | formula version adoption rate | Quant Core | no |
| IM-002 | Adaptive ensemble scoring | `src/predictive/formula_engine.py` | scaffold | untested | signal precision@k | Quant Core | no |
| IM-003 | Meta-formula compiler | `src/predictive/formula_engine.py` | scaffold | untested | candidate->champion conversion rate | Quant Core | no |
| IM-004 | Regime-conditioned formula switching | `src/predictive/formula_engine.py`, `src/risk/autonomous_risk_brain.py` | partial | unit (`tests/test_roadmap_runtime.py`) | regime mismatch rate | Quant Core | no |
| IM-005 | Formula fitness walk-forward benchmarking | `src/simulation/digital_twin.py` | scaffold | untested | out-of-sample sharpe drift | Quant Research | no |
| IM-006 | Unified strategy API contract | `src/strategies/__init__.py`, `src/strategies/advanced_strategies.py` | partial | unit (`tests/test_core.py`) | strategy interface compatibility score | Strategy Eng | yes |
| IM-007 | Predictive stack fusion | `src/predictive/omega_intelligence.py`, `src/predictive/market_intel.py` | scaffold | untested | blended alpha lift vs baseline | Strategy Eng | no |
| IM-008 | Intent-aware execution + slippage sim | `src/strategies/liquidation_executor.py`, `src/simulation/digital_twin.py` | partial | unit (`tests/test_release_critical_matrix.py`) | pre-trade slippage error | Execution Eng | yes |
| IM-009 | Multi-objective optimizer | `src/strategies/route_optimizer.py` | partial | unit (`tests/test_roadmap_slice2.py`) | objective score delta | Execution Eng | no |
| IM-010 | Strategy kill-switch + quarantine | `src/governance/policy_engine.py`, `src/core/feature_flags.py` | partial | unit (`tests/test_roadmap_slice2.py`, `tests/test_roadmap_runtime.py`) | auto-quarantine time-to-trigger | Reliability | yes |
| IM-011 | Exchange capability matrix | `src/strategies/route_optimizer.py` | scaffold | untested | venue selection accuracy | Expansion | no |
| IM-012 | Bridge safety matrix | `src/strategies/expansion_router.py` | partial | unit (`tests/test_release_critical_matrix.py`) | unsafe route rejection rate | Expansion | yes |
| IM-013 | Smart route optimizer (DEX/CEX/bridge) | `src/strategies/route_optimizer.py` | partial | unit (`tests/test_roadmap_slice2.py`) | net execution edge bps | Execution Eng | yes |
| IM-014 | Failure-domain isolation per venue | `src/core/engine.py`, `src/core/modules.py` | partial | unit (`tests/test_release_critical_matrix.py`) | blast-radius containment ratio | Reliability | yes |
| IM-015 | Liquidity-weighted pair activation | `src/core/asset_universe.py` | partial | unit (`tests/test_expansion_blueprints.py`) | dormant-pair false activation rate | Expansion | no |
| IM-016 | Asset universe taxonomy | `src/core/asset_universe.py` | partial | unit (`tests/test_expansion_blueprints.py`) | taxonomy coverage ratio | Risk Eng | no |
| IM-017 | Per-asset risk templates | `src/core/risk_manager.py`, `src/core/asset_universe.py` | partial | unit (`tests/test_release_critical_matrix.py`) | template policy violation rate | Risk Eng | yes |
| IM-018 | Pair lifecycle manager | `src/core/asset_universe.py` | scaffold | untested | probation->active promotion quality | Risk Eng | no |
| IM-019 | Correlation clustering controls | `src/core/risk_manager.py` | scaffold | untested | hidden concentration alerts/day | Risk Eng | no |
| IM-020 | Asset-specific oracle confidence | `src/predictive/market_intel.py` | scaffold | untested | oracle confidence calibration error | Data Eng | no |
| IM-021 | Modular executor contracts | `contracts/AaveBotExecutor.sol`, `contracts/NeuralBotVault.sol` | partial | unit (`tests/test_release_critical_matrix.py`) | executor module failure rate | Smart Contracts | yes |
| IM-022 | Pausable + role/timelock guardrails | `contracts/AaveBotFactory.sol`, `contracts/NeuralBotVault.sol` | partial | unit (`tests/test_release_critical_matrix.py`) | privileged action audit pass rate | Smart Contracts | yes |
| IM-023 | Invariant-based policy proofs | `contracts/SECURITY_EXPANSION_PLAN.md` | partial | unit (`tests/test_release_critical_matrix.py`) | invariant breach count | Smart Contracts | yes |
| IM-024 | Runtime anomaly emergency actions | `src/monitoring/platform_reporter.py`, `src/governance/policy_engine.py` | partial | unit (`tests/test_release_critical_matrix.py`) | emergency action MTTR | Reliability | yes |
| IM-025 | Segmented custody vault upgrade path | `contracts/NeuralBotVault.sol`, `backend/vault_client.py` | partial | unit (`tests/test_release_critical_matrix.py`) | custody isolation coverage | Smart Contracts | yes |
| IM-026 | Unified real-time risk brain | `src/risk/autonomous_risk_brain.py` | partial | unit (`tests/test_roadmap_runtime.py`) | risk mode classification accuracy | Risk Eng | yes |
| IM-027 | CVaR envelope with adaptive caps | `src/core/risk_manager.py` | partial | unit (`tests/test_release_critical_matrix.py`) | cvar cap breach rate | Risk Eng | yes |
| IM-028 | Self-adjusting stop policies | `src/governance/policy_engine.py` | partial | unit (`tests/test_release_critical_matrix.py`) | drawdown containment delta | Risk Eng | yes |
| IM-029 | Risk debt tracking + forced delever | `src/core/risk_manager.py` | partial | unit (`tests/test_release_critical_matrix.py`) | delever trigger latency | Risk Eng | yes |
| IM-030 | Risk explainability feed | `src/monitoring/hud_server.py`, `src/monitoring/platform_reporter.py` | scaffold | untested | explainability coverage % | Observability | no |
| IM-031 | Deterministic backtest engine | `src/simulation/digital_twin.py` | partial | unit (`tests/test_roadmap_runtime.py`) | replay determinism score | Quant Research | yes |
| IM-032 | Live-to-sim incident replay | `src/simulation/digital_twin.py` | partial | unit (`tests/test_roadmap_runtime.py`) | replay reconstruction success | Reliability | no |
| IM-033 | Shadow mode for candidate strategies | `src/core/feature_flags.py`, `src/core/engine.py` | scaffold | untested | shadow-prod divergence | Strategy Eng | no |
| IM-034 | Profit attribution by signal/path | `src/monitoring/platform_reporter.py` | scaffold | untested | attribution completeness | Data Eng | no |
| IM-035 | Continuous model benchmark competition | `src/predictive/formula_engine.py`, `src/simulation/digital_twin.py` | scaffold | untested | champion retention duration | Quant Research | no |
| IM-036 | Reliability scorecards | `src/monitoring/platform_reporter.py` | partial | unit (`tests/test_roadmap_phase_c_d.py`) | module SLO attainment | Reliability | no |
| IM-037 | Self-remediation runbooks | `src/core/engine.py`, `src/monitoring/hud_server.py` | partial | unit (`tests/test_release_critical_matrix.py`) | auto-remediation success rate | SRE | yes |
| IM-038 | Canary releases for strategy/formula | `src/core/feature_flags.py` | partial | unit (`tests/test_release_critical_matrix.py`) | canary rollback rate | SRE | yes |
| IM-039 | Cost-aware autoscaling/failover | `src/core/engine.py` | scaffold | untested | failover recovery time | SRE | no |
| IM-040 | Runtime blast-radius controls | `src/core/modules.py`, `src/core/engine.py` | partial | unit (`tests/test_release_critical_matrix.py`) | fault containment scope | SRE | yes |
| IM-041 | Policy-as-code deployment gates | `src/governance/policy_engine.py`, `scripts/release_gate.sh` | partial | unit (`tests/test_roadmap_slice2.py`) | policy gate pass/fail fidelity | Governance | yes |
| IM-042 | Human-in-loop high-risk approvals | `src/governance/policy_engine.py` | partial | unit (`tests/test_release_critical_matrix.py`) | approval SLA | Governance | yes |
| IM-043 | API productization + telemetry exports | `backend/auth.py`, `src/monitoring/partykit_client.py` | partial | unit (`tests/test_roadmap_phase_c_d.py`) | API uptime + export lag | Product | no |
| IM-044 | Multi-tenant entitlement model | `backend/auth.py`, `src/core/feature_flags.py` | scaffold | untested | entitlement policy violation count | Product | no |
| IM-045 | Plugin framework for external alpha | `src/core/modules.py` | partial | unit (`tests/test_roadmap_phase_c_d.py`) | plugin fault isolation score | Platform | no |
| IM-046 | Deterministic release test gate | `scripts/test.sh`, `scripts/release_gate.sh` | prod | script + unit (`tests/test_implementation_matrix_gate.py`) | release gate pass rate | Release Eng | yes |
| IM-047 | Python compile verification gate | `scripts/release_gate.sh` | prod | script + unit (`tests/test_implementation_matrix_gate.py`) | syntax gate failure rate | Release Eng | yes |
| IM-048 | Dependency health check gate | `scripts/release_gate.sh`, `scripts/import_healthcheck.py` | partial | script + unit (`tests/test_implementation_matrix_gate.py`) | dependency conflict incidence | Release Eng | yes |
| IM-049 | Matrix-integrity release gate | `scripts/release_gate.sh`, `scripts/check_implementation_matrix.py` | prod | unit (`tests/test_implementation_matrix_gate.py`) | release-critical scaffold leakage | Release Eng | yes |
| IM-050 | Matrix ID roadmap traceability | `docs/REVOLUTION_ROADMAP.md`, `docs/RELEASE_BLUEPRINT.md`, `ROADMAP.md` | prod | review-only | roadmap claim traceability % | PMO | yes |
