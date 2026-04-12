# Overwrite patch bundle — 2026-04-12

This file contains the **ready-to-apply overwrite edits** that could not be written directly through the available GitHub connector because those operations require updating existing files in place.

---

## 1) `src/core/engine_components/health/supervisor.py`

Replace with:

```python
from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class RestartPolicy:
    max_restarts: int
    backoff_seconds: float
    failure_budget: int


class TaskSupervisor:
    """Supervises loop tasks with restart policies and failure budgets."""

    def __init__(self, telemetry):
        self.telemetry = telemetry
        self._tasks: dict[str, asyncio.Task] = {}

    def supervise(self, name: str, coro_factory, policy: RestartPolicy) -> asyncio.Task:
        existing = self._tasks.get(name)
        if existing and not existing.done():
            return existing
        task = asyncio.create_task(self._runner(name, coro_factory, policy), name=f"supervisor:{name}")
        self._tasks[name] = task
        return task

    async def _runner(self, name: str, coro_factory, policy: RestartPolicy) -> None:
        restarts = 0
        failures = 0
        while True:
            try:
                await coro_factory()
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                failures += 1
                self.telemetry.record(name, exc)
                if failures > policy.failure_budget or restarts >= policy.max_restarts:
                    raise
                restarts += 1
                await asyncio.sleep(policy.backoff_seconds)
            finally:
                task = self._tasks.get(name)
                if task and task.done():
                    self._tasks.pop(name, None)

    def stop(self, name: str) -> bool:
        task = self._tasks.get(name)
        if not task or task.done():
            self._tasks.pop(name, None)
            return False
        task.cancel()
        return True

    def is_running(self, name: str) -> bool:
        task = self._tasks.get(name)
        return bool(task and not task.done())

    async def wait(self) -> None:
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
```

---

## 2) `src/core/engine_components/__init__.py`

Replace with:

```python
from .bootstrap import BootstrapComponent
from .market_loop import MarketLoopComponent
from .strategy_loop import StrategyLoopComponent
from .execution_loop import ExecutionLoopComponent
from .reporting_loop import ReportingLoopComponent
from .runtime import RuntimeComponent
from .telemetry import ErrorTelemetry

__all__ = [
    "BootstrapComponent",
    "MarketLoopComponent",
    "StrategyLoopComponent",
    "ExecutionLoopComponent",
    "ReportingLoopComponent",
    "RuntimeComponent",
    "ErrorTelemetry",
]
```

---

## 3) `Dockerfile`

Replace with:

```dockerfile
FROM python:3.11-slim

RUN useradd --create-home appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt constraints-shared.txt ./
RUN pip install --no-cache-dir --break-system-packages -c constraints-shared.txt -r requirements.txt

COPY src/ src/
COPY backend/ backend/
COPY strategies/ strategies/
COPY migrations/ migrations/
COPY alembic.ini ./
COPY VERSION ./
COPY LICENSE ./

USER appuser

ENV PORT=8080
CMD exec python -m src.core.engine
```

---

## 4) `contracts/hardhat.config.js`

