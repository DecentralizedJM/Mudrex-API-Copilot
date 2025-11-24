# Mudrex API Intelligent Assistant 🤖

An intelligent Telegram bot that answers Mudrex API questions using RAG (Retrieval-Augmented Generation) with Google Gemini 2.5 Flash. The bot speaks like a confident Mudrex developer intern with deep API knowledge, providing helpful answers in a friendly, approachable manner.

**Bot:** [@Mudrex_API_bot](https://t.me/Mudrex_API_bot)  
**Author:** [DecentralizedJM](https://github.com/DecentralizedJM)  
**License:** MIT (with attribution required)  
**Copyright:** © 2025 DecentralizedJM

---

## Features

- 🤖 **Smart Query Detection**: Automatically identifies API-related questions and silently ignores casual chat
- 📚 **RAG-Powered Responses**: Uses vector search across Mudrex API documentation for accurate answers
- � **@Mention Support**: Responds to all @mentions and asks for clarification when needed
- 🎯 **Confident Personality**: Speaks like a skilled Mudrex intern who knows the API inside-out
- ⚡ **Fast & Accurate**: Powered by Gemini 2.5 Flash with 2048 token responses
- 🔐 **Secure**: Optional chat ID restrictions for controlled access
- 📖 **Auto-Documentation Fetch**: Automatically pulls latest docs from https://docs.trade.mudrex.com

## Architecture

```
┌─────────────┐
│  Telegram   │
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Telegram Bot   │
│   (Handler)     │  ✓ Silent filtering
│                 │  ✓ @mention detection
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  RAG Pipeline   │◄────►│  Vector Store   │
│                 │      │ (sklearn-based) │
│  • Query detect │      │  22 documents   │
│  • Context ret. │      │  embeddings     │
└──────┬──────────┘      └─────────────────┘
       │
       ▼
┌─────────────────┐
│  Gemini 2.5     │
│  Flash API      │  ✓ 2048 max tokens
│                 │  ✓ Confident persona
└─────────────────┘
```

## Tech Stack

- **Python 3.14** - Latest Python runtime
- **python-telegram-bot** - Async Telegram integration
- **Scikit-learn** - Vector similarity search with cosine distance
- **Google Gemini 2.5 Flash** - Fast, efficient LLM with extended context
- **BeautifulSoup4** - Documentation auto-fetching from web

## Setup

### 1. Prerequisites

- Python 3.10 or higher (tested on Python 3.14)
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- Google Gemini API Key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/DecentralizedJM/Mudrex-API-Intelligent-Assitant-.git
cd Mudrex-API-Intelligent-Assitant-

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=2048

# Optional: Restrict to specific chat IDs (comma-separated)
# ALLOWED_CHAT_IDS=123456789,-987654321
```

**⚠️ Security Note:** Never commit your `.env` file to version control. It's already in `.gitignore`.

### 4. Fetch & Ingest Documentation

The bot automatically fetches Mudrex API documentation:

```bash
# Auto-fetch from docs.trade.mudrex.com and ingest
python scripts/ingest_docs.py
```

This creates vector embeddings from 22 documentation chunks.

### 5. Run the Bot

```bash
python main.py
```

You should see:
```
==================================================
Starting Mudrex API Documentation Bot
==================================================
Initialized vector store with 22 documents
Initialized Gemini client with model: gemini-2.5-flash
Bot is now running. Press Ctrl+C to stop.
```

## Usage

### Telegram Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show usage tips and features
- `/stats` - Display bot statistics (documents loaded, model info)

### Bot Behavior

**✅ Responds to:**
- Direct API questions: "How do I create an order?"
- Error troubleshooting: "Getting 401 error"
- @Mentions: "@Mudrex_API_bot how to authenticate?"

**❌ Silently ignores:**
- Casual chat: "hello", "how are you", "I made profit today"
- Non-API discussions

**💬 Asks for clarification when:**
- @Mentioned but message is vague: "@Mudrex_API_bot hi"

### Example Interactions

```
User: How do I authenticate with the Mudrex API?
Bot: Hey! For authentication, you'll need to use API keys. Here's how...

User: What's the endpoint for placing orders?
Bot: The order placement endpoint is POST /v1/orders. Let me break down...

User: I got profit today! 🚀
Bot: [silently ignores - not API-related]

User: @Mudrex_API_bot what are webhooks?
Bot: Webhooks let you receive real-time updates from Mudrex...

User: @Mudrex_API_bot hi
Bot: Hey! I'm here to help with Mudrex API questions. What would you like to know?
```

## Configuration Options

Edit `.env` to customize behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | *Required* |
| `GEMINI_API_KEY` | Google Gemini API key | *Required* |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_TEMPERATURE` | Response creativity (0-1) | `0.3` |
| `GEMINI_MAX_TOKENS` | Maximum response length | `2048` |
| `EMBEDDING_MODEL` | Model for embeddings | `models/text-embedding-004` |
| `TOP_K_RESULTS` | Documents to retrieve | `5` |
| `SIMILARITY_THRESHOLD` | Minimum similarity score | `0.6` |
| `ALLOWED_CHAT_IDS` | Restrict to specific chats | None (all allowed) |
| `AUTO_DETECT_QUERIES` | Enable smart filtering | `true` |

## Project Structure

```
mudrex-api-bot/
├── src/
│   ├── bot/
│   │   ├── telegram_bot.py      # Telegram handlers, @mention detection
│   │   └── __init__.py
│   ├── rag/
│   │   ├── pipeline.py          # RAG orchestration
│   │   ├── vector_store.py      # sklearn-based vector search
│   │   ├── gemini_client.py     # Gemini API client with persona
│   │   └── __init__.py
│   ├── config/
│   │   ├── settings.py          # Configuration management
│   │   └── __init__.py
│   └── utils/
│       └── document_loader.py   # Auto-fetch from docs.trade.mudrex.com
├── scripts/
│   └── ingest_docs.py           # Documentation ingestion script
├── data/
│   └── chroma/
│       └── vectors.pkl          # Serialized vector embeddings
├── docs/
│   └── mudrex-api-documentation.md  # Auto-fetched documentation
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (not in repo)
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
└── README.md                    # This file
```

## Development

### Adding/Updating Documentation

The bot automatically fetches documentation from https://docs.trade.mudrex.com:

```bash
# Re-fetch and re-ingest latest documentation
python scripts/ingest_docs.py

# Restart bot to reload
python main.py
```

### Customizing Bot Personality

Edit `src/rag/gemini_client.py` to modify the system prompt:

```python
# Current persona: Confident Mudrex intern with IQ 200
# Modify the prompt in generate_response() method
```

### Changing LLM Provider

To use OpenAI/Claude instead of Gemini:

1. Update `src/rag/gemini_client.py` 
2. Replace Gemini API calls with your provider
3. Update environment variables in `.env`

### Testing

```bash
# Test documentation ingestion
python scripts/ingest_docs.py

# Test bot locally
python main.py
# Send test messages on Telegram
```

## Deployment

### Running in Production

```bash
# Use nohup to run in background
nohup python main.py > bot.log 2>&1 &

# Or use screen/tmux
screen -S mudrex-bot
python main.py
# Ctrl+A, D to detach
```

### Docker (Optional)

```dockerfile
# Dockerfile included in repo
docker build -t mudrex-api-bot .
docker run -d --env-file .env mudrex-api-bot
```

### Production Best Practices

- ✅ Set `ALLOWED_CHAT_IDS` to restrict access to authorized users
- ✅ Monitor logs: `tail -f bot.log`
- ✅ Set up log rotation for `bot.log`
- ✅ Regularly update documentation via re-ingestion
- ✅ Consider using Telegram webhooks for better scalability
- ✅ Keep API keys secure and rotate regularly

## Troubleshooting

### Bot doesn't respond to messages
- ✅ Check `TELEGRAM_BOT_TOKEN` is correct
- ✅ Verify no other bot instances are running: `ps aux | grep python.*main.py`
- ✅ Check chat ID isn't in restricted list (`ALLOWED_CHAT_IDS`)
- ✅ Look for errors in `bot.log`

### "Conflict: terminated by other getUpdates request"
- Multiple bot instances are running
- Kill all instances: `pkill -9 -f "python.*main.py"`
- Wait 5-10 seconds before restarting

### Bot silently ignores API questions
- Check if question contains API keywords (authentication, endpoint, error, etc.)
- Try @mentioning the bot: `@Mudrex_API_bot your question`
- Check `AUTO_DETECT_QUERIES` is set to `true` in `.env`

### Poor answer quality
- ✅ Increase `TOP_K_RESULTS` to retrieve more context (try 7-10)
- ✅ Lower `SIMILARITY_THRESHOLD` for broader matching (try 0.4-0.5)
- ✅ Re-fetch documentation: `python scripts/ingest_docs.py`
- ✅ Increase `GEMINI_MAX_TOKENS` for longer responses (max 8192)

### Import/dependency errors
- ✅ Ensure virtual environment is activated: `source venv/bin/activate`
- ✅ Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- ✅ Check Python version: `python --version` (need 3.10+)

### Vector store shows 0 documents
- Run ingestion script: `python scripts/ingest_docs.py`
- Check `data/chroma/vectors.pkl` exists
- Verify working directory is project root when running bot

## Features Roadmap

- [x] RAG-based question answering
- [x] Gemini 2.5 Flash integration
- [x] Silent non-API message filtering
- [x] @Mention detection and handling
- [x] Auto-documentation fetching
- [x] Confident developer persona
- [ ] Multi-language support
- [ ] Webhook mode for production
- [ ] Conversation history tracking
- [ ] Admin commands for bot management
- [ ] Analytics dashboard
- [ ] Docker deployment

## Contributing

Contributions are welcome! This project is open-source under MIT license with attribution requirement.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

**Attribution Required:** When forking or creating derivative works, please maintain attribution to [DecentralizedJM](https://github.com/DecentralizedJM) as per MIT license.

## License

MIT License - Copyright © 2025 [DecentralizedJM](https://github.com/DecentralizedJM)

This is original work. While open-source under MIT, proper attribution is required for any derivative works. See [LICENSE](LICENSE) file for full details.

## Support & Contact

- 🐛 **Issues:** [GitHub Issues](https://github.com/DecentralizedJM/Mudrex-API-Intelligent-Assitant-/issues)
- 📧 **Contact:** Open an issue for questions or support
- 📝 **Logs:** Check `bot.log` for debugging
- 🤖 **Live Bot:** [@Mudrex_API_bot](https://t.me/Mudrex_API_bot) on Telegram

---

**Built with ❤️ by [DecentralizedJM](https://github.com/DecentralizedJM)**  
*Empowering the Mudrex API community with intelligent assistance*
