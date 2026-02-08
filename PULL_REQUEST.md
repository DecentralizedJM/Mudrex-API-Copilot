# 🚀 Mudrex API Bot - Complete Revamp

## 📋 Overview

This PR revamps the Mudrex API Intelligent Assistant into a production-ready, group-only Telegram bot with MCP integration, latest Gemini SDK, and comprehensive RAG-powered documentation support.

## 🎯 Key Changes

### 1. **Architecture Overhaul**
- ✅ Migrated to latest `google-genai` SDK (replaces deprecated `google-generativeai`)
- ✅ Upgraded to `gemini-3-flash-preview` model
- ✅ Implemented service account model for MCP integration
- ✅ File-based vector store using Gemini embeddings
- ✅ Group-only bot (rejects DMs, responds when mentioned or API-related)

### 2. **MCP Integration**
- ✅ Python wrapper for Mudrex MCP server (`https://mudrex.com/mcp`)
- ✅ Supports 2 public data tools: `list_futures`, `get_future`
- ✅ Blocks 18 personal account/trading tools for security
- ✅ Service account authentication support
- ✅ Comprehensive error handling and fallback modes

### 3. **RAG Knowledge Base**
- ✅ 10 comprehensive documentation files covering entire Mudrex API
- ✅ 29 document chunks with semantic search
- ✅ Gemini `gemini-embedding-001` for embeddings (fallback if deprecated model configured)
- ✅ Persistent vector store (`./data/chroma/vectors.pkl`)
- ✅ Automatic document ingestion pipeline

### 4. **Bot Personality & Behavior**
- ✅ Junior Dev + Community Admin persona
- ✅ Smart query detection (responds to API questions automatically)
- ✅ Group-only mode with DM rejection
- ✅ Rate limiting (per-group)
- ✅ Context-aware responses with chat history

### 5. **Security & Safety**
- ✅ `.gitignore` protects API keys and secrets
- ✅ Code-level blocking of personal account queries
- ✅ Trading actions blocked (read-only operations)
- ✅ Clear user messaging about data access limitations

### 6. **Railway Deployment Ready**
- ✅ `railway.json` configuration
- ✅ `Procfile` for process management
- ✅ `nixpacks.toml` for build configuration
- ✅ `runtime.txt` for Python version
- ✅ Environment variable documentation

## 📁 File Structure

```
├── main.py                      # Entry point with async support
├── src/
│   ├── bot/
│   │   └── telegram_bot.py     # Group-only bot handlers
│   ├── rag/
│   │   ├── pipeline.py         # RAG orchestration
│   │   ├── vector_store.py     # File-based vector storage
│   │   ├── gemini_client.py    # Latest Gemini SDK integration
│   │   └── document_loader.py   # Document processing
│   ├── mcp/
│   │   ├── client.py           # MCP server wrapper
│   │   └── tools.py            # MCP tool definitions
│   └── config/
│       └── settings.py         # Configuration management
├── scripts/
│   ├── ingest_docs.py          # Document ingestion
│   └── scrape_docs.py         # Documentation scraper
├── docs/                        # API documentation (10 files)
├── data/chroma/                 # Vector store (auto-created)
├── requirements.txt             # Updated dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Protects secrets
└── railway.json                 # Railway deployment config
```

## 🔧 Technical Details

### Dependencies Updated
- `google-genai>=1.0.0` (new SDK)
- `python-telegram-bot==21.0`
- `aiohttp>=3.9.0` (for MCP async calls)
- `scikit-learn>=1.3.0` (for vector similarity)
- `beautifulsoup4>=4.12.0` (for doc scraping)

### Configuration
- **Model**: `gemini-3-flash-preview`
- **Embeddings**: `models/gemini-embedding-001`
- **Vector Store**: File-based pickle format
- **Storage**: `./data/chroma/vectors.pkl`

