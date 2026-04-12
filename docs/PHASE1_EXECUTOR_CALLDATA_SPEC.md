# Phase 1 Executor Calldata Spec

This document is the canonical calldata contract between the Python strategy layer and the Solidity executor.

## DEX code map

- `0` = Uniswap
- `1` = Camelot
- `2` = Sushi

## Arbitrage payload tuple

```text
(uint8,address,address,address,uint8,uint8,uint8,uint24,uint24,uint24,uint256,uint256,uint256)
```

Fields in order:
1. `strategy_code`
2. `token_a`
3. `token_b`
4. `token_c`
5. `dex_buy`
6. `dex_mid`
7. `dex_sell`
8. `fee_buy`
9. `fee_mid`
10. `fee_sell`
11. `min_amount_out_buy`
12. `min_amount_out_mid`
13. `min_amount_out_sell`

Notes:
- `token_c` is the zero address for non-triangular routes.
- `dex_mid` and `fee_mid` are zero for non-triangular routes.
- `min_amount_out_buy` and `min_amount_out_sell` must be strictly positive.
- `min_amount_out_mid` may be zero only for non-triangular routes.

## Liquidation payload tuple

```text
(address,address,address,uint256,bool,uint8,uint24,uint256)
```

Fields in order:
1. `collateral_asset`
2. `debt_asset`
3. `borrower`
4. `debt_to_cover`
5. `receive_a_token`
6. `sell_dex`
7. `sell_fee`
8. `amount_out_min`

Notes:
- `amount_out_min` must be strictly positive.
- `sell_dex` must resolve through the canonical DEX code map.

## Python helper surface

The canonical encoder helpers live in:
- `src/strategies/executor_calldata.py`

Primary functions:
- `encode_arb_calldata(...)`
- `encode_liquidation_calldata(...)`
- `slippage_min_out(...)`

## Test coverage

Round-trip ABI coverage is implemented in:
- `tests/test_executor_calldata.py`

## Integration target

After the overwrite patch is applied to the runtime strategy modules and the Solidity executor:
- `src/strategies/flash_arb.py` should use `encode_arb_calldata(...)`
- `src/strategies/liquidation_executor.py` should use `encode_liquidation_calldata(...)`
- `contracts/AaveBotExecutor.sol` should decode the same tuple shapes before executing strategy logic
