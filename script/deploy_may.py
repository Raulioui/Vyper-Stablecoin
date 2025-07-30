from moccasin.config import get_active_network

from src import may


def deploy_may():
    may_contract = may.deploy()

    active_network = get_active_network()

    # Verify
    if active_network.has_explorer():
        print("Verifying contract on explorer...")
        result = active_network.moccasin_verify(may_contract)
        result.wait_for_verification()
    print(f"Deployed MAY contract at {may_contract.address}")
    return may_contract


def moccasin_main():
    return deploy_may()