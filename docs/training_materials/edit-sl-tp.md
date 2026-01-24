# Edit SL/TP
Source: https://docs.trade.mudrex.com/docs/edit-sl-tp
Date Scraped: 2026-01-24

---

Request

API

curl -X PATCH "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/riskorder" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "order_price": 107526,
    "stoploss_price": 106900,
    "takeprofit_price": 110000,
    "stoploss_order_id": "<order_id>",
    "takeprofit_order_id": "<order_id>",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true
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

order_price

number

No

Order price

stoploss_price

number

Conditional

Required if

is_stoploss

is true. New stop loss price

takeprofit_price

number

Conditional

Required if

is_takeprofit

is true. New take profit price

stoploss_order_id

string

No

ID of the existing stop loss order to modify

takeprofit_order_id

string

No

ID of the existing take profit order to modify

trigger_type

string

No

Trigger type:

MARKET

or

LIMIT

is_stoploss

boolean

No

Whether to update the stop loss order (default: false)

is_takeprofit

boolean

No

Whether to update the take profit order (default: false)

Response

JSON

{
    "success": true,
    "data": {
        "position_id": "01999e74-27a6-76d5-880b-4cab5eac78f1",
        "status": "CREATED",
        "message": "Risk order updated successfully"
    }
}

Parameters

Parameter

Description

position_id

ID of the position for which the risk order was updated

status

Status of the risk order (e.g.,

CREATED

)

message

Status message

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

This error occurs when attempting to amend risk orders on a position that is not currently open.

Invalid request

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Invalid request"
        }
    ]
}

Status:

400 Bad Request

This error occurs when the request parameters are invalid or missing required fields.

Updated

2 days ago

Ask AI
