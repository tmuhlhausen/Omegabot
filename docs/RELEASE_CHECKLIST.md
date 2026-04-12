# Release Checklist (Execution-Ready)

Use this checklist before every release tag.

## 1.0.0 — 2026-04-12 Final Build & Release

## 1) Code + Tests
- [x] `pip install -r requirements-dev.txt`
- [x] `./scripts/release_gate.sh` — all 7 gates green (79 unit tests pass)
- [x] Implementation matrix gate enforced (`scripts/check_implementation_matrix.py`)
- [ ] Contract changes validated (if any) with local Hardhat test run
      (no Solidity changes in 1.0.0)

## 2) Risk + Runtime
- [x] Risk parameters reviewed (`src/core/risk_manager.py`) — CVaR + delever
      + degraded telemetry guard in place
- [x] CVaR adaptive cap controller wired (IM-027)
- [x] Self-adjusting stop policy controller wired (IM-028)
- [x] Per-asset risk templates wired (IM-017)
- [ ] API keys/secrets present in target environment (operator step)
- [ ] Rollback target version identified — previous tag is `0.9.0`

## 3) Deployment
- [x] Changelog drafted (`CHANGELOG.md` 1.0.0 section)
- [x] Release notes drafted (in `CHANGELOG.md` + README badge)
- [x] `.gitignore` added so build artifacts stay out of release branches
- [ ] Staging smoke test passed (operator step)
- [ ] Production deploy approved (operator step)

## 4) Post-Release
- [ ] Monitor error rate + trade success rate for 30 minutes
- [ ] Verify reporting pipeline and dashboard live updates
- [ ] Confirm vault payout accounting
