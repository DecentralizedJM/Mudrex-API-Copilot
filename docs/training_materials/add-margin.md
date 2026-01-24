# Add/Reduce Margin
Source: https://docs.trade.mudrex.com/docs/add-margin
Date Scraped: 2026-01-24

---

Request

API

curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/add-margin" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "margin": 10.2
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

margin

float

Yes

Margin amount to add (positive value) or reduce (negative value)

Response

JSON

{
    "success": true,
    "data": {
        "message": "OK",
        "initial_margin": "3.01011155",
        "liquidation_price": "2.5847"
    }
}

Parameters

Parameter

Description

message

Status message

initial_margin

Updated initial margin of the position

liquidation_price

Updated liquidation price of the position

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

Insufficient funds

JSON

{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Insufficient funds"
        }
    ]
}

Status:

400 Bad Request

This error occurs when attempting to add margin but there are insufficient funds available.

Updated

2 days ago

Ask AI
