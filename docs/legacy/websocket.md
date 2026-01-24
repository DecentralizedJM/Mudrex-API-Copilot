# Mudrex WebSocket API

## Overview
WebSocket streams provide real-time market data and account updates.

## Base URL
```
wss://stream.mudrex.com/ws
```

## Connection
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(data)

def on_open(ws):
    # Subscribe to streams
    ws.send(json.dumps({
        "method": "SUBSCRIBE",
        "params": ["btcusdt@ticker"],
        "id": 1
    }))

ws = websocket.WebSocketApp(
    "wss://stream.mudrex.com/ws",
    on_message=on_message,
    on_open=on_open
)
ws.run_forever()
```

## Available Streams

### Ticker Stream
Real-time ticker updates.
```
<symbol>@ticker
Example: btcusdt@ticker
```

### Kline Stream
Real-time candlestick updates.
```
<symbol>@kline_<interval>
Example: btcusdt@kline_1m
```

### Depth Stream
Orderbook updates.
```
<symbol>@depth<levels>
Example: btcusdt@depth10
```

### Trade Stream
Real-time trades.
```
<symbol>@trade
Example: btcusdt@trade
```

### Mark Price Stream
Mark price updates.
```
<symbol>@markPrice
Example: btcusdt@markPrice
```

## User Data Stream
For account and order updates, you need to create a listen key.

**Create Listen Key:**
```python
response = requests.post(
    'https://api.mudrex.com/api/v1/listenKey',
    headers={'X-Authentication': 'your_api_secret'}
)
listen_key = response.json()['listenKey']
```

**Connect to User Stream:**
```
wss://stream.mudrex.com/ws/<listenKey>
```

**Events:**
- `ACCOUNT_UPDATE` - Balance and position changes
- `ORDER_TRADE_UPDATE` - Order status changes
- `MARGIN_CALL` - Margin warnings
