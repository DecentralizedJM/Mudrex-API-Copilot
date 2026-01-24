# Set leverage by asset id/symbol
Source: https://docs.trade.mudrex.com/docs/set
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/{asset_id}/leverage" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "margin_type": "ISOLATED",
    "leverage": 50
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

margin_type

string

No

Margin type. Currently only

ISOLATED

is supported (defaults to ISOLATED)

leverage

number

Yes

Leverage value to set for the asset (must be within permissible range)

Symbol-First Trading

You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the

is_symbol

query parameter:

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT/leverage?is_symbol" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "margin_type": "ISOLATED",
    "leverage": 50
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

Response

JSON

{
    "success": true,
    "data": {
        "Leverage": "50",
        "MarginType": "ISOLATED"
    }
}

Parameters

Parameter

Description

Leverage

Leverage level set for the asset

MarginType

Margin type for the asset. Currently only

ISOLATED

is supported

Common errors

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

This error occurs when:

Leverage value is too high (e.g.,

5999836

)

Leverage value is invalid (e.g.,

0

or negative)

Invalid asset ID

Status:

400 Bad Request

Occurs when the provided asset ID is invalid or not found.

Notes

Currently, only

margin_type = ISOLATED

is supported, so

margin_type

is not a mandatory field in the request body

Leverage must be within the permissible range for the specific asset (check asset details for min/max leverage values)

Updated

2 days ago

Ask AI
