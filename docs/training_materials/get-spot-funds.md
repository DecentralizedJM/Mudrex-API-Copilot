# Funds (spot)
Source: https://docs.trade.mudrex.com/docs/get-spot-funds
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/wallet/funds" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key"

Response

JSON

{
    "success": true,
    "data": {
        "total": 4.13,
        "rewards": 0,
        "invested": 3.5,
        "withdrawable": 0.63,
        "coin_investable": 0.63,
        "coinset_investable": 0.63,
        "vault_investable": 0.63
    }
}

Parameters

Parameter

Description

total

Total value in your spot wallet across all products.

rewards

Bonus funds earned from promotions, not withdrawable.

invested

Funds currently locked in other Mudrex products.

withdrawable

Amount available to withdraw or transfer to futures.

coin_investable

Amount available for investment in individual coins.

coinset_investable

Amount available for investment in coin sets.

vault_investable

Amount available for investment in vaults.

Updated

2 days ago

Ask AI
