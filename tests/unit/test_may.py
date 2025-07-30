import boa

ZERO = "0x0000000000000000000000000000000000000000"


def test_cannot_mint_to_zero_address(may):
    with boa.env.prank(may.owner()):
        with boa.reverts():
            may.mint(ZERO, 0)


def test_cant_burn_more_than_you_have(may):
    with boa.env.prank(may.owner()):
        with boa.reverts():
            may.burn_from(may.owner(), 1)

