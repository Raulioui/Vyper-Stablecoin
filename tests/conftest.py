import boa
import pytest
from eth_account import Account
from eth_utils import to_wei
from moccasin.config import get_active_network

from script.deploy_may_engine import deploy_may_engine

BALANCE = to_wei(10, "ether")
COLLATERAL_AMOUNT = to_wei(10, "ether")
AMOUNT_TO_MINT = to_wei(100, "ether")
COLLATERAL_TO_COVER = to_wei(20, "ether")

# ------------------------------------------------------------------
#                         SESSION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def active_network():
    return get_active_network()


@pytest.fixture(scope="session")
def weth(active_network):
    return active_network.manifest_named("weth")


@pytest.fixture(scope="session")
def wbtc(active_network):
    return active_network.manifest_named("wbtc")


@pytest.fixture(scope="session")
def eth_usd(active_network):
    return active_network.manifest_named("eth_usd_price_feed")


@pytest.fixture(scope="session")
def btc_usd(active_network):
    return active_network.manifest_named("btc_usd_price_feed")

@pytest.fixture(scope="session")
def some_user(weth, wbtc):
    entropy = 13
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint()
        wbtc.mock_mint()
    return account.address


# ------------------------------------------------------------------
#                        FUNCTION SCOPED
# ------------------------------------------------------------------

@pytest.fixture
def may(active_network):
    return active_network.manifest_named("may")


@pytest.fixture
def maye(may, weth, wbtc, eth_usd, btc_usd):
    return deploy_may_engine(may)

@pytest.fixture
def maye_deposited(maye, some_user, weth):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral(weth, COLLATERAL_AMOUNT)
    return maye

@pytest.fixture
def maye_minted(maye, some_user, weth):
    with boa.env.prank(some_user):
        weth.approve(maye.address, COLLATERAL_AMOUNT)
        maye.deposit_collateral_and_mint_may(
            weth.address, COLLATERAL_AMOUNT, AMOUNT_TO_MINT
        )
    return maye