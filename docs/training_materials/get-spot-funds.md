# Funds (spot)
Source: https://docs.trade.mudrex.com/docs/get-spot-funds
Date Scraped: 2026-01-24

---

Request

API

GET /fapi/v1/wallet/funds — auth: X-Authentication only (no HMAC, no signature).

curl -X GET "https://trade.mudrex.com/fapi/v1/wallet/funds" \
  -H "X-Authentication: your-secret-key"

Python (only X-Authentication; no HMAC, no signature):

```python
import requests
r = requests.get(
    "https://trade.mudrex.com/fapi/v1/wallet/funds",
    headers={"X-Authentication": "your_api_secret"}
)
print(r.json())
```

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
