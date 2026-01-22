# Using Personal Read-Only Key

## ✅ Yes, You Can Use Your Personal Key!

Since Mudrex doesn't have "service accounts", you can use **your personal read-only API key**.

## 🔒 Important Security Notes

### What Happens:
- Bot uses **YOUR** account's API key
- Bot can access public data (prices, contracts, market info)
- Bot is **programmed to block** personal account queries
- If someone asks "my balance", bot will say it can't access personal data

### Safety Measures:
1. **Read-Only Key**: Your key must have Trade and Withdraw DISABLED
2. **Code Protection**: Bot code blocks personal account tools
3. **Smart Responses**: Bot tells users it can't access their personal data

## 📋 Setup

1. **Get Your Read-Only Key**:
   - Go to Mudrex → Settings → API Key Management
   - Use existing read-only key OR create new one
   - Make sure Trade and Withdraw are OFF

2. **Add to .env**:
   ```env
   MUDREX_API_SECRET=your_personal_read_only_key
   ```

3. **That's it!** Bot will use your key for public data only.

## ⚠️ What Users Will See

**User asks**: "What's my balance?"
**Bot responds**: "I'm a community bot using a service account. I can only access public market data. For your personal account information, please use Claude Desktop with MCP (using your own API key) or check the Mudrex web dashboard."

The bot **won't** fetch your balance even though it has your key - it's blocked in code!

## ✅ Safe Because:

1. Key is read-only (can't trade or withdraw)
2. Bot code blocks personal account tools
3. Bot only uses public data tools
4. Users get clear message about personal data

## 🎯 Summary

- ✅ Use your personal read-only key
- ✅ Bot fetches public data only
- ✅ Personal queries are blocked
- ✅ Safe and secure!
