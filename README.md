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
* `LIQUIDATION_THRESHOLD = 50` (→ 50%)
* `LIQUIDATION_PRECISION = 100`
* `LIQUIDATION_BONUS = 10` (→ +10% collateral to liquidator)
* `MIN_HEALTH_FACTOR = 1e18` (must stay ≥ 1e18)

---

## 🧮 Math & Risk

### Health Factor (HF)

```
HF = (CollateralValueUSD * LIQUIDATION_THRESHOLD / LIQUIDATION_PRECISION) * 1e18 / TotalMAYMinted
```

* If `TotalMAYMinted == 0` → returns `max(uint256)`.
* Liquidation is allowed when HF < `MIN_HEALTH_FACTOR` (1e18).

### Oracle Scaling

* Price feeds are assumed to return **8‑decimals** integers (typical Chainlink USD feeds).
* Conversion uses:

```
USD = price * 1e10 * amount / 1e18
```

Where `amount` is in token wei (assuming token has 18 decimals). Adjust if a collateral token has a different number of decimals (see "Limitations").

### Liquidation

* Liquidator targets a user with HF < 1e18.
* Chooses a collateral and a debt amount (in USD)
* Protocol computes token amount equivalent to that USD and grants **+10% bonus** in collateral, then burns the corresponding MAY from the user (paid by liquidator as `may_from`).

---

## 🔗 External Interfaces

* `IERC20` transfer/transferFrom used for collateral flows.
* `AggregatorV3Interface.latestAnswer()` used for spot pricing (no staleness checks in this minimal version).
* `i_decentralized_stable_coin` used by the Engine:

  * `mint(address,uint256)`
  * `burn_from(address,uint256)`

---

## 🚀 Quickstart

> Tooling is flexible (Ape, Brownie, Foundry‑vyper). Below is a generic flow.

1. **Deploy MAY**

   * Owner deploys `May Stablecoin`.
   * Set the Engine as a **minter** (via `set_minter` in the ERC‑20 module) or mint directly during tests.

2. **Deploy Engine**

   * Provide `token_addresses` (e.g., `[WETH, WBTC]`), `price_feed_addresses` (matching each token), and `may_address`.

3. **Fund collateral**

   * Users approve Engine to spend collateral and call `deposit_collateral(token, amount)`.

4. **Mint**

   * Call `mint_may(amount)` or `deposit_collateral_and_mint_may(token, collateralAmount, mayToMint)`.
   * The Engine checks your HF post‑mint; reverts if below threshold.

5. **Redeem**

   * `redeem_collateral(token, amount)` or `redeem_collateral_for_may(token, amount, burnAmount)`.

6. **Liquidate**

   * If a user’s HF < 1e18, call `liquidate(token, user, debtUsd)`. You receive collateral + bonus; the user’s MAY debt is burned.

---


