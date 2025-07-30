import boa
from boa.util.abi import Address
from eth.constants import ZERO_ADDRESS
from eth_utils import to_wei
from hypothesis import assume, settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
)
from moccasin.config import get_active_network
from boa.test.strategies import strategy
from script.deploy_may import deploy_may
from script.deploy_may_engine import deploy_may_engine
from src.mocks import MockV3Aggregator

USERS_SIZE = 10  
MAX_DEPOSIT_SIZE = to_wei(1000, "ether")  

class StablecoinFuzzer(RuleBasedStateMachine):

    def __init__(self):
        super().__init__()
        
    @initialize()
    def setup(self):
        self.may = deploy_may()
        self.maye = deploy_may_engine(self.may)

        active_network = get_active_network()
        self.weth = active_network.manifest_named("weth")
        self.wbtc = active_network.manifest_named("wbtc")
        self.eth_usd = active_network.manifest_named("eth_usd_price_feed")
        self.btc_usd = active_network.manifest_named("btc_usd_price_feed")

        self.users = [Address("0x" + ZERO_ADDRESS.hex())]
        while Address("0x" + ZERO_ADDRESS.hex()) in self.users:
            self.users = [boa.env.generate_address() for _ in range(USERS_SIZE)]

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USERS_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE)
    )
    def mint_and_deposit(self, collateral_seed, user_seed, amount):
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed]

        with boa.env.prank(user):
            # Special function added to the mock for the testing purpose
            collateral.mint_amount(amount)
            collateral.approve(self.maye.address, amount)
            self.maye.deposit_collateral(collateral, amount)

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USERS_SIZE - 1),
        percentage=st.integers(min_value=1, max_value=100)
    )
    def redeem_collateral(self, collateral_seed, user_seed, percentage):
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed]

        max_redeemable = self.maye.get_collateral_balance_of_user(user, collateral)
        collateral_to_redeem = (max_redeemable * percentage) // 100
        assume(collateral_to_redeem > 0)

        with boa.env.prank(user):
            self.maye.redeem_collateral(collateral, collateral_to_redeem)

    rule(
        percentage_new_price=st.floats(min_value=0.4, max_value=1.25),
        collateral_seed=st.integers(min_value=0, max_value=1),
    )
    def update_collateral_price(self, percentage_new_price, collateral_seed):
        collateral = self._get_collateral_from_seed(collateral_seed)

        price_feed = MockV3Aggregator.at(self.maye.token_to_price_feed(collateral))

        current_price = price_feed.latestAnswer()
        new_price = int(current_price * percentage_new_price)
        price_feed.updateAnswer(new_price)

    @invariant()
    def protocol_must_have_more_value_than_total_supply(self):
        total_supply = self.may.totalSupply()
        weth_deposited = self.weth.balanceOf(self.maye.address)
        wbtc_deposited = self.wbtc.balanceOf(self.maye.address)

        weth_value = self.maye.get_usd_value(self.weth, weth_deposited)
        wbtc_value = self.maye.get_usd_value(self.wbtc, wbtc_deposited)

        assert (weth_value + wbtc_value) >= total_supply

    def _get_collateral_from_seed(self, seed):
        if seed == 0:
            return self.weth
        return self.wbtc




stablecoin_fuzzer = StablecoinFuzzer.TestCase
stablecoin_fuzzer.settings = settings(max_examples=64, stateful_step_count=64)