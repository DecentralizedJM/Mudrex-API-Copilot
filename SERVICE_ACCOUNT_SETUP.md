# Service Account Setup Guide

## 🎯 Service Account Model

This bot uses a **Service Account** (read-only API key) to access PUBLIC data only.

Think of it like a **Public Kiosk** at the Mudrex office:
- The bot has a "service ID card" (read-only API key)
- It can access the building directory and lobby status (public data)
- It does NOT have keys to individual offices (user accounts)

## 📋 Setup Steps

### Step 1: Get Your Personal Read-Only API Key

1. Log in to Mudrex with **your personal account**
2. Go to **Settings → API Key Management**
3. Either:
   - **Option A**: Use an existing read-only key (if you have one)
   - **Option B**: Create a new API key
     - Name it: `Telegram_Bot_ReadOnly` (or any name)
     - **CRITICAL**: Set permissions to **READ-ONLY**
       - ✅ Enable: Read
       - ❌ Disable: Trade (MUST be off!)
       - ❌ Disable: Withdraw (MUST be off!)
4. Copy the API Secret (shown only once!)

**Note**: Since Mudrex doesn't have "service accounts", you'll use your personal read-only key. The bot is configured to only access public data and will block personal account queries.

### Step 2: Configure Bot

Add to your `.env` file:

```env
MUDREX_API_SECRET=your_service_account_read_only_key_here
```

### Step 3: What Works vs What Doesn't

#### ✅ Works (Public Data):
- Market prices and tickers
- System status
- Futures contract listings
- Public volume data
- General market information

#### ❌ Doesn't Work (Personal Data):
- User balances (would return bot's balance, not user's)
- User orders (would return bot's orders, not user's)
- User positions (would return bot's positions, not user's)

## 🔒 Security

- Service account key is **READ-ONLY** - cannot trade or withdraw
- Bot cannot access individual user accounts
- Each user needs their own API key for personal data

## 💡 Example Queries

**✅ Bot Can Answer:**
```
User: "What's the BTC price?"
Bot: [Fetches public ticker data using service account]
     "BTC/USDT: $43,250.50"
```

**❌ Bot Cannot Answer:**
```
User: "What's my balance?"
Bot: "I'm a community bot using a service account. I can only 
     access public market data. For your personal account 
     information, please use Claude Desktop with MCP (using 
     your own API key) or check the Mudrex web dashboard."
```

## 🎯 Architecture

```
┌─────────────────────────────────────────┐
│  Telegram Group (Community)             │
│  User asks: "What's BTC price?"         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  MudrexBot (Service Account)            │
│  Uses: MUDREX_API_SECRET (read-only)    │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Mudrex MCP Server                      │
│  X-Authentication: [Service Key]        │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Mudrex API                             │
│  Returns: Public data only              │
└─────────────────────────────────────────┘
```

## 📝 Summary

- **Service Account**: One read-only key for the bot
- **Public Data**: Prices, market info, system status
- **No Personal Data**: Cannot access user accounts
- **Secure**: Read-only key cannot trade or withdraw
