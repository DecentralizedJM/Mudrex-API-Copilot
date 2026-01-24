# Create new order
Source: https://docs.trade.mudrex.com/docs/post-market-order
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/{asset_id}/order" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "leverage": 50,
    "quantity": 0.01,
    "order_price": 12445627,
    "order_type": "LONG",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true,
    "stoploss_price": 3800,
    "takeprofit_price": 5000,
    "reduce_only": false
  }'

Parameters

Parameter

Type

Required

Description

asset_id

string

Yes

The unique identifier of the asset (path parameter) or trading symbol (e.g., "BTCUSDT") if

is_symbol

query parameter is present

is_symbol

string

No

Query parameter. If present (even with value false/0), the

asset_id

path parameter is treated as a trading symbol instead of asset ID. If not passed, backward compatibility is maintained and asset ID is used

leverage

number

Yes

Leverage value (must be within permissible range for the asset)

quantity

number

Yes

Order quantity (must be a multiple of the quantity step for the asset)

order_price

number

Yes

Order price (must be between min & max price for the asset based on

LONG

/

SHORT

orders)

order_type

string

Yes

Order type:

LONG

or

SHORT

. If

reduce_only

is true, must be opposite of existing position

trigger_type

string

Yes

Trigger type:

MARKET

or

LIMIT

is_takeprofit

boolean

No

Whether to set a take profit order (default: false)

is_stoploss

boolean

No

Whether to set a stop loss order (default: false)

stoploss_price

number

Conditional

Required if

is_stoploss

is true. Stop loss price

takeprofit_price

number

Conditional

Required if

is_takeprofit

is true. Take profit price

reduce_only

boolean

No

If true, order can only decrease or close an existing position (default: false)

Response

Status:

202 Accepted

JSON

{
    "success": true,
    "data": {
        "leverage": "80.9",
        "amount": "222.8",
        "quantity": "0.05",
        "price": "4456",
        "order_id": "0199c39f-e866-7d6b-947e-ed2f09c90b8e",
        "status": "CREATED",
        "message": "OK"
    }
}

Parameters

Parameter

Description

order_id

UUID of the created order. This ID is used for CRUD operations on the order/position (setting SL/TP, square off, cancel, delete)

leverage

Leverage used for the order

amount

Amount used for the order

quantity

Order quantity

price

Order price

status

Order status (e.g.,

CREATED

)

message

Status message

Common errors

Params error

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Params error"
        }
    ]
}

Status:

400 Bad Request

Invalid trigger type

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "invalid trigger type"
        }
    ]
}

Status:

400 Bad Request

Invalid order type

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "invalid order type"
        }
    ]
}

Status:

400 Bad Request

Order price out of permissible range

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "order price out of permissible range"
        }
    ]
}

Status:

400 Bad Request

Quantity not a multiple of the quantity step

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "quantity not a multiple of the quantity step"
        }
    ]
}

Status:

400 Bad Request

Leverage out of permissible range

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "leverage out of permissible range"
        }
    ]
}

Status:

400 Bad Request

Symbol-First Trading

You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the

is_symbol

query parameter:

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT/order?is_symbol" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "leverage": 50,
    "quantity": 0.01,
    "order_price": 12445627,
    "order_type": "LONG",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true,
    "stoploss_price": 3800,
    "takeprofit_price": 5000,
    "reduce_only": false
  }'

Note

: The

is_symbol

query parameter need not have a value—its mere presence is enough. If the query parameter is passed (even with values like

false

,

f

,

False

,

0

), the system will treat the path parameter as a symbol. For backward compatibility, if the query parameter is not passed, the existing Asset ID support is used.

Notes

Order Price

: Must be between min & max price for the asset based on

LONG

/

SHORT

orders

Order Type

: Can be

LONG

or

SHORT

. If there is no existing position in an asset, you can open a new position or average/reduce position sizing

Reduce-Only Orders

: If

reduce_only

is

true

and there is an existing open position in a particular asset, the order type must be opposite to the existing position (e.g., if open position is

LONG

, request body must have order type

SHORT

and vice versa). A reduce-only order ensures it can only decrease or close an existing position

Trigger Type

: Can be

MARKET

or

LIMIT

Stop Loss/Take Profit

: If

is_takeprofit

is

true

or

is_stoploss

is

true

, you must define the corresponding price. If both are

false

, stop loss and take profit prices are not required

Updated

2 days ago

Ask AI
