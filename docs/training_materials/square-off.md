# Square off
Source: https://docs.trade.mudrex.com/docs/square-off
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/close" \
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

JSON

{
    "success": true,
    "data": {
        "position_id": "0199be9e-21f3-74c3-9439-dc826109223e",
        "status": "CREATED",
        "message": "OK"
    }
}

Parameters

Parameter

Description

position_id

ID of the position being closed

status

Status of the close operation (e.g.,

CREATED

)

message

Status message

Common errors

Position is not open

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "position is not open"
        }
    ]
}

Status:

400 Bad Request

Occurs when attempting to close a position that is not currently open.

Updated

2 days ago

Ask AI
