# Release Checklist (Execution-Ready)

Use this checklist before every release tag.

## 1) Code + Tests
- [ ] `pip install -r requirements-dev.txt`
- [ ] `./scripts/release_gate.sh`
- [ ] Contract changes validated (if any) with local Hardhat test run

## 2) Risk + Runtime
- [ ] Risk parameters reviewed (`src/core/risk_manager.py`)
- [ ] API keys/secrets present in target environment
- [ ] Rollback target version identified

## 3) Deployment
- [ ] Changelog drafted
- [ ] Release notes drafted
- [ ] Staging smoke test passed
- [ ] Production deploy approved

## 4) Post-Release
- [ ] Monitor error rate + trade success rate for 30 minutes
- [ ] Verify reporting pipeline and dashboard live updates
- [ ] Confirm vault payout accounting
