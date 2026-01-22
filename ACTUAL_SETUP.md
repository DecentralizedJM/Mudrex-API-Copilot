# Actual Setup - Using Your API Key/Secret

## ✅ Reality Check

Mudrex doesn't have "read-only" keys. You just have:
- **API Key** (public identifier)
- **API Secret** (private key)

That's it. No permission settings.

## 🔧 How It Works

1. **You provide your API secret** to the bot
2. **Bot code blocks personal queries** - even though it has your key, it won't fetch:
   - User balances
   - User orders  
   - User positions
3. **Bot only uses public data tools**:
   - Market prices
   - Futures contract listings
   - System status

## 📋 Setup (Simple)

1. **Get your API Secret**:
   - Mudrex → Settings → API Key Management
   - Copy your **API Secret**

2. **Add to `.env`**:
   ```env
   MUDREX_API_SECRET=your_api_secret_here
   ```

3. **Done!** Bot uses your key but code blocks personal queries.

## 🔒 Security

**Why it's safe:**
- Bot code explicitly blocks personal account tools
- Users asking "my balance" get message: "I can't access personal data"
- Bot only calls public data endpoints
- Your key is used but personal queries are blocked in code

**What happens:**
```
User: "What's my balance?"
Bot: [Code checks] → "This is a personal account query"
     → Blocks the call
     → Responds: "I'm a community bot. I can only access 
        public market data. For your personal account, use 
        Claude Desktop with MCP or the Mudrex dashboard."
```

## ✅ Summary

- Use your regular API secret
- Bot code blocks personal queries
- Only public data is accessed
- Safe and works!
