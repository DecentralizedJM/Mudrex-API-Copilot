# Transfer funds
Source: https://docs.trade.mudrex.com/docs/post-transfer-funds
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/wallet/futures/transfer" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "from_wallet_type": "SPOT",
    "to_wallet_type": "FUTURES", 
    "amount": "10.5"
  }'

Parameters

Field

Type

Required

Description

from_wallet_type

string

Yes

Source wallet:

"SPOT"

or

"FUTURES"

to_wallet_type

string

Yes

Destination wallet: must be opposite of source

amount

string

Yes

Decimal amount to transfer (must be positive)

Response

Status:

202 Accepted

JSON

{
    "success": true,
    "data": {
        "msg": "internal_wallet_fund_transfer_request accepted"
    }
}   d

Examples

Request

JSON

{
    "from_wallet_type": "SPOT",
    "to_wallet_type": "FUTURES",
    "amount": "1"
}

Response

JSON

{
    "success": true,
    "data": {
        "msg": "internal_wallet_fund_transfer_request accepted"
    }
}

Common errors

Same wallet type selected

JSON

{
    "success": false,
    "errors": [
        {
            "code": null,
            "text": "From and To wallet types must be different"
        }
    ]
}

Status:

400 Bad Request

Insufficient funds

JSON

{
    "success": false,
    "errors": [
        {
            "code": null,
            "text": "insufficient balance"
        }
    ]
}

Status:

400 Bad Request

Notes

Transfers are

instant

and

free of fees

You must have sufficient balance in the source wallet

The wallets must be different (

SPOT

↔

FUTURES

only)

Authentication is required for all transfer requests

Updated

2 days ago

Ask AI
