from src import may_engine
import pytest
from eth.codecs.abi.exceptions import EncodeError
from tests.conftest import (
    COLLATERAL_AMOUNT,
    AMOUNT_TO_MINT,
    COLLATERAL_TO_COVER,
    some_user,
)
import boa
from eth_utils import to_wei

LIQUIDATION_THRESHOLD = 50
MIN_HEALTH_FACTOR = to_wei(1, "ether")


# ------------------------- INIT -------------------------


def test_reverts_if_token_lengths_are_different(may, eth_usd, btc_usd, weth, wbtc):
    with pytest.raises(EncodeError):
        may_engine.deploy([wbtc, weth, weth], [eth_usd, btc_usd], may.address)


# ------------------------- MINT MAY -------------------------


def test_reverts_if_minting_amount_is_zero(maye, some_user, weth):
    with boa.env.prank(some_user):
        with boa.reverts("MAY_ENGINE: Amount must be greater than zero"):
            maye.mint_may(0)

def test_reverts_if_mint_amount_breaks_health_factor(maye_deposited, eth_usd, some_user, weth):
    price = eth_usd.latestRoundData()[1]
    amount_to_mint = (
        COLLATERAL_AMOUNT * (price * maye_deposited.ADDITIONAL_FEED_PRECISION())
    ) // maye_deposited.PRECISION()

    with boa.env.prank(some_user):
        maye_deposited.calculate_health_factor(
            amount_to_mint, maye_deposited.get_usd_value(weth, COLLATERAL_AMOUNT)
        )
        with boa.reverts("MAY_ENGINE: Health factor is below threshold"):
            maye_deposited.mint_may(amount_to_mint)

def test_mint_may_success(maye, weth, some_user, may):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)

        maye.mint_may(AMOUNT_TO_MINT)

        assert maye.user_to_may_minted(some_user) == AMOUNT_TO_MINT
        assert may.balanceOf(some_user) == AMOUNT_TO_MINT
        

# ------------------------- DEPOSIT COLLATERAL -------------------------


