# Generic Community Bot - Clarification

## ✅ What This Bot Is:

- **Generic Community Helper**: Provides general API documentation and help
- **Group-Only**: Works only in Telegram groups, rejects DMs
- **No Personal Data**: Does NOT access user accounts (positions, orders, balance)
- **No Authentication**: Doesn't need API keys - it's a public helper

## ❌ What This Bot Is NOT:

- ❌ Personal account assistant
- ❌ Does NOT show user's positions
- ❌ Does NOT show user's orders
- ❌ Does NOT show user's balance
- ❌ Does NOT require authentication

## 🎯 What It Does:

1. **API Documentation**: Answers questions about API endpoints
2. **Code Examples**: Shows how to use the API
3. **Error Debugging**: Helps troubleshoot API errors
4. **General Help**: Explains authentication, rate limits, etc.
5. **Public Info**: Can list futures contracts (public data)

## 📝 For Personal Account Data:

Users should use:
- Claude Desktop with MCP (personal setup)
- Mudrex web interface
- Their own authenticated API clients

## 🔧 MCP Integration:

MCP is used ONLY for:
- `list_futures` - Public list of available contracts
- `get_future` - Public contract details

MCP is BLOCKED for:
- All personal account tools (get_positions, get_orders, etc.)
- All trading tools (place_order, close_position, etc.)

