# Reverse position
Source: https://docs.trade.mudrex.com/docs/reverse
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/reverse" \
  -H "Content-Type: application/json" \
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

Response

Status:

202 Accepted

JSON

{
    "success": true,
    "data": {
        "position_id": "01999e74-27a6-76d5-880b-4cab5eac78f1",
        "status": "CREATED",
        "message": "Position reversed successfully"
    }
}

Parameters

Parameter

Description

position_id

ID of the reversed position

status

Status of the reversal operation (e.g.,

CREATED

)

message

Status message

Common errors

Position not in sync with exchange

JSON

{
    "success": false,
    "errors": [
        {
            "code": null,
            "text": "position not in sync with exchange"
        }
    ]
}

Status:

400 Bad Request

This error occurs when the position state on the exchange differs from the local state, preventing the reversal operation.

Updated

2 days ago

Ask AI
