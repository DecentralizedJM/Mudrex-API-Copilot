# Leverage by asset id/symbol
Source: https://docs.trade.mudrex.com/docs/get-leverage-by-asset-id
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/{asset_id}/leverage" \
  -H "X-Authentication: your-secret-key"

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

Symbol-First Trading

You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the

is_symbol

query parameter:

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT/leverage?is_symbol" \
  -H "X-Authentication: your-secret-key"

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

Current leverage level set for the asset

MarginType

Margin type for the asset. Currently only

ISOLATED

is supported

Updated

2 days ago

Ask AI
