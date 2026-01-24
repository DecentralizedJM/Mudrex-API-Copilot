# Mudrex API Authentication

## Overview
The Mudrex API uses API key authentication. You need to include your API secret in the request headers.

## Authentication Header
All authenticated endpoints require the `X-Authentication` header:

```
X-Authentication: your_api_secret_here
```

## Getting API Keys
1. Log in to your Mudrex account
2. Navigate to API Management settings
3. Create a new API key
4. Store your API secret securely - it's only shown once

## Key Types
- **Read-Only Keys**: Can view account data, positions, and market data
- **Trading Keys**: Can place and manage orders (use with caution)

## Security Best Practices
- Never share your API secret
- Use read-only keys when possible
- Whitelist IP addresses if available
- Rotate keys periodically
- Don't commit keys to version control

## Example Request (Python)
Mudrex uses only X-Authentication (no HMAC, no signature, no X-MUDREX-* headers).
```python
import requests

response = requests.get(
    "https://trade.mudrex.com/fapi/v1/wallet/funds",
    headers={"X-Authentication": "your_api_secret"}
)
print(response.json())
```

## Example Request (JavaScript)
```javascript
const response = await fetch("https://trade.mudrex.com/fapi/v1/wallet/funds", {
    headers: { "X-Authentication": "your_api_secret" }
});
const data = await response.json();
```
