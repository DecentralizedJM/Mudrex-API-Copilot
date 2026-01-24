# Funds (futures)
Source: https://docs.trade.mudrex.com/docs/get-available-funds-futures
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/funds" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key"

Response

JSON

{
    "success": true,
    "data": {
        "balance": "12.6787",
        "locked_amount": "1.6979",
        "first_time_user": false
    }
}

Parameters

balance

: investable balance in futures wallet

locked_amount

: locked balance in futures wallet

first_time_user

: first time user

Updated

2 days ago

Ask AI
