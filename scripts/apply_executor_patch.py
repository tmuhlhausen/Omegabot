#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(rel_path: str, old: str, new: str) -> None:
    path = ROOT / rel_path
    body = path.read_text(encoding="utf-8")
    if old not in body:
        raise RuntimeError(f"pattern not found in {rel_path}: {old[:60]!r}")
    path.write_text(body.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel_path}")


def main() -> None:
    replace_once(
        "src/strategies/flash_arb.py",
        "import asyncio\nimport logging\nimport time\nfrom dataclasses import dataclass, field\nimport uuid\nfrom typing import Optional, List\n\nfrom web3 import AsyncWeb3\n",
        "import asyncio\nimport logging\nimport time\nfrom dataclasses import dataclass, field\nimport uuid\nfrom typing import Optional, List\n\nfrom eth_abi import encode as abi_encode\nfrom web3 import AsyncWeb3\n",
    )

    replace_once(
        "src/strategies/flash_arb.py",
        "                op_code,\n                b\"\",  # opData — in production: ABI-encoded swap path\n            ).build_transaction({\n",
        "                op_code,\n                op_data,\n            ).build_transaction({\n",
    )

    replace_once(
        "src/strategies/liquidation_executor.py",
        "                    b\"\",  # swap calldata built by contract\n                    0,    # minOut — contract calculates\n                ],\n            )\n",
        "                    False,\n                    0,\n                    3000,\n                    max(1, int(target.debt_to_cover_wei * (10_000 - MAX_SLIPPAGE_BPS) / 10_000)),\n                )],\n            )\n",
    )

    replace_once(
        "contracts/AaveBotExecutor.sol",
        "    modifier onlyOwner() {\n        require(msg.sender == owner, \"NOT_OWNER\");\n        _;\n    }\n\n    // ─── Flash Loan Callback ─────────────────────────────────────────────\n",
        "    modifier onlyOwner() {\n        require(msg.sender == owner, \"NOT_OWNER\");\n        _;\n    }\n\n    function execute(\n        address asset,\n        uint256 amount,\n        uint8 opCode,\n        bytes calldata opData\n    ) external onlyOwner whenNotPaused nonReentrant {\n        require(amount > 0, \"ZERO_AMOUNT\");\n        bytes memory params = bytes.concat(bytes1(opCode), opData);\n        POOL.flashLoanSimple(address(this), asset, amount, params, 0);\n    }\n\n    function _approveExact(address token, address spender, uint256 amount) internal {\n        IERC20(token).forceApprove(spender, 0);\n        IERC20(token).forceApprove(spender, amount);\n    }\n\n    // ─── Flash Loan Callback ─────────────────────────────────────────────\n",
    )

    replace_once(
        "contracts/AaveBotExecutor.sol",
        "        // AUDIT[EXACT_APPROVAL]: Approve exact repay amount\n        IERC20(asset).safeIncreaseAllowance(address(POOL), repayAmount);\n",
        "        // AUDIT[EXACT_APPROVAL]: Approve exact repay amount\n        _approveExact(asset, address(POOL), repayAmount);\n",
    )

    replace_once(
        "contracts/AaveBotExecutor.sol",
        "        // AUDIT[EXACT_APPROVAL]: Approve exact swap amount\n        IERC20(tokenIn).safeIncreaseAllowance(router, amountIn);\n\n        amountOut = ISwapRouter(router).exactInputSingle(\n",
        "        require(amountOutMin > 0, \"MIN_OUT_REQUIRED\");\n\n        // AUDIT[EXACT_APPROVAL]: Approve exact swap amount\n        _approveExact(tokenIn, router, amountIn);\n\n        amountOut = ISwapRouter(router).exactInputSingle(\n",
    )

    print("executor/strategy patch applied")


if __name__ == "__main__":
    main()
