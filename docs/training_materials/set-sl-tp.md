# Set SL/TP
Source: https://docs.trade.mudrex.com/docs/set-sl-tp
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/riskorder" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "stoploss_price": "5289.5",
    "takeprofit_price": "50713.00",
    "order_source": "API",
    "is_stoploss": true,
    "is_takeprofit": true
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

stoploss_price

string

Conditional

Required if

is_stoploss

is true. Stop loss price (must be above liquidation price for LONG positions)

takeprofit_price

string

Conditional

Required if

is_takeprofit

is true. Take profit price

order_source

string

No

Source of the order (e.g., "API")

is_stoploss

boolean

No

Whether to set a stop loss order (default: false)

is_takeprofit

boolean

No

Whether to set a take profit order (default: false)

Response

JSON

{
    "success": true,
    "data": {
        "position_id": "0199c39f-e864-7dbc-8b83-6954c1df7832",
        "status": "CREATED",
        "message": "Risk order placed successfully"
    }
}

Parameters

Parameter

Description

position_id

ID of the position for which the risk order was set

status

Status of the risk order (e.g.,

CREATED

)

message

Status message

Examples

Get position details after setting SL/TP

JSON

{
    "success": true,
    "data": [
        {
            "created_at": "2025-10-08T11:41:01Z",
            "updated_at": "2025-10-08T12:13:10Z",
            "stoploss": {
                "price": "0",
                "order_id": "",
                "order_type": ""
            },
            "takeprofit": {
                "price": "30000",
                "order_id": "0199c3bd-53ba-7491-ae5c-15bb95c1977a",
                "order_type": "SHORT"
            },
            "entry_price": "5304.392",
            "quantity": "0.05",
            "leverage": "80.9",
            "liquidation_price": "5265.16",
            "initial_margin": "3.42243351",
            "maintenance_margin": "1.47012993",
            "pnl": "-0.0076",
            "closed_price": "0",
            "order_type": "LONG",
            "status": "OPEN",
            "id": "0199c39f-e864-7dbc-8b83-6954c1df7832",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        }
    ]
}

Common errors

Position not found

JSON

{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "Position not found"
        }
    ]
}

Status:

404 Not Found

This error occurs when the position ID is incorrect or the position does not exist.

Position not in OPEN state

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Position is not in OPEN state"
        }
    ]
}

Status:

400 Bad Request

This error occurs when attempting to set risk orders on a position that is not currently open.

Risk order creation failed (SL below liquidation)

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Risk order creation failed"
        }
    ]
}

Status:

400 Bad Request

This error occurs when the stop loss price is set below the liquidation price for a LONG position (or above for a SHORT position).

Updated

2 days ago

Ask AI
