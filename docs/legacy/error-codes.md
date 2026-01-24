# Mudrex API Error Codes

## HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

## Error Response Format
```json
{
    "code": -1121,
    "msg": "Invalid symbol."
}
```

## Common Error Codes

### General Errors
- `-1000` - Unknown error
- `-1001` - Disconnected
- `-1002` - Unauthorized
- `-1003` - Too many requests
- `-1006` - Unexpected response
- `-1007` - Timeout
- `-1014` - Unknown order composition
- `-1015` - Too many orders
- `-1016` - Service shutting down
- `-1020` - Unsupported operation
- `-1021` - Invalid timestamp
- `-1022` - Invalid signature

### Order Errors
- `-1100` - Illegal characters in parameter
- `-1101` - Too many parameters
- `-1102` - Mandatory parameter missing
- `-1103` - Unknown parameter
- `-1104` - Unread parameters
- `-1105` - Parameter empty
- `-1106` - Parameter not required
- `-1111` - Precision over maximum
- `-1112` - No orders on symbol
- `-1114` - TimeInForce not required
- `-1115` - Invalid timeInForce
- `-1116` - Invalid orderType
- `-1117` - Invalid side
- `-1118` - New client order ID empty
- `-1119` - Original client order ID empty
- `-1120` - Invalid interval
- `-1121` - Invalid symbol
- `-1125` - Invalid listenKey
- `-1127` - Lookup interval too big
- `-1128` - Combination of optional parameters invalid

### Trading Errors
- `-2010` - New order rejected
- `-2011` - Cancel rejected
- `-2013` - Order does not exist
- `-2014` - API key format invalid
- `-2015` - Invalid API key, IP, or permissions
- `-2019` - Margin is insufficient
- `-2020` - Unable to fill
- `-2021` - Order would immediately trigger
- `-2022` - ReduceOnly order rejected
- `-2024` - Position not sufficient
- `-2025` - Reach max open order limit

## Rate Limits
- API requests: 1200 requests per minute
- Order placement: 10 orders per second
- Order cancellation: 10 cancels per second

When rate limited, wait for the retry-after period before making new requests.
