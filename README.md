# May Protocol Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vyper](https://img.shields.io/badge/Vyper-0.4.1-blue.svg)](https://vyper.readthedocs.io/)

A decentralized stablecoin protocol built on Ethereum using Vyper, featuring over-collateralized positions and algorithmic stability mechanisms.

## Overview

May Protocol is a decentralized stablecoin system that allows users to mint MAY tokens (pegged to USD) by depositing approved collateral assets. The protocol maintains stability through over-collateralization and automated liquidation mechanisms.

### Key Features

- **🏦 Over-Collateralized**: Requires 200% collateralization ratio (50% liquidation threshold)
- **⚡ Decentralized**: No central authority controls the system
- **🔒 Multi-Collateral**: Supports WETH, WBTC, and other approved tokens
- **📊 Price Oracle Integration**: Uses Chainlink price feeds for accurate valuations
- **🔄 Liquidation System**: Automated liquidation with 10% liquidator incentive
- **💎 Health Factor Monitoring**: Real-time solvency tracking

## Protocol Mechanics

### Collateralization
- **Minimum Health Factor**: 1.0 (100% backed)
- **Liquidation Threshold**: 50% (200% over-collateralized)
- **Liquidation Bonus**: 10% for liquidators

### Supported Collateral
- WETH (Wrapped Ethereum)
- WBTC (Wrapped Bitcoin)
- Additional tokens can be added through governance

## Smart Contract Architecture

```
May Protocol Engine (Core Contract)
├── Collateral Management
├── MAY Token Minting/Burning
├── Health Factor Calculations
├── Liquidation System
└── Price Oracle Integration
```

## Installation

### Prerequisites
- Python 3.8+
- Vyper 0.4.1+
- Foundry or Hardhat for testing

### Setup
```bash

# Install dependencies
pip install vyper

# Compile contracts
vyper src/MayEngine.vy
```

## Usage

### For Users

#### Deposit Collateral and Mint MAY
```python
# Deposit 1 ETH as collateral and mint 1000 MAY tokens
engine.deposit_collateral_and_mint_may(
    WETH_ADDRESS,      # Collateral token
    1 * 10**18,        # 1 ETH
    1000 * 10**18      # 1000 MAY tokens
)
```

#### Check Health Factor
```python
health_factor = engine.health_factor(user_address)
# Health factor > 1.0 = Safe
# Health factor < 1.0 = Subject to liquidation
```

#### Redeem Collateral
```python
# Burn MAY tokens and redeem collateral
engine.redeem_collateral_for_may(
    WETH_ADDRESS,      # Collateral token to redeem
    0.5 * 10**18,      # 0.5 ETH to redeem
    500 * 10**18       # 500 MAY tokens to burn
)
```

### For Liquidators

```python
# Liquidate an undercollateralized position
engine.liquidate(
    collateral_token,    # Token to claim as collateral
    user_to_liquidate,   # Address of user to liquidate
    debt_amount          # Amount of debt to cover (in USD)
)
```

## API Reference

### Core Functions

#### `deposit_collateral(collateral_token: address, amount: uint256)`
Deposits approved collateral tokens into the protocol.

#### `mint_may(amount: uint256)`
Mints MAY tokens against deposited collateral.

#### `burn_may(amount: uint256)`
Burns MAY tokens to improve health factor.

#### `redeem_collateral(collateral_token: address, amount: uint256)`
Redeems collateral tokens from the protocol.

#### `liquidate(collateral_token: address, user_to_liquidate: address, debt_amount_in_usd: uint256)`
Liquidates undercollateralized positions.

### View Functions

#### `health_factor(user: address) -> uint256`
Returns the health factor for a specific user.

#### `get_account_information(user: address) -> (uint256, uint256)`
Returns total MAY minted and collateral value in USD.

#### `get_usd_value(token: address, amount: uint256) -> uint256`
Converts token amount to USD value using oracle prices.

## Security Considerations

- ⚠️ **Oracle Risk**: Relies on Chainlink price feeds
- ⚠️ **Liquidation Risk**: Positions can be liquidated if health factor < 1.0
- ⚠️ **Smart Contract Risk**: Unaudited code - use at your own risk
- ⚠️ **Market Risk**: Collateral value fluctuations affect position safety

## Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Check coverage
pytest --cov=src tests/
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is experimental and unaudited. Use at your own risk. The authors are not responsible for any losses incurred through the use of this protocol.

## Contact

- **Author**: rauloiui

## Acknowledgments

- Chainlink for price oracle infrastructure
- MakerDAO for stablecoin design inspiration
- Vyper community for language support

---

*Built with ❤️ using Vyper*
