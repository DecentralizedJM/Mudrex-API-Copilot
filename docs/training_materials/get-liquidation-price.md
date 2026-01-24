# Get Liquidation Price
Source: https://docs.trade.mudrex.com/docs/get-liquidation-price
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price?ext_margin=2.1" \
  -H "X-Authentication: your-secret-key"

Parameters

Parameter

Type

Required

Description

position_id

string

Yes

The unique identifier of the position (path parameter)

ext_margin

float

No

Additional margin amount (positive for adding margin, negative for reducing margin). If not passed or zero, returns current liquidation price

Response

JSON

{
    "success": true,
    "data": "2.5847"
}

Parameters

Parameter

Description

data

Estimated liquidation price (string)

Examples

Get current liquidation price (no query parameter)

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price" \
  -H "X-Authentication: your-secret-key"

Get estimated liquidation price after adding margin

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price?ext_margin=10.5" \
  -H "X-Authentication: your-secret-key"

Get estimated liquidation price after reducing margin

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price?ext_margin=-5.2" \
  -H "X-Authentication: your-secret-key"

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

Updated

2 days ago

Ask AI
