# May Protocol (MAY)

A minimal over‑collateralized stablecoin system written in **Vyper 0.4.1** with a clean separation between the **Stablecoin (ERC‑20)** and the **Engine** that manages collateral, mint/burn, redemptions, and liquidations. Oracles use Chainlink‑style `AggregatorV3Interface` price feeds.

> This repo contains two core contracts:
>
> * `May Stablecoin` (ERC‑20 via Snekmate modules)
> * `May Engine` (risk/health, collateral accounting, mint/burn, liquidation)

---

## ✨ Features

* **Exogenous collateral** (e.g., WETH, WBTC, USDC) — configurable via constructor.
* **Over‑collateralized minting** — users deposit collateral to mint MAY.
* **Health factor** with liquidation threshold to keep the system solvent.
* **Liquidation flow** with a configurable bonus for liquidators.
* **Deterministic math** with 1e18 fixed‑point precision and feed scaling.

---

## 📦 Contracts

### 1) `May Stablecoin` (`src/may.vy`)

Implemented with Snekmate modules:

* ERC‑20 (name/symbol/decimals: `May Stablecoin` / `MAY` / `18`).
* Ownable, `mint`, `burn_from`, and `set_minter` exposed by the module.
* EIP‑712 metadata initialized for typed signing support in the ERC‑20 module.

Constructor (`@deploy`):

```vyper
ow.__init__()
erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP_712_VERSION)
```

### 2) `May Engine` (`src/engine.vy`)

Handles all protocol logic:

* Collateral deposit / redemption per token.
* Mint / burn MAY for users.
* Health factor checks on every state‑changing path.
* Liquidation with bonus.
* Price feeds via `AggregatorV3Interface`.

Key constants:

* `ADDITIONAL_FEED_PRECISION = 1e10`
* `PRECISION = 1e18`
* `LIQUIDATION_THRESHOLD = 50` (→

