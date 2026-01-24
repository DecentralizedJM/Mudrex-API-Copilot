# Fees
Source: https://docs.trade.mudrex.com/docs/fees
Date Scraped: 2026-01-24

---

Request

API

curl -X GET "https://trade.mudrex.com/fapi/v1/futures/fee/history?limit=2" \
  -H "X-Authentication: your-secret-key"

Parameters

Parameter

Type

Required

Description

limit

number

No

Maximum number of records to return (default: 20)

offset

number

No

Number of records to skip (default: 0)

Response

JSON

{
    "success": true,
    "data": [
        {
            "symbol": "ETHUSDT",
            "fee_amount": "0.0206648",
            "fee_perc": "0.05",
            "fee_type": "TRANSACTION",
            "created_at": "2025-10-01T06:31:00Z",
            "transaction_amount": "41.3296"
        },
        {
            "symbol": "ETHUSDT",
            "fee_amount": "0.0206693",
            "fee_perc": "0.05",
            "fee_type": "TRANSACTION",
            "created_at": "2025-10-01T06:27:17Z",
            "transaction_amount": "41.3386"
        }
    ]
}

Parameters

Parameter

Description

symbol

Trading symbol (e.g., "ETHUSDT")

fee_amount

Fee amount charged

fee_perc

Fee percentage

fee_type

Type of fee:

TRANSACTION

or

FUNDING

created_at

Timestamp when the fee was charged

transaction_amount

Transaction amount on which the fee was calculated

Updated

2 days ago

Ask AI
