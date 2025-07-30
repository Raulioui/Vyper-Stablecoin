# pragma version 0.4.1

"""
@license MIT
@title May Protocol Stablecoin
@author rauloiui
"""

from snekmate.tokens import erc20
from snekmate.auth import ownable as ow 

initializes: ow
initializes: erc20[ownable := ow]

exports: (
    erc20.IERC20,
    erc20.IERC20Detailed,
    erc20.burn_from,
    erc20.mint,
    erc20.set_minter,
    ow.owner,
    ow.transfer_ownership,
)

NAME: constant(String[25]) = "May Stablecoin"
SYMBOL: constant(String[3]) = "MAY"
DECIMALS: constant(uint8) = 18
EIP_712_VERSION: constant(String[20]) = "1"


@deploy 
def __init__():
    ow.__init__()
    erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP_712_VERSION)