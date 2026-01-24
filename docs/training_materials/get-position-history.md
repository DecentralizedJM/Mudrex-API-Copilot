# Position history
Source: https://docs.trade.mudrex.com/docs/get-position-history
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/history?limit=2" \
  -H "X-Authentication: your-secret-key"

Parameters

Parameter

Type

Required

Description

limit

number

No

Maximum number of records to return (default: 20)

Response

JSON

{
    "success": true,
    "data": [
        {
            "position_type": "LONG",
            "status": "LIQUIDATED",
            "leverage": "80.9",
            "entry_price": "6139.17",
            "closed_price": "6063.29",
            "quantity": "0.05",
            "pnl": "-3.794",
            "created_at": "2025-10-07T11:04:40Z",
            "updated_at": "2025-10-07T11:10:48Z",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        },
        {
            "position_type": "LONG",
            "status": "LIQUIDATED",
            "leverage": "58",
            "entry_price": "4435.8747619047619048",
            "closed_price": "4359.4",
            "quantity": "0.21",
            "pnl": "-16.05970001",
            "created_at": "2025-09-24T07:37:22Z",
            "updated_at": "2025-09-24T07:48:21Z",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        }
    ]
}

Parameters

Parameter

Description

position_type

Position type:

LONG

or

SHORT

status

Position status (e.g.,

LIQUIDATED

,

CLOSED

)

leverage

Leverage used for the position

entry_price

Price at which the position was opened

closed_price

Price at which the position was closed

quantity

Position quantity

pnl

Realised profit and loss for the closed position

created_at

Timestamp when the position was created

updated_at

Timestamp when the position was closed

asset_uuid

UUID of the asset

symbol

Trading symbol (e.g., "ETHUSDT")

Updated

2 days ago

Ask AI
