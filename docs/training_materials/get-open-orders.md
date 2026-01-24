# Open orders
Source: https://docs.trade.mudrex.com/docs/get-open-orders
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/orders?limit=2" \
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
            "created_at": "2025-10-08T11:41:01Z",
            "updated_at": "2025-10-08T11:41:01Z",
            "reason": {
                "message": "OK"
            },
            "actual_amount": 222.8,
            "desired_amount": 0,
            "quantity": 0.05,
            "filled_quantity": 0,
            "price": 4456,
            "filled_price": 0,
            "leverage": 80.9,
            "liquidation_price": 0,
            "order_type": "LONG",
            "trigger_type": "LIMIT",
            "status": "CREATED",
            "id": "0199c39f-e866-7d6b-947e-ed2f09c90b8e",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        },
        {
            "created_at": "2025-10-08T11:41:01Z",
            "updated_at": "2025-10-08T11:41:01Z",
            "reason": null,
            "actual_amount": 0,
            "desired_amount": 0,
            "quantity": 0,
            "filled_quantity": 0,
            "price": 30000,
            "filled_price": 0,
            "leverage": 0,
            "liquidation_price": 0,
            "order_type": "TAKEPROFIT",
            "trigger_type": "MARKET",
            "status": "CREATED",
            "id": "0199c39f-e866-7d6e-b5d9-850852495106",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        }
    ]
}

Parameters

Parameter

Description

id

Order ID (UUID). This ID is used for updating or deleting open orders/positions

created_at

Timestamp when the order was created

updated_at

Timestamp when the order was last updated

reason

Reason object containing message (can be null)

actual_amount

Actual amount used for the order

desired_amount

Desired amount for the order

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

liquidation_price

Liquidation price for the position

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

CREATED

)

asset_uuid

UUID of the asset

symbol

Trading symbol (e.g., "ETHUSDT")

Examples

No open orders

JSON

{
    "success": true,
    "data": []
}

Updated

2 days ago

Ask AI