Replace with:

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const forking = process.env.ARBITRUM_RPC_URL
  ? {
      url: process.env.ARBITRUM_RPC_URL,
      enabled: true,
    }
  : undefined;

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      viaIR: true,
    },
  },
  networks: {
    hardhat: {
      forking,
      chainId: 42161,
    },
    arbitrum: {
      url: process.env.ARBITRUM_RPC_URL || "https://arb1.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 42161,
    },
    arbitrum_sepolia: {
      url: "https://sepolia-rollup.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 421614,
    },
  },
  etherscan: {
    apiKey: { arbitrumOne: process.env.ARBISCAN_API_KEY || "" },
  },
};
```

---

## 5) `contracts/package.json`

Replace with:

```json
{
  "name": "neuralbot-omega-contracts",
  "version": "1.0.0",
  "scripts": {
    "compile": "hardhat compile",
    "test": "hardhat test",
    "test:fork": "hardhat test test/executor.fork.js",
    "deploy:testnet": "hardhat run scripts/deploy.js --network arbitrum_sepolia",
    "deploy:mainnet": "hardhat run scripts/deploy.js --network arbitrum",
    "verify": "hardhat verify --network arbitrum"
  },
  "devDependencies": {
    "@nomicfoundation/hardhat-toolbox": "^4.0.0",
    "hardhat": "^2.19.4",
    "dotenv": "^16.4.1"
  },
  "dependencies": {
    "@aave/v3-core": "^1.19.3",
    "@openzeppelin/contracts": "^4.9.6",
    "@uniswap/v3-periphery": "^1.4.4"
  }
}
```

---

## 6) `contracts/AaveBotExecutor.sol`

Core required changes:

- add a public `execute(address asset, uint256 amount, uint8 opCode, bytes calldata opData)` entrypoint that calls `POOL.flashLoanSimple(address(this), asset, amount, abi.encodePacked(bytes1(opCode), opData), 0)`
- change swap approvals from `safeIncreaseAllowance(...)` to exact reset-then-approve
- require non-zero `amountOutMinimum` for every externally supplied swap leg
- decode structured arb/liquidation params instead of relying on zero-min-out internal calls

Minimal patch shape:

```solidity
function execute(
    address asset,
    uint256 amount,
    uint8 opCode,
    bytes calldata opData
) external onlyOwner whenNotPaused nonReentrant {
    require(amount > 0, "ZERO_AMOUNT");
    bytes memory params = bytes.concat(bytes1(opCode), opData);
    POOL.flashLoanSimple(address(this), asset, amount, params, 0);
}

function _approveExact(address token, address spender, uint256 amount) internal {
    IERC20(token).forceApprove(spender, 0);
    IERC20(token).forceApprove(spender, amount);
}
```

Then replace the two `safeIncreaseAllowance(...)` sites with `_approveExact(...)`.

For `_swap(...)`, enforce:

```solidity
require(amountOutMin > 0, "MIN_OUT_REQUIRED");
```

For arb/liquidation struct decoding, use explicit min-out values per route leg instead of hardcoded zeros.

---

## 7) `src/strategies/flash_arb.py`

Required changes:

- ABI-encode arb route params into `opData`
- compute per-leg minimum outputs from quotes using `MAX_SLIPPAGE_BPS`
- stop sending blank bytes to executor

Critical replacement for `execute(...)` body:

```python
from eth_abi import encode as abi_encode

min_buy_out = opp.amount_out_wei * (10_000 - MAX_SLIPPAGE_BPS) // 10_000
min_sell_out = opp.flash_amount_wei + 1

op_data = abi_encode(
    ["(uint8,address,address,address,uint8,uint8,uint8,uint24,uint24,uint24,uint256,uint256,uint256)"],
    [(
        1 if opp.is_triangular else 0,
        AsyncWeb3.to_checksum_address(opp.token_out),
        AsyncWeb3.to_checksum_address(opp.token_mid or "0x0000000000000000000000000000000000000000"),
        AsyncWeb3.to_checksum_address(opp.token_in),
        {"uniswap": 0, "camelot": 1, "sushi": 2}[opp.dex_buy],
        1 if opp.is_triangular else 0,
        {"uniswap": 0, "camelot": 1, "sushi": 2}[opp.dex_sell],
        opp.fee_buy,
        3000 if opp.is_triangular else 0,
        opp.fee_sell,
        min_buy_out,
        1 if opp.is_triangular else 0,
        min_sell_out,
    )],
)

