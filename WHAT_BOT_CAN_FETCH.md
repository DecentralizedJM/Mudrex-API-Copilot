# What the Bot Can Fetch with MCP Integration

## ✅ What the Bot CAN Fetch (Public Data Only)

The bot can only fetch **2 public data tools**:

### 1. `list_futures`
**What it does**: Lists all available futures contracts on Mudrex

**Example queries**:
- "What futures contracts are available?"
- "List all futures pairs"
- "Show me all tradable contracts"

**Returns**: List of all 600+ futures contracts with details like:
- Symbol (BTC/USDT, ETH/USDT, etc.)
- Contract type
- Trading status
- Contract specifications

---

### 2. `get_future`
**What it does**: Get detailed information about a specific futures contract

**Example queries**:
- "What are the details for BTC/USDT contract?"
- "Show me ETH/USDT contract specs"
- "Get information about SOL/USDT futures"

**Parameters**: 
- `symbol` (required): Trading pair like "BTC/USDT"

**Returns**: Contract details including:
- Symbol and name
- Contract specifications
- Trading rules
- Minimum/maximum quantities
- Price precision
- Leverage limits

---

## ❌ What the Bot CANNOT Fetch (Blocked)

### Personal Account Data (Blocked):
- ❌ `get_positions` - Your open positions
- ❌ `get_orders` - Your open orders
- ❌ `get_order` - Specific order details
- ❌ `get_order_history` - Your order history
- ❌ `get_position_history` - Your position history
- ❌ `get_available_funds` - Your balance
- ❌ `get_fee_history` - Your fee history
- ❌ `get_leverage` - Your leverage settings
- ❌ `get_liquidation_price` - Your liquidation prices

**Why blocked**: These return YOUR account data (the bot owner's), not the user's. The bot code blocks these to prevent confusion.

### Trading Actions (Blocked):
- ❌ `place_order` - Place orders
- ❌ `cancel_order` - Cancel orders
- ❌ `amend_order` - Modify orders
- ❌ `close_position` - Close positions
- ❌ `reverse_position` - Reverse positions
- ❌ `set_leverage` - Change leverage
- ❌ `add_margin` - Add margin
- ❌ `place_risk_order` - Set stop-loss/take-profit
- ❌ `amend_risk_order` - Modify SL/TP

**Why blocked**: These modify accounts and require confirmation. Bot is read-only for safety.

---

## 📊 Summary

| Category | Available | Blocked |
|----------|-----------|---------|
| **Public Data** | 2 tools | 0 |
| **Personal Account** | 0 | 9 tools |
| **Trading Actions** | 0 | 9 tools |
| **Total** | **2 tools** | **18 tools** |

---

## 💡 Real-World Examples

### ✅ Works:
```
User: "What futures can I trade?"
Bot: [Calls list_futures]
     "Available futures contracts:
     • BTC/USDT - Perpetual
     • ETH/USDT - Perpetual
     • SOL/USDT - Perpetual
     ... (all 600+ contracts)"
```

```
User: "What are the specs for BTC/USDT?"
Bot: [Calls get_future with symbol="BTC/USDT"]
     "BTC/USDT Futures Contract:
     • Type: Perpetual
     • Min Quantity: 0.001 BTC
     • Price Precision: 2 decimals
     • Leverage: Up to 125x
     ..."
```

### ❌ Blocked:
```
User: "What are my positions?"
Bot: "I'm a community bot using a service account. I can only 
     access public market data. For your personal account 
     information, please use Claude Desktop with MCP (using 
     your own API key) or check the Mudrex web dashboard."
```

```
User: "Place a buy order for BTC"
Bot: "⚠️ place_order modifies your account and requires confirmation.
     For safety, this bot only executes read-only operations. 
     Use Claude Desktop or the Mudrex web interface for trading actions."
```

---

## 🎯 Why So Limited?

The bot is designed as a **community helper** for:
- General API documentation
- Code examples
- Error debugging
- Public market information

It's **NOT** designed for:
- Personal account management
- Trading execution
- Individual user data

This keeps it safe, simple, and focused on helping the community with general questions!

---

## 🔧 Technical Details

**MCP Tools Available**: 20 total
- Safe (Read-Only): 11 tools
- Confirmation Required: 9 tools

**Bot Uses**: 2 tools (public data only)
**Bot Blocks**: 18 tools (personal + trading)

**Blocking Method**: Code-level checks in `src/mcp/client.py` that prevent personal account tools from being called.