def test_reverts_if_collateral_is_zero(maye, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        with boa.reverts("MAY_ENGINE: Amount must be greater than zero"):
            maye.deposit_collateral(maye.address, 0)

def test_reverts_if_collateral_is_not_supported(maye, some_user, weth, eth_usd):
    with boa.env.prank(some_user):
        with boa.reverts("MAY_ENGINE: Collateral not supported"):
            maye.deposit_collateral(eth_usd.address, COLLATERAL_AMOUNT)

def test_deposit_collateral_success(maye, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)

        assert maye.user_to_token_to_amount_deposited(some_user, weth) == COLLATERAL_AMOUNT
        assert weth.balanceOf(maye.address) == COLLATERAL_AMOUNT
        assert maye.get_collateral_balance_of_user(some_user, weth) == COLLATERAL_AMOUNT


# ------------------------- DEPOSIT AND MINT -------------------------


def test_deposit_and_mint_success(maye, weth, some_user, may):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral_and_mint_may(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)

        assert maye.user_to_token_to_amount_deposited(some_user, weth) == COLLATERAL_AMOUNT
        assert weth.balanceOf(maye.address) == COLLATERAL_AMOUNT
        assert maye.get_collateral_balance_of_user(some_user, weth) == COLLATERAL_AMOUNT
        assert maye.user_to_may_minted(some_user) == AMOUNT_TO_MINT
        assert may.balanceOf(some_user) == AMOUNT_TO_MINT


# ------------------------- REDEEM COLLATERAL -------------------------


def test_redeems_collateral_success(maye, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)

        maye.redeem_collateral(weth, COLLATERAL_AMOUNT)

        assert maye.user_to_token_to_amount_deposited(some_user, weth) == 0
        assert weth.balanceOf(some_user) == COLLATERAL_AMOUNT


def test_redeems_for_may_success(maye, weth, some_user, may):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        may.approve(maye.address, AMOUNT_TO_MINT)
        maye.deposit_collateral_and_mint_may(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
        maye.redeem_collateral_for_may(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
        user_balance = may.balanceOf(some_user)
        assert user_balance == 0


# ------------------------- LIQUIDATE -------------------------


def test_reverts_if_debt_amount_is_zero(maye, weth, some_user):
    with boa.reverts("MAY_ENGINE: Debt amount must be greater than zero"):
        maye.liquidate(weth, some_user, 0)

def test_reverts_if_health_factor_is_above_threshold(maye, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)

    with boa.reverts("MAY_ENGINE: Health factor is above threshold"):
        maye.liquidate(weth, some_user, AMOUNT_TO_MINT)

def test_reverts_if_health_factor_did_not_improve(maye, weth, some_user, eth_usd):
    pass
    

# ------------------------- HEALTH FACTOR -------------------------


def test_reverts_if_health_factor_is_below_threshold(maye, weth, some_user):
    with boa.env.prank(some_user):
        with boa.reverts("MAY_ENGINE: Health factor is below threshold"):
            maye.mint_may(AMOUNT_TO_MINT)


# ------------------------- PRICE TESTS -------------------------

def test_get_token_amount_from_usd(maye, weth):
    expected_weth = to_wei(0.05, "ether")
    actual_weth = maye.get_token_amount_from_usd(weth, to_wei(100, "ether"))
    assert expected_weth == actual_weth


def test_get_usd_value(maye, weth):
    eth_amount = to_wei(15, "ether")
    expected_usd = to_wei(30_000, "ether")
    actual_usd = maye.get_usd_value(weth, eth_amount)
    assert expected_usd == actual_usd

# ------------------------- BURN MAY -------------------------

def test_cant_burn_more_than_user_has(maye, may, some_user):
    with boa.env.prank(some_user):
        may.approve(maye, 1)
        with boa.reverts():
            maye.burn_may(1)


def test_can_burn_may(maye_minted, may, some_user):
    with boa.env.prank(some_user):
        may.approve(maye_minted, AMOUNT_TO_MINT)
        maye_minted.burn_may(AMOUNT_TO_MINT)
        user_balance = may.balanceOf(some_user)
        assert user_balance == 0

# ------------------------------------------------------------------
#                    VIEW & PURE FUNCTION TESTS
# ------------------------------------------------------------------
def test_get_collateral_token_price_feed(maye, weth, eth_usd):
    price_feed = maye.token_to_price_feed(weth)
    assert price_feed == eth_usd.address


def test_get_collateral_tokens(maye, weth):
    collateral_tokens = maye.get_collateral_tokens()
    assert collateral_tokens[0] == weth.address


def test_get_min_health_factor(maye):
    min_health_factor = maye.MIN_HEALTH_FACTOR()
    assert min_health_factor == MIN_HEALTH_FACTOR


def test_get_liquidation_threshold(maye):
    liquidation_threshold = maye.LIQUIDATION_THRESHOLD()
    assert liquidation_threshold == LIQUIDATION_THRESHOLD


def test_get_account_collateral_value_from_information(maye_deposited, some_user, weth):
    _, collateral_value = maye_deposited.get_account_information(some_user)
    expected_collateral_value = maye_deposited.get_usd_value(weth, COLLATERAL_AMOUNT)
    assert collateral_value == expected_collateral_value


def test_get_collateral_balance_of_user(maye, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(maye, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)

    collateral_balance = maye.get_collateral_balance_of_user(some_user, weth)
    assert collateral_balance == COLLATERAL_AMOUNT


def test_get_account_collateral_value(maye, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(maye, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)

    collateral_value = maye.get_account_collateral_value(some_user)
    expected_collateral_value = maye.get_usd_value(weth, COLLATERAL_AMOUNT)
    assert collateral_value == expected_collateral_value


def test_get_may(maye, may):
    may_address = maye.MAY()
    assert may_address == may.address


def test_liquidation_precision(maye):
    expected_liquidation_precision = 100
    actual_liquidation_precision = maye.LIQUIDATION_PRECISION()
    assert actual_liquidation_precision == expected_liquidation_precision