# Group-Only Bot Changes

## ✅ Updated for Private Group Usage

### Key Changes:

1. **GROUP-ONLY Mode**
   - Bot ONLY works in Telegram groups (GROUP, SUPERGROUP)
   - Rejects all direct messages (DMs) with helpful message
   - All handlers use `filters.ChatType.GROUPS`

2. **Mention/Tag Required**
   - Bot ONLY responds when:
     - User @mentions the bot
     - User replies to bot's previous message
   - Silently ignores messages where bot is not mentioned

3. **Community Focus**
   - Updated personality for group discussions
   - Focus: API questions, coding help, error debugging, feedback
   - Help messages updated to reflect group-only usage

4. **Rate Limiting**
   - Changed from per-user to per-group
   - Prevents spam from single group

5. **Chat History**
   - History stored per-group (`history_{chat_id}`)
   - Each group has separate conversation context

### Files Modified:

- `src/bot/telegram_bot.py` - Group-only handlers, DM rejection
- `src/rag/gemini_client.py` - Updated system instruction for group context
- `README.md` - Updated to reflect group-only nature

### Usage in Group:

```
User: @botname How do I authenticate?
Bot: [Responds with help]

User: How do I authenticate?  (not tagged)
Bot: [Silently ignores]

User: [Sends DM]
Bot: "I'm a community bot for the Mudrex API traders group..."
```

### Configuration:

No changes needed - bot automatically detects group vs DM and responds accordingly.
