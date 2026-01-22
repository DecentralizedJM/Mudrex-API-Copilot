# Quick Setup Guide - Service Account

## 🚀 Step-by-Step Setup

### Step 1: Get Your API Secret

1. **Log in to Mudrex**
   - Go to https://trade.mudrex.com
   - Log in with **your personal account**

2. **Navigate to API Settings**
   - Go to Settings → API Key Management
   - Or direct link: https://trade.mudrex.com/settings/api-keys

3. **Get Your API Secret**
   - If you already have an API key, copy the **API Secret**
   - If you don't have one, create a new API key
   - Copy the **API Secret** (shown only once!)

**Note**: Mudrex doesn't have "read-only" keys - you just have API key and secret. The bot code is configured to block personal account queries for security. The bot will use your key to fetch public data only.

---

### Step 2: Configure the Bot

1. **Open `.env` file** in the project root:
   ```bash
   cd /tmp/mudrex-bot-revamp
   nano .env
   ```

2. **Add your API secret**:
   ```env
   # Telegram Bot
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   
   # Gemini AI
   GEMINI_API_KEY=AIzaSyBvdNVeWY5eOJD8sr-9XKQZbeJAacuOVlc
   
   # Mudrex API Secret (Your Personal Key)
   MUDREX_API_SECRET=your_api_secret_here
   ```

3. **Save the file**

---

### Step 3: Test the Setup

Run the bot:
```bash
python3 main.py
```

You should see:
```
MCP connected with service account - X public tools available
```

---

### Step 4: Verify It Works

In your Telegram group, try:
```
@botname What futures contracts are available?
```

The bot should respond with a list of contracts (using public data).

---

## ✅ What Works Now

- ✅ Market prices and tickers
- ✅ Futures contract listings
- ✅ System status
- ✅ Public market data

## ❌ What Doesn't Work

- ❌ User balances (would show bot's balance, not user's)
- ❌ User orders (would show bot's orders, not user's)
- ❌ User positions (would show bot's positions, not user's)

---

## 🔒 Security Checklist

- [ ] API key is READ-ONLY (Trade disabled)
- [ ] API key is READ-ONLY (Withdraw disabled)
- [ ] `.env` file is in `.gitignore` (not committed to git)
- [ ] Service account key is stored securely

---

## 🆘 Troubleshooting

**Problem**: "MCP not connected"
- Check if `MUDREX_API_SECRET` is set in `.env`
- Verify the API secret is correct
- Make sure you copied the full secret

**Problem**: "Authentication failed"
- Verify the API secret is correct (no extra spaces)
- Check if the key is still active in Mudrex
- Try creating a new API key if needed

**Problem**: Bot can't fetch data
- Check if the service account key is active
- Verify MCP server is accessible
- Check bot logs for error messages

