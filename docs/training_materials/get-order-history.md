# Order history
Source: https://docs.trade.mudrex.com/docs/get-order-history
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/orders/history?limit=2" \
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
            "created_at": "2025-10-01T10:37:12Z",
            "updated_at": "2025-10-01T10:37:12Z",
            "reason": null,
            "actual_amount": 398.8752,
            "quantity": 1840,
            "filled_quantity": 1840,
            "price": 0.22118,
            "filled_price": 0.21678,
            "leverage": 25,
            "order_type": "SHORT",
            "trigger_type": "MARKET",
            "status": "FILLED",
            "id": "01999f58-f8cd-73e0-ad02-96b0e3451882",
            "asset_uuid": "01920a1c-88a3-7c9c-a71e-9d2d89dc1999",
            "symbol": "SQDUSDT"
        },
        {
            "created_at": "2025-10-01T10:25:41Z",
            "updated_at": "2025-10-01T10:25:41Z",
            "reason": {
                "message": "OK"
            },
            "actual_amount": 415.4904,
            "quantity": 1840,
            "filled_quantity": 1840,
            "price": 0.22568,
            "filled_price": 0.22581,
            "leverage": 25,
            "order_type": "LONG",
            "trigger_type": "MARKET",
            "status": "FILLED",
            "id": "01999f4e-6da3-7eaa-8339-096300e9b9f5",
            "asset_uuid": "01920a1c-88a3-7c9c-a71e-9d2d89dc1999",
            "symbol": "SQDUSDT"
        }
    ]
}

Parameters

Parameter

Description

id

Order ID (UUID)

created_at

Timestamp when the order was created

updated_at

Timestamp when the order was last updated

reason

Reason object containing message (can be null)

actual_amount

Actual amount used for the order

quantity

Order quantity

filled_quantity

Quantity that has been filled

price

Order price

filled_price

Average price at which the order has been filled

leverage

Leverage used for the order

order_type

Type of order:

LONG

,

SHORT

, or

TAKEPROFIT

trigger_type

Trigger type:

MARKET

or

LIMIT

status

Order status (e.g.,

FILLED

)

asset_uuid

UUID of the asset

symbol

Trading symbol (e.g., "SQDUSDT")

Updated

2 days ago

Ask AI
