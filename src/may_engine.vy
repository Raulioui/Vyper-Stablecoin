# pragma version 0.4.1

"""
@license MIT
@title May Protocol Engine
@author rauloiui
@notice 
    Collateral: Exogenous (WETH, WBTC, USDC, etc.)
    Stability Mechanism(Minting): Decentralized (Algorithmic)
    Value (Relative Stability): Anchored (Pegged to the USD)
"""

from ethereum.ercs import IERC20
from src.interfaces import AggregatorV3Interface
from src.interfaces import i_decentralized_stable_coin

# ------------------------------------------------------------------
#                        EVENTS
# ------------------------------------------------------------------

event CollateralDeposited:
    user: indexed(address)
    collateral_token: indexed(address)
    amount: uint256

event CollateralRedeemed:
    collateral_token: indexed(address)
    amount: uint256
    _from: indexed(address)
    _to: indexed(address)

# ------------------------------------------------------------------
#                        STATE VARIABLES
# ------------------------------------------------------------------

MAY: public(immutable(i_decentralized_stable_coin))
COLLATERAL_TOKENS: public(immutable(address[2]))

token_to_price_feed: public(HashMap[address, address])
ADDITIONAL_FEED_PRECISION: public(constant(uint256)) = 1 * (10 ** 10)
PRECISION: public(constant(uint256)) = 1 * (10 ** 18)
LIQUIDATION_THRESHOLD: public(constant(uint256)) = 50
LIQUIDATION_PRECISION: public(constant(uint256)) = 100
LIQUIDATION_BONUS: public(constant(uint256)) = 10 # 10% bonus for liquidators

# Minimum health factor to avoid liquidation (has to be greater than 1)
MIN_HEALTH_FACTOR: public(constant(uint256)) = 1 * (10**18)

# user -> token -> amount deposited
user_to_token_to_amount_deposited: public(HashMap[address, HashMap[address, uint256]])
user_to_may_minted: public(HashMap[address, uint256])

# ------------------------------------------------------------------
#                       EXTERNAL FUNCTIONS
# ------------------------------------------------------------------

@deploy
def __init__(
    token_addresses: address[2], # [ETH, WBTC]
    price_feed_addresses: address[2],
    may_address: address,
):
    MAY = i_decentralized_stable_coin(may_address)
    COLLATERAL_TOKENS = token_addresses
    # This is gas inefficient!
    self.token_to_price_feed[token_addresses[0]] = price_feed_addresses[0]
    self.token_to_price_feed[token_addresses[1]] = price_feed_addresses[1]

@external
def mint_may(amount: uint256):
    self._mint_may(amount)
    
@external
def deposit_collateral(collateral_token: address, amount: uint256):
    self._deposit_collateral(collateral_token, amount)

@external
def redeem_collateral(collateral_token: address, amount: uint256):
    self._redeem_collateral(collateral_token, amount, msg.sender, msg.sender)
    self._revert_if_health_factor_broken(msg.sender)

@external
def redeem_collateral_for_may(collateral_token: address, amount: uint256, amount_may: uint256):
    self._burn_may(amount_may, msg.sender, msg.sender)
    self._redeem_collateral(collateral_token, amount, msg.sender, msg.sender)
    self._revert_if_health_factor_broken(msg.sender)

@external
def burn_may(amount: uint256):
    self._burn_may(amount, msg.sender, msg.sender)
    self._revert_if_health_factor_broken(msg.sender)

@external
def deposit_collateral_and_mint_may(
    token_collateral_address: address,
    amount_collateral: uint256,
    amount_may_to_mint: uint256,
):
    self._deposit_collateral(token_collateral_address, amount_collateral)
    self._mint_may(amount_may_to_mint)
    
@external 
def liquidate(collateral_token: address, user_to_liquidate: address, debt_amount_in_usd: uint256):
    assert debt_amount_in_usd > 0, "MAY_ENGINE: Debt amount must be greater than zero"

    starting_health_factor: uint256 = self._health_factor(user_to_liquidate)
    assert starting_health_factor < MIN_HEALTH_FACTOR, "MAY_ENGINE: Health factor is above threshold"

    token_amount_from_debt: uint256 = self._get_token_amount_from_usd(
        collateral_token, debt_amount_in_usd
    )

    liquidation_bonus: uint256 = (token_amount_from_debt * LIQUIDATION_BONUS) // LIQUIDATION_PRECISION
    self._redeem_collateral(collateral_token, token_amount_from_debt + liquidation_bonus, user_to_liquidate, msg.sender)
    self._burn_may(debt_amount_in_usd, user_to_liquidate, msg.sender)

    ending_health_factor: uint256 = self._health_factor(user_to_liquidate)
    assert ending_health_factor > starting_health_factor, "MAY_ENGINE: Health factor did not  improve"
    self._revert_if_health_factor_broken(msg.sender)
    

# ------------------------------------------------------------------
#                       INTERNAL FUNCTIONS
# ------------------------------------------------------------------

@internal
def _deposit_collateral(collateral_token: address, amount: uint256):
    assert amount > 0, "MAY_ENGINE: Amount must be greater than zero"
    assert self.token_to_price_feed[collateral_token] != empty(address), "MAY_ENGINE: Collateral not supported"

    self.user_to_token_to_amount_deposited[msg.sender][collateral_token] += amount

    #log CollateralDeposited(msg.sender, collateral_token, amount)

    success: bool = extcall IERC20(collateral_token).transferFrom(msg.sender, self, amount)
    assert success, "MAY_ENGINE: Transfer failed"

