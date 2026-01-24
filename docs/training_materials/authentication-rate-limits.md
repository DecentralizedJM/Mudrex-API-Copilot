# Authentication & Rate Limits
Source: https://docs.trade.mudrex.com/docs/authentication-rate-limits
Date Scraped: 2026-01-24

---

Authentication

Mudrex enforces strong security measures. To call any private endpoint, you must:

Verify your identity

: Complete KYC verification (PAN & Aadhaar) and enable two-factor authentication for your Mudrex account.

Generate an API key

: In your dashboard, create an API key. Copy the secret and store it securely, as it will not be displayed again.

All endpoints under

/fapi/v1

require the following headers:

Header

Value

Required

X-Authentication

your_api_secret

Yes

Content-Type

application/json

Only for POST/PATCH/DELETE requests

Example Request

Shell

curl -X POST https://trade.mudrex.com/fapi/v1/futures/<asset_id>/order \
  -H "Content-Type: application/json" \
  -H "X-Authentication: <secret-key>" \
  -d '{
    "leverage": "5",
    "quantity": "0.001",
    "order_price": "107526",
    "order_type": "LONG",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true,
    "stoploss_price": "106900",
    "takeprofit_price": "110000",
    "reduce_only": false
  }'

Rate Limits

The following rate limits are enforced per API key:

Duration

Limit

Second

2

Minute

50

Hour

1000

Day

10000

Updated

2 days ago

Quickstart

Ask AI
