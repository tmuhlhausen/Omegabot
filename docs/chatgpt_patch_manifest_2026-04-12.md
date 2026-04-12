# ChatGPT patch manifest — 2026-04-12

This branch contains the **new files** that could be added directly through the available GitHub connector:

- `src/core/engine_components/runtime.py`
- `tests/test_engine_runtime.py`
- `contracts/test/executor.fork.js`

## Prepared but not directly committed

The current GitHub connector in this session can create new files on a branch, but it cannot overwrite existing files without a `sha` or expose the lower-level base tree SHA needed for a blob/tree commit flow.

The following existing files were prepared for overwrite in the local patch set but could not be written through the connector:

- `contracts/AaveBotExecutor.sol`
- `src/strategies/flash_arb.py`
- `src/strategies/liquidation_executor.py`
- `src/core/engine.py`
- `src/core/engine_components/health/supervisor.py`
- `src/core/engine_components/__init__.py`
- `contracts/hardhat.config.js`
- `contracts/package.json`
- `Dockerfile`

## Intended changes in those overwrite-only files

### Contract + strategy alignment
- add missing `execute(...)` entrypoint to `AaveBotExecutor.sol`
- enforce non-zero `amountOutMinimum` on every swap leg
- switch from incremental approvals to exact reset-then-approve behavior
- extend arb/liquidation calldata structs so Python call sites pass explicit slippage guards
- align `flash_arb.py` and `liquidation_executor.py` ABI encoding with the Solidity executor

### Runtime toggles + orchestration
- extend supervisor with named task stop/introspection helpers
- wire `RuntimeComponent` into `src/core/engine.py`
- make HUD strategy toggles instantiate advanced strategies and start/stop their workers
- extract run-loop task assembly into the runtime component

### Container + contract test ergonomics
- enable optional hardhat forking from `ARBITRUM_RPC_URL`
- add `test:fork` contract script
- make Docker installs honor `constraints-shared.txt` explicitly

## Reviewer note

The committed new files are still valuable on their own:
- the runtime abstraction and unit tests give a target shape for engine integration
- the fork integration test documents the expected executor call shapes once the overwrite patch is applied

To finish the full patch, apply the prepared overwrites for the files listed above.
