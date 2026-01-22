# Smart Response Behavior

## ✅ Bot Now Identifies API Questions Automatically

The bot is now smarter - it responds to API-related questions even when not tagged!

### Response Logic:

```
┌─────────────────────────────────────────────────┐
│ User sends message in group                     │
└─────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Bot mentioned/tagged? │
        └───────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
       YES                     NO
        │                       │
        │              ┌──────────────────┐
        │              │ API-related?     │
        │              └──────────────────┘
        │                       │
        │              ┌────────┴────────┐
        │              │                │
        │             YES              NO
        │              │                │
        └──────────────┴────────────────┘
                │              │
            RESPOND      IGNORE
```

### Examples:

✅ **Responds (API question, not tagged):**
```
User: "How do I authenticate with the API?"
Bot: [Responds with help]
```

✅ **Responds (Tagged, even if off-topic):**
```
User: "@botname What's the weather?"
Bot: "I'm here to help with Mudrex API questions! Ask me about..."
```

✅ **Responds (Tagged + API question):**
```
User: "@botname How do I place an order?"
Bot: [Responds with detailed help]
```

❌ **Ignores (Not tagged, not API-related):**
```
User: "What's for lunch?"
Bot: [Silently ignores]
```

❌ **Ignores (Not tagged, casual chat):**
```
User: "Hey everyone!"
Bot: [Silently ignores]
```

### What Makes a Message "API-Related"?

The bot detects:
- Code snippets (```python, import, def, etc.)
- API keywords (authentication, endpoint, order, position, etc.)
- Question words (how, what, why) + API context
- Error messages or debugging requests
- Technical terms (MCP, WebSocket, REST, etc.)

### Benefits:

1. **Better UX** - Users don't need to remember to tag
2. **Less noise** - Still ignores off-topic chat
3. **Smart detection** - Only responds to relevant questions
4. **Always responsive** - Tagged messages always get response