### MCP Tools Available
- ✅ `list_futures` - Public contract listings
- ✅ `get_future` - Public contract details
- ❌ All personal account tools (blocked)
- ❌ All trading tools (blocked)

## 🚀 Setup Instructions

### 1. Environment Variables
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
MUDREX_API_SECRET=your_api_secret  # Optional, for MCP public data
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Ingest Documentation
```bash
python3 scripts/ingest_docs.py
```

### 4. Run Bot
```bash
python3 main.py
```

## 📊 Features

### Bot Commands
- `/help` - Show help
- `/tools` - List available API tools
- `/mcp` - MCP setup guide
- `/futures` - List futures contracts (requires MCP)
- `/stats` - Bot statistics

### Smart Response Behavior
- ✅ Responds when @mentioned (always)
- ✅ Responds to API-related questions (auto-detection)
- ❌ Ignores off-topic messages when not mentioned
- ❌ Rejects DMs with helpful message

### Knowledge Sources
- **RAG**: 29 document chunks covering entire Mudrex API
- **MCP**: Live public data (contract listings)
- **Gemini**: AI reasoning and code generation

## 🔒 Security

- ✅ `.gitignore` excludes `.env`, `*.pkl`, `data/`
- ✅ No API keys in code
- ✅ Personal account queries blocked in code
- ✅ Trading actions blocked
- ✅ Service account model (uses bot owner's key for public data only)

## 📝 Documentation

- ✅ Comprehensive README.md
- ✅ Setup guides (QUICK_SETUP_GUIDE.md, ACTUAL_SETUP.md)
- ✅ MCP integration guide (SERVICE_ACCOUNT_SETUP.md)
- ✅ RAG knowledge explanation (RAG_KNOWLEDGE_EXPLAINED.md)
- ✅ What bot can fetch (WHAT_BOT_CAN_FETCH.md)

## 🧪 Testing

Run test suite:
```bash
python3 test_bot.py
```

Tests cover:
- ✅ Configuration validation
- ✅ MCP tools definition
- ✅ Document loading
- ✅ Gemini client initialization
- ✅ MCP client connection

## 🚂 Deployment

### Railway
1. Connect GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy (auto-detects `railway.json`)

### Manual
1. Set environment variables
2. Run `python3 scripts/ingest_docs.py`
3. Run `python3 main.py`

## 📈 Improvements Over Previous Version

| Aspect | Before | After |
|--------|--------|-------|
| **SDK** | Deprecated `google-generativeai` | Latest `google-genai` |
| **Model** | `gemini-2.5-flash` | `gemini-3-flash-preview` |
| **MCP** | Not integrated | Full MCP wrapper with 2 public tools |
| **Storage** | ChromaDB (complex) | File-based (simple, portable) |
| **Bot Mode** | DMs + Groups | Group-only (community focused) |
| **Docs** | 4 basic files | 10 comprehensive files (29 chunks) |
| **Security** | Basic | `.gitignore`, code-level blocking |
| **Deployment** | Manual | Railway-ready |

## 🐛 Breaking Changes

- ⚠️ Bot no longer responds to DMs (group-only)
- ⚠️ Requires re-ingestion of documents (new vector store format)
- ⚠️ Environment variable names unchanged but usage clarified

## ✅ Checklist

- [x] Updated to latest Gemini SDK
- [x] MCP integration implemented
- [x] RAG knowledge base created
- [x] Group-only mode configured
- [x] Security measures in place
- [x] Railway deployment ready
- [x] Documentation complete
- [x] Test suite passing
- [x] `.gitignore` configured
- [x] Code-level personal data blocking

## 📚 References

- [Mudrex MCP Documentation](https://docs.trade.mudrex.com/docs/mcp)
- [Mudrex API Documentation](https://docs.trade.mudrex.com/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)

## 👤 Author

DecentralizedJM

## 📄 License

MIT License - See LICENSE file

---

**Ready for Review & Merge** ✅
