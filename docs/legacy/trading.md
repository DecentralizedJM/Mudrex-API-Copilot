# Mudrex Trading API

## Overview
The Mudrex Trading API allows you to place, modify, and cancel orders programmatically.

⚠️ **Important**: Trading endpoints require authenticated API keys with trading permissions.

## Base URL
```
https://api.mudrex.com/api/v1
```

## Order Types

### Market Order
Executes immediately at the best available price.

### Limit Order
Executes at specified price or better.

### Stop Market Order
Triggers a market order when stop price is reached.

### Stop Limit Order
Triggers a limit order when stop price is reached.

## Place Order

**Endpoint:** `POST /order`

**Parameters:**
- `symbol` (required): Trading pair (e.g., BTCUSDT)
- `side` (required): BUY or SELL
- `type` (required): MARKET, LIMIT, STOP_MARKET, STOP_LIMIT
- `quantity` (required): Order quantity
- `price` (conditional): Required for LIMIT orders
- `stopPrice` (conditional): Required for STOP orders
- `timeInForce` (optional): GTC, IOC, FOK (default: GTC)
- `reduceOnly` (optional): true/false
- `closePosition` (optional): true/false

**Example Request:**
```python
import requests

headers = {
    'X-Authentication': 'your_api_secret',
    'Content-Type': 'application/json'
}

data = {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'LIMIT',
    'quantity': '0.01',
    'price': '42000',
    'timeInForce': 'GTC'
}

response = requests.post(
    'https://api.mudrex.com/api/v1/order',
    headers=headers,
    json=data
)
```

**Response:**
```json
{
    "orderId": "123456789",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "price": "42000",
    "origQty": "0.01",
    "status": "NEW",
    "timeInForce": "GTC"
}
```

## Cancel Order

**Endpoint:** `DELETE /order`

**Parameters:**
- `symbol` (required): Trading pair
- `orderId` (required): Order ID to cancel

**Example:**
```python
response = requests.delete(
    'https://api.mudrex.com/api/v1/order',
    headers=headers,
    params={'symbol': 'BTCUSDT', 'orderId': '123456789'}
)
```

## Get Open Orders

**Endpoint:** `GET /openOrders`

**Parameters:**
- `symbol` (optional): Filter by trading pair

## Get Order History

**Endpoint:** `GET /allOrders`

**Parameters:**
- `symbol` (required): Trading pair
- `limit` (optional): Number of orders (default 500, max 1000)