@internal 
def _mint_may(amount: uint256):
    assert amount > 0, "MAY_ENGINE: Amount must be greater than zero"
    self.user_to_may_minted[msg.sender] += amount
    self._revert_if_health_factor_broken(msg.sender)
    extcall MAY.mint(msg.sender, amount)

@internal 
def _burn_may(amount: uint256, on_behalf_of: address, may_from: address):
    self.user_to_may_minted[on_behalf_of] -= amount
    extcall MAY.burn_from(may_from, amount)

@internal 
def _redeem_collateral(collateral_token: address, amount: uint256, _from: address, _to: address):
    self.user_to_token_to_amount_deposited[_from][collateral_token] -= amount
   # log CollateralRedeemed(collateral_token, amount, _from, _to)

    success: bool = extcall IERC20(collateral_token).transfer(_to, amount)
    assert success, "MAY_ENGINE: Transfer failed"
    

@internal 
def _revert_if_health_factor_broken(user: address):
    user_health_factor: uint256 = self._health_factor(user)
    assert user_health_factor >= MIN_HEALTH_FACTOR, "MAY_ENGINE: Health factor is below threshold"

# ------------------------------------------------------------------
#                PURE AND VIEW EXTERNAL FUNCTIONS
# ------------------------------------------------------------------

@external
@view
def health_factor(user: address) -> uint256:
    return self._health_factor(user)

@external
@pure
def calculate_health_factor(
    total_may_minted: uint256, collateral_value_in_usd: uint256
) -> uint256:
    return self._calculate_health_factor(
        total_may_minted, collateral_value_in_usd
    )

@external
@view
def get_account_information(user: address) -> (uint256, uint256):
    return self._get_account_information(user)

@external
@view
def get_usd_value(token: address, amount: uint256) -> uint256:
    return self._get_usd_value(token, amount)

@external
@view
def get_collateral_balance_of_user(user: address, collateral_token: address) -> uint256:
    return self.user_to_token_to_amount_deposited[user][collateral_token]

@external
@view
def get_account_collateral_value(user: address) -> uint256:
    return self._get_account_collateral_value(user)


@external
@view
def get_token_amount_from_usd(
    token: address, usd_amount_in_wei: uint256
) -> uint256:
    return self._get_token_amount_from_usd(token, usd_amount_in_wei)


@external
@view
def get_collateral_tokens() -> address[2]:
    return COLLATERAL_TOKENS

# ------------------------------------------------------------------
#                PURE AND VIEW INTERNAL FUNCTIONS
# ------------------------------------------------------------------

@internal
@view
def _get_account_information(user: address) -> (uint256, uint256):
    total_may_minted: uint256 = self.user_to_may_minted[user]
    collateral_value_in_usd: uint256 = self._get_account_collateral_value(user)
    return total_may_minted, collateral_value_in_usd


@internal
@view
def _get_user_info(user: address) -> (uint256, uint256):
    total_may_minted: uint256 = self.user_to_may_minted[user]
    collateral_value_in_usd: uint256 = self._get_collateral_value_in_usd(user)

    return total_may_minted, collateral_value_in_usd

@internal 
@view
def _health_factor(user: address) -> uint256:
    total_may_minted: uint256 = 0
    collateral_value_in_usd: uint256 = 0

    total_may_minted, collateral_value_in_usd = self._get_user_info(user)

    return self._calculate_health_factor(
        total_may_minted, collateral_value_in_usd
    )

@internal
@view
def _get_usd_value(token: address, amount: uint256) -> uint256:
    price_feed: AggregatorV3Interface = AggregatorV3Interface(self.token_to_price_feed[token])
    price: int256 = staticcall price_feed.latestAnswer()
    return (((convert(price, uint256) * ADDITIONAL_FEED_PRECISION)) * amount) // PRECISION

@internal
@pure
def _calculate_health_factor(
    total_may_minted: uint256, collateral_value_in_usd: uint256
) -> uint256:
    if total_may_minted == 0:
        return max_value(uint256)
    collateral_adjusted_for_threshold: uint256 = (
        collateral_value_in_usd * LIQUIDATION_THRESHOLD
    ) // LIQUIDATION_PRECISION
    return (collateral_adjusted_for_threshold * (10**18)) // total_may_minted

@internal
@view
def _get_account_collateral_value(user: address) -> uint256:
    total_collateral_value_in_usd: uint256 = 0
    for token: address in COLLATERAL_TOKENS:
        amount: uint256 = self.user_to_token_to_amount_deposited[user][token]
        total_collateral_value_in_usd += self._get_usd_value(token, amount)
    return total_collateral_value_in_usd

@internal 
@view
def _get_collateral_value_in_usd(user: address) -> uint256:
    total_value: uint256 = 0
    for token: address in COLLATERAL_TOKENS:
        amount: uint256 = self.user_to_token_to_amount_deposited[user][token]
        total_value += self._get_usd_value(token, amount)
    return total_value
        

@internal
@view
def _get_token_amount_from_usd(
    collateral_token: address, usd_amount_in_wei: uint256
) -> uint256:
    price_feed: AggregatorV3Interface = AggregatorV3Interface(
        self.token_to_price_feed[collateral_token]
    )
    price: int256 = staticcall price_feed.latestAnswer()
    return (
        (usd_amount_in_wei * PRECISION) // (
            convert(price, uint256) * ADDITIONAL_FEED_PRECISION
        )
    )


    

    

    