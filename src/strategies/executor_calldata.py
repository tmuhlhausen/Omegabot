from __future__ import annotations

from dataclasses import dataclass

from eth_abi import encode

ZERO_ADDRESS = "0x" + "0" * 40

DEX_CODE_MAP = {
    "uniswap": 0,
    "camelot": 1,
    "sushi": 2,
}

ARB_EXECUTION_TUPLE = (
    "(uint8,address,address,address,uint8,uint8,uint8,uint24,uint24,uint24,uint256,uint256,uint256)"
)
LIQ_EXECUTION_TUPLE = "(address,address,address,uint256,bool,uint8,uint24,uint256)"


@dataclass(frozen=True)
class ArbCalldataRequest:
    strategy_code: int
    token_a: str
    token_b: str
    token_c: str | None
    dex_buy: str
    dex_mid: str | None
    dex_sell: str
    fee_buy: int
    fee_mid: int
    fee_sell: int
    min_amount_out_buy: int
    min_amount_out_mid: int
    min_amount_out_sell: int


@dataclass(frozen=True)
class LiquidationCalldataRequest:
    collateral_asset: str
    debt_asset: str
    borrower: str
    debt_to_cover: int
    receive_a_token: bool
    sell_dex: str
    sell_fee: int
    amount_out_min: int


def dex_code(name: str | None) -> int:
    if name is None:
        return 0
    try:
        return DEX_CODE_MAP[name.lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported dex: {name}") from exc


def slippage_min_out(amount_out: int, slippage_bps: int) -> int:
    if amount_out <= 0:
        raise ValueError("amount_out must be positive")
    if not 0 <= slippage_bps < 10_000:
        raise ValueError("slippage_bps must be in [0, 10000)")
    return max(1, amount_out * (10_000 - slippage_bps) // 10_000)


def encode_arb_calldata(request: ArbCalldataRequest) -> bytes:
    if request.min_amount_out_buy <= 0:
        raise ValueError("min_amount_out_buy must be positive")
    if request.min_amount_out_sell <= 0:
        raise ValueError("min_amount_out_sell must be positive")

    return encode(
        [ARB_EXECUTION_TUPLE],
        [(
            request.strategy_code,
            request.token_a,
            request.token_b,
            request.token_c or ZERO_ADDRESS,
            dex_code(request.dex_buy),
            dex_code(request.dex_mid),
            dex_code(request.dex_sell),
            request.fee_buy,
            request.fee_mid,
            request.fee_sell,
            request.min_amount_out_buy,
            request.min_amount_out_mid,
            request.min_amount_out_sell,
        )],
    )


def encode_liquidation_calldata(request: LiquidationCalldataRequest) -> bytes:
    if request.amount_out_min <= 0:
        raise ValueError("amount_out_min must be positive")

    return encode(
        [LIQ_EXECUTION_TUPLE],
        [(
            request.collateral_asset,
            request.debt_asset,
            request.borrower,
            request.debt_to_cover,
            request.receive_a_token,
            dex_code(request.sell_dex),
            request.sell_fee,
            request.amount_out_min,
        )],
    )