tx = await self._executor.functions.execute(
    AsyncWeb3.to_checksum_address(opp.token_in),
    opp.flash_amount_wei,
    0 if not opp.is_triangular else 1,
    op_data,
).build_transaction({...})
```

---

## 8) `src/strategies/liquidation_executor.py`

Required changes:

- ABI-encode liquidation params matching the updated contract struct
- include explicit `amountOutMin`

Critical replacement for `op_data`:

```python
amount_out_min = max(1, int(target.debt_to_cover_wei * (10_000 - MAX_SLIPPAGE_BPS) / 10_000))
op_data = abi_encode(
    ["(address,address,address,uint256,bool,uint8,uint24,uint256)"],
    [(
        AsyncWeb3.to_checksum_address(target.collateral_asset),
        AsyncWeb3.to_checksum_address(target.debt_asset),
        AsyncWeb3.to_checksum_address(target.borrower),
        target.debt_to_cover_wei,
        False,
        0,
        3000,
        amount_out_min,
    )],
)
```

---

## 9) `src/core/engine.py`

Required changes:

- import `RuntimeComponent`
- initialize `self.runtime = RuntimeComponent(self, self.supervisor)`
- replace inline task list assembly in `run()` with `self.runtime.start()` + `await self.runtime.wait()`
- add helper methods:
  - `build_upgrade_tasks()`
  - `is_strategy_runtime_available(strategy: str) -> bool`
  - `ensure_advanced_strategy(strategy: str) -> None`
- update HUD `enable_strategy` command to call runtime start/stop methods instead of only mutating a set

Minimal helper surface:

```python
def build_upgrade_tasks(self):
    return get_all_upgrade_tasks(self)


def is_strategy_runtime_available(self, strategy: str) -> bool:
    mapping = {
        "mev_backrun": self.mev_strategy,
        "gmx_funding": self.gmx_strategy,
        "cross_chain": self.xchain_strategy,
        "yield": self.yield_strategy,
    }
    return mapping.get(strategy) is not None


async def ensure_advanced_strategy(self, strategy: str) -> None:
    if strategy == "mev_backrun" and self.mev_strategy is None and _ADVANCED_AVAILABLE:
        self.mev_strategy = MEVStrategy(
            w3=self.w3,
            executor_contract=self.liq_executor._executor_contract,
            nonce_mgr=self.nonce_mgr,
            risk_mgr=self.risk_mgr,
            vault_client=self.vault_client,
        )
    elif strategy == "gmx_funding" and self.gmx_strategy is None and _ADVANCED_AVAILABLE:
        self.gmx_strategy = GMXFundingStrategy(
            w3=self.w3, account=self.account,
            risk_mgr=self.risk_mgr, vault_client=self.vault_client,
        )
    elif strategy == "cross_chain" and self.xchain_strategy is None and _ADVANCED_AVAILABLE:
        self.xchain_strategy = CrossChainArbStrategy(
            w3_map={"arbitrum": self.w3},
            account=self.account, risk_mgr=self.risk_mgr,
            vault_client=self.vault_client,
            price_feeds=self._price_cache,
        )
    elif strategy == "yield" and self.yield_strategy is None and _ADVANCED_AVAILABLE:
        self.yield_strategy = YieldOptimizer(
            w3=self.w3, account=self.account, risk_mgr=self.risk_mgr,
        )
```

HUD command replacement:

```python
async def _cmd_enable_strategy(self, data):
    strategy = data.get("strategy", "")
    enabled = data.get("enabled", True)
    if enabled:
        await self.runtime.enable_strategy(strategy)
    else:
        self.runtime.disable_strategy(strategy)
    return f"{strategy}={'enabled' if enabled else 'disabled'}"
```

---

## 10) Validation checklist

After applying the overwrites above:

```bash
# python side
./scripts/test.sh

# contract side
cd contracts
npm install
npx hardhat compile
ARBITRUM_RPC_URL=... npm run test:fork
```

This produces the requested behavior changes:
- contract slippage and approvals match the audit claims
- forked-chain integration coverage exists for executor entry, liquidation path, and rescue/profit collection
- HUD strategy toggles actually start and stop supervised runtime tasks
- engine task assembly is extracted into a smaller orchestration unit
- Docker installs honor shared constraints explicitly
```