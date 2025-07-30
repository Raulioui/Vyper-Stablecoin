from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network
from src import may_engine

def deploy_may_engine(may: VyperContract):
    active_network = get_active_network()

    btc_usd = active_network.manifest_named("btc_usd_price_feed")   
    eth_usd = active_network.manifest_named("eth_usd_price_feed")
    wbtc = active_network.manifest_named("wbtc")
    weth = active_network.manifest_named("weth")

    engine = may_engine.deploy(
        [weth.address, wbtc.address],
        [eth_usd, btc_usd],
        may
    )

    may.set_minter(engine.address, True)
    may.transfer_ownership(engine.address)

    return engine

def moccasin_main():
    active_network = get_active_network()
    may = active_network.manifest_named("may")
    return deploy_may_engine(may)