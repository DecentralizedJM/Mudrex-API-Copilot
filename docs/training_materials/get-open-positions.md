# Open Positions
Source: https://docs.trade.mudrex.com/docs/get-open-positions
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions" \
  -H "X-Authentication: your-secret-key"

Response

JSON

{
    "success": true,
    "data": [
        {
            "created_at": "2025-10-01T06:27:17Z",
            "updated_at": "2025-10-01T06:31:15Z",
            "stoploss": {
                "price": "4100",
                "order_id": "01999e77-8eab-79aa-8db3-8cc0624c7d0e",
                "order_type": "SHORT"
            },
            "takeprofit": {
                "price": "5000",
                "order_id": "01999e77-8eab-79ad-b3f0-22ee1e8e81d6",
                "order_type": "SHORT"
            },
            "entry_price": "4133.41",
            "quantity": "0.02",
            "leverage": "50",
            "liquidation_price": "4071.1",
            "pnl": "-0.0362",
            "order_type": "LONG",
            "status": "OPEN",
            "id": "01999e74-27a6-76d5-880b-4cab5eac78f1",
            "asset_uuid": "01903bc9-973a-7106-99e2-08287b632806",
            "symbol": "ETHUSDT"
        }
    ]
}

Parameters

Parameter

Description

id

Position ID (UUID)

created_at

Timestamp when the position was created

updated_at

Timestamp when the position was last updated

stoploss

Stop loss object containing

price

,

order_id

, and

order_type

(can be null if not set)

takeprofit

Take profit object containing

price

,

order_id

, and

order_type

(can be null if not set)

entry_price

Price at which the position was opened

quantity

Position quantity

leverage

Leverage used for the position

liquidation_price

Liquidation price for the position

pnl

Unrealised profit and loss for the position

order_type

Position type:

LONG

or

SHORT

status

Position status (e.g.,

OPEN

)

asset_uuid

UUID of the asset

symbol

Trading symbol (e.g., "ETHUSDT")

Examples

No open positions

JSON

{
    "success": true,
    "data": null
}

Updated

2 days ago

Ask AI
