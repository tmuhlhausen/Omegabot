# Runtime / Executor Hardening Roadmap

This roadmap sequences the remaining work after PR #24 into small, testable phases.

## Phase 0 — Apply the committed patch helpers

Goal: get the branch into the intended intermediate state using the scripts already added in PR #24.

Actions:
- run `python scripts/apply_runtime_patch.py`
- run `python scripts/apply_executor_patch.py`
- inspect the resulting diffs before commit

Gate:
- `./scripts/test.sh`
- `cd contracts && npm install && npx hardhat compile`

Exit criteria:
- runtime task wiring is in place
- executor entrypoint exists
- container installs honor constraints
- hardhat fork config is enabled when `ARBITRUM_RPC_URL` is present

## Phase 1 — Make executor calldata fully structural

Goal: remove remaining ad hoc calldata assumptions between Python and Solidity.

Actions:
- define canonical arb/liquidation structs in Solidity comments and Python encoder helpers
- replace inline ABI tuple strings with shared helper functions in Python strategy modules
- add validation checks for unsupported DEX codes / empty route legs
- ensure every route leg has explicit `amountOutMinimum`

Tests:
- unit tests for Python calldata encoding helpers
- hardhat tests decoding encoded calldata and asserting field values

Exit criteria:
- calldata format is documented in one place
- Python and Solidity use the same route model
- blank `opData` paths are gone

## Phase 2 — Tighten contract execution invariants

Goal: make the on-chain executor behavior match the audit claims precisely.

Actions:
- replace all approval flows with exact reset-then-approve semantics
- reject zero `amountOutMinimum` on all externally supplied swap paths
- emit dedicated events for `execute()` requests and per-strategy path execution
- validate strategy opcode and struct length before branching
- add explicit revert strings for malformed calldata and unsupported routes

Tests:
- hardhat unit tests for zero-min-out rejection
- hardhat unit tests for malformed opcode/data rejection
- fork test asserting `execute()` reverts cleanly with invalid min-out settings

Exit criteria:
- approvals and slippage behavior match audit language
- revert reasons are specific and diagnosable

## Phase 3 — Strengthen fork integration coverage

Goal: go beyond compile-only confidence and exercise more real chain behavior.

Actions:
- expand `contracts/test/executor.fork.js`
- add a liquidation-path test against a known non-liquidatable borrower to validate clean failure path
- add a rescue/profit collection round-trip test for multiple assets
- add a smoke test for executor deployment + entrypoint call shape on fork

Tests:
- `ARBITRUM_RPC_URL=... npm run test:fork`

Exit criteria:
- fork suite covers executor entrypoint, liquidation path wiring, and rescue flow
- failures are deterministic enough for CI opt-in or nightly runs

## Phase 4 — Finish runtime task ownership model

Goal: make operator toggles and task lifecycle management fully deterministic.

Actions:
- route all supervised task startup through `RuntimeComponent`
- eliminate duplicated task assembly logic from `engine.py`
- ensure toggled-off strategies stop cleanly and do not auto-restart unexpectedly
- add runtime status reporting for currently running supervised tasks
- surface task names/state in HUD diagnostics

Tests:
- extend `tests/test_engine_runtime.py`
- add tests for idempotent enable/disable
- add tests for disable-while-running cancellation behavior

Exit criteria:
- HUD toggles actually control worker lifecycle
- task ownership lives in one orchestration component

## Phase 5 — Refactor engine into smaller orchestration surfaces

Goal: reduce the blast radius of `src/core/engine.py`.

Actions:
- move advanced strategy initialization into a dedicated component
- move HUD command registration/handlers into a command component
- move state sync logic into a state projection component
- keep `TradingEngine` as a thin composition root

Tests:
- targeted unit tests for each extracted component
- smoke test for engine bootstrap and shutdown path

Exit criteria:
- `engine.py` becomes primarily composition + lifecycle
- subsystems are independently testable without full engine startup

## Phase 6 — CI and release-gate integration

Goal: make the hardening work enforceable.

Actions:
- add optional fork-test job behind env/secret presence
- add static assertions for Docker constraint usage and runtime component imports
- add a release-gate check ensuring executor entrypoint exists and strategy toggles are runtime-backed

Tests:
- GitHub Actions release gate
- optional nightly fork workflow

Exit criteria:
- regressions fail automatically
- roadmap items become policy, not convention

## Recommended order of implementation

1. Phase 0
2. Phase 1 + Phase 2 together
3. Phase 3
4. Phase 4
5. Phase 5
6. Phase 6

## Minimal command checklist

```bash
python scripts/apply_runtime_patch.py
python scripts/apply_executor_patch.py
./scripts/test.sh
cd contracts
npm install
npx hardhat compile
ARBITRUM_RPC_URL=... npm run test:fork
```

## Definition of done for the whole hardening track

- contract slippage and approval behavior are mechanically enforced
- Python/contract execution interfaces are aligned and tested
- runtime toggles control actual supervised workers
- engine orchestration is decomposed into smaller units
- container installs use shared constraints explicitly
- release gates encode the new invariants
