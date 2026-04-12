from __future__ import annotations

from eth_abi import decode
import pytest

from src.strategies.executor_calldata import (
    ARB_EXECUTION_TUPLE,
    LIQ_EXECUTION_TUPLE,
    ArbCalldataRequest,
    LiquidationCalldataRequest,
    ZERO_ADDRESS,
    dex_code,
    encode_arb_calldata,
    encode_liquidation_calldata,
    slippage_min_out,
)


def test_dex_code_mapping_is_stable():
    assert dex_code("uniswap") == 0
    assert dex_code("camelot") == 1
    assert dex_code("sushi") == 2
    with pytest.raises(ValueError):
        dex_code("unknown")


def test_slippage_min_out_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        slippage_min_out(0, 50)
    with pytest.raises(ValueError):
        slippage_min_out(100, 10000)


def test_slippage_min_out_rounds_down_with_floor_of_one():
    assert slippage_min_out(100_000, 50) == 99_500
    assert slippage_min_out(1, 9_999) == 1


def test_encode_arb_calldata_round_trips_expected_fields():
    payload = encode_arb_calldata(
        ArbCalldataRequest(
            strategy_code=1,
            token_a="0x1111111111111111111111111111111111111111",
            token_b="0x2222222222222222222222222222222222222222",
            token_c=None,
            dex_buy="uniswap",
            dex_mid="camelot",
            dex_sell="sushi",
            fee_buy=500,
            fee_mid=3000,
            fee_sell=500,
            min_amount_out_buy=99,
            min_amount_out_mid=88,
            min_amount_out_sell=77,
        )
    )
    decoded = decode([ARB_EXECUTION_TUPLE], payload)[0]
    assert decoded[0] == 1
    assert decoded[1] == "0x1111111111111111111111111111111111111111"
    assert decoded[2] == "0x2222222222222222222222222222222222222222"
    assert decoded[3] == ZERO_ADDRESS
    assert decoded[4] == 0
    assert decoded[5] == 1
    assert decoded[6] == 2
    assert decoded[10] == 99
    assert decoded[11] == 88
    assert decoded[12] == 77


def test_encode_liquidation_calldata_round_trips_expected_fields():
    payload = encode_liquidation_calldata(
        LiquidationCalldataRequest(
            collateral_asset="0x3333333333333333333333333333333333333333",
            debt_asset="0x4444444444444444444444444444444444444444",
            borrower="0x5555555555555555555555555555555555555555",
            debt_to_cover=123456,
            receive_a_token=False,
            sell_dex="uniswap",
            sell_fee=3000,
            amount_out_min=120000,
        )
    )
    decoded = decode([LIQ_EXECUTION_TUPLE], payload)[0]
    assert decoded[0] == "0x3333333333333333333333333333333333333333"
    assert decoded[1] == "0x4444444444444444444444444444444444444444"
    assert decoded[2] == "0x5555555555555555555555555555555555555555"
    assert decoded[3] == 123456
    assert decoded[4] is False
    assert decoded[5] == 0
    assert decoded[6] == 3000
    assert decoded[7] == 120000


def test_encode_helpers_reject_zero_min_out_values():
    with pytest.raises(ValueError):
        encode_arb_calldata(
            ArbCalldataRequest(
                strategy_code=0,
                token_a="0x1111111111111111111111111111111111111111",
                token_b="0x2222222222222222222222222222222222222222",
                token_c=None,
                dex_buy="uniswap",
                dex_mid=None,
                dex_sell="sushi",
                fee_buy=500,
                fee_mid=0,
                fee_sell=500,
                min_amount_out_buy=0,
                min_amount_out_mid=0,
                min_amount_out_sell=1,
            )
        )

    with pytest.raises(ValueError):
        encode_liquidation_calldata(
            LiquidationCalldataRequest(
                collateral_asset="0x3333333333333333333333333333333333333333",
                debt_asset="0x4444444444444444444444444444444444444444",
                borrower="0x5555555555555555555555555555555555555555",
                debt_to_cover=123456,
                receive_a_token=False,
                sell_dex="uniswap",
                sell_fee=3000,
                amount_out_min=0,
            )
        )
