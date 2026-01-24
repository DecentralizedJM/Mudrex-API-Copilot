# Cancel order by id
Source: https://docs.trade.mudrex.com/docs/delete-order
Date Scraped: 2026-01-24

---

Request

API

curl -X DELETE "https://trade.mudrex.com/fapi/v1/futures/orders/{order_id}" \
  -H "X-Authentication: your-secret-key"

Parameters

Parameter

Type

Required

Description

order_id

string

Yes

The unique identifier of the order (path parameter)

Response

JSON

{
    "success": true,
    "data": {
        "message": "Order cancelled successfully",
        "order_id": "0199c7e7-628f-75e0-8212-d02f6e3b1c7a",
        "status": "CANCELLED"
    }
}

Parameters

Parameter

Description

message

Status message

order_id

ID of the cancelled order

status

Status of the order (e.g.,

CANCELLED

)

Common errors

Order already deleted

Status:

400 Bad Request

Occurs when attempting to delete an order that has already been cancelled or deleted.

Invalid order ID

Status:

500 Internal Server Error

Occurs when the provided order ID is invalid or malformed.

Updated

2 days ago

Ask AI
