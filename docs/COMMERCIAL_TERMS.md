# Commercial profit sharing and payment

English | [繁體中文](COMMERCIAL_TERMS.zh-TW.md)

Licensor: teateatea03. Applicable version: [Novel OS Source-Available and Commercial Profit-Sharing License 1.0](../LICENSE). This page collects payment details; the license terms are governed by LICENSE.

## Simple rules

- Noncommercial use is free. Modification and redistribution are permitted while retaining the license and third-party notices; modified versions remain under the same terms
- For commercial use, aggregate annual revenue from related products, services, and novels, then deduct actual reasonable costs, expenses, and taxes. Pay 0.5% of positive net profit; nothing is payable without positive net profit. Losses cannot be carried across years
- Existing related items remain covered in years when they continue to earn profits. Unrelated business is excluded, and rights to novels and other outputs do not transfer to the system provider
- Settle by calendar year and self-report and pay by March 31 of the following year. Convert to US dollars using the user's consistent accounting exchange rate and state its source and date
- Each US dollar payable corresponds to 1 USDT or 1 USDC; the payer bears network fees. This agreement does not guarantee stablecoin market prices, reserves, or redeemability

## Receiving network and address

The following two Binance-Peg tokens on **BNB Smart Chain mainnet (BSC, chain ID 56)** are accepted and share the same receiving address. Do not use opBNB, Ethereum, testnets, or another network.

**Receiving address:** `0xE35023A45F4d7c8e070D335Db6Cc4C5c9a3Fe4Bd`

- **USDT / Binance-Peg BSC-USD**, BEP-20, 18 decimals; token contract: `0x55d398326f99059ff775485246999027b3197955`
- **USDC / Binance-Peg USD Coin**, BEP-20, 18 decimals; token contract: `0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d`

**Token contracts identify the token; they are not the payment receiving address. Do not send payments to a token contract.** The contracts were checked against the [official BNB Chain list](https://github.com/bnb-chain/mpp-sdk/blob/801eb5db2d1d615755d29944e1f7178d26d349d6/src/server/curated.ts) and BscScan's [USDT](https://bscscan.com/token/0x55d398326f99059ff775485246999027b3197955) / [USDC](https://bscscan.com/token/0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d) records on 2026-10-01. These are Binance-Peg versions, not described as versions natively issued by their issuers on BSC.

The receiving address has only passed offline format and EIP-55 checksum checks. No actual receipt test has been performed, and wallet or exchange deposit support has not been verified. Before the first payment, confirm the current receiving details and support with the maintainer, and have the wallet holder independently verify with a small amount. An on-chain transaction can prove a transfer, but cannot prove annual net profit.

## Acceptance and reporting

Before commercial use, explicitly accept the license version above and retain a written or electronic record. You may first open an issue in this GitHub repository without financial information, stating that you want to discuss commercial licensing and identifying the version accepted. Do not post financial summaries, payment transaction details, or private works in public issues; first confirm a private reporting channel separately.

Each year, prepare your own summary of covered items, related revenue, total deductible costs and taxes, net profit, the 0.5% amount payable, and currency conversion. After payment, retain the transaction hash and confirm the receipt through the agreed private channel. There is no secret tracking, compulsory auditing, or automatic debiting, and no need to provide private keys, seed phrases, or wallet-connection authorization.
