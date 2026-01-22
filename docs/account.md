# Mudrex Account API

## Overview
Account endpoints provide information about your trading account, balances, and positions.

## Get Account Balance

**Endpoint:** `GET /account/balance`

**Response:**
```json
{
    "totalWalletBalance": "10000.00",
    "totalUnrealizedProfit": "250.50",
    "totalMarginBalance": "10250.50",
    "availableBalance": "8500.00",
    "maxWithdrawAmount": "8500.00"
}
```

## Get Positions

**Endpoint:** `GET /positions`

**Parameters:**
- `symbol` (optional): Filter by trading pair

**Response:**
```json
[
    {
        "symbol": "BTCUSDT",
        "positionSide": "BOTH",
        "positionAmt": "0.5",
        "entryPrice": "42000.00",
        "markPrice": "43000.00",
        "unrealizedProfit": "500.00",
        "liquidationPrice": "35000.00",
        "leverage": "10",
        "marginType": "cross"
    }
]
```

## Set Leverage

**Endpoint:** `POST /leverage`

**Parameters:**
- `symbol` (required): Trading pair
- `leverage` (required): Leverage value (1-125)

**Example:**
```python
response = requests.post(
    'https://api.mudrex.com/api/v1/leverage',
    headers=headers,
    json={'symbol': 'BTCUSDT', 'leverage': 10}
)
```

## Change Margin Type

**Endpoint:** `POST /marginType`

**Parameters:**
- `symbol` (required): Trading pair
- `marginType` (required): ISOLATED or CROSSED
