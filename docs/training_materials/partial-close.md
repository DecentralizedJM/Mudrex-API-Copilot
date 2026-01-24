# Partial Close
Source: https://docs.trade.mudrex.com/docs/partial-close
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/close/partial" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "order_type": "LIMIT",
    "quantity": "0.01",
    "limit_price": "102.75"
  }'

Parameters

Parameter

Type

Required

Description

position_id

string

Yes

The unique identifier of the position (path parameter)

order_type

string

Yes

Order type:

LIMIT

or

MARKET

quantity

string

Yes

Quantity to close (must be less than the total position quantity)

limit_price

string

Conditional

Required if

order_type

is

LIMIT

. Price at which to close the partial position

Response

JSON

{
    "success": true,
    "data": true
}

Common errors

Position is not open

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "position is not open"
        }
    ]
}

Status:

400 Bad Request

Occurs when attempting to partially close a position that is not currently open.

Updated

2 days ago

Ask AI
