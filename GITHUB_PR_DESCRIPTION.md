# 🚀 Mudrex API Bot - Complete Revamp

## Overview

Complete overhaul of the Mudrex API Intelligent Assistant into a production-ready, group-only Telegram bot with MCP integration, latest Gemini SDK, and comprehensive RAG-powered documentation support.

## 🎯 Key Changes

### Architecture Overhaul
- ✅ Migrated to latest `google-genai` SDK (replaces deprecated `google-generativeai`)
- ✅ Upgraded to `gemini-3-flash-preview` model
- ✅ Implemented service account model for MCP integration
- ✅ File-based vector store using Gemini embeddings
- ✅ Group-only bot (rejects DMs, responds when mentioned or API-related)

### MCP Integration
- ✅ Python wrapper for Mudrex MCP server (`https://mudrex.com/mcp`)
- ✅ Supports 2 public data tools: `list_futures`, `get_future`
- ✅ Blocks 18 personal account/trading tools for security
- ✅ Service account authentication support
- ✅ Comprehensive error handling and fallback modes

### RAG Knowledge Base
- ✅ 10 comprehensive documentation files covering entire Mudrex API
- ✅ 29 document chunks with semantic search
- ✅ Gemini `text-embedding-004` for embeddings
- ✅ Persistent vector store (`./data/chroma/vectors.pkl`)
- ✅ Automatic document ingestion pipeline

### Bot Personality & Behavior
- ✅ Junior Dev + Community Admin persona
- ✅ Smart query detection (responds to API questions automatically)
- ✅ Group-only mode with DM rejection
- ✅ Rate limiting (per-group)
- ✅ Context-aware responses with chat history

### Security & Safety
- ✅ `.gitignore` protects API keys and secrets
- ✅ Code-level blocking of personal account queries
- ✅ Trading actions blocked (read-only operations)
- ✅ Clear user messaging about data access limitations

### Railway Deployment Ready
- ✅ `railway.json` configuration
- ✅ `Procfile` for process management
- ✅ `nixpacks.toml` for build configuration
- ✅ `runtime.txt` for Python version
- ✅ Environment variable documentation

## 📁 File Structure

```
├── main.py                      # Entry point with async support
├── src/
│   ├── bot/telegram_bot.py     # Group-only bot handlers
│   ├── rag/                     # RAG pipeline (4 files)
│   ├── mcp/                     # MCP integration (2 files)
│   └── config/settings.py       # Configuration management
├── scripts/
│   ├── ingest_docs.py          # Document ingestion
│   └── scrape_docs.py         # Documentation scraper
├── docs/                        # API documentation (10 files)
├── requirements.txt             # Updated dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Protects secrets
└── railway.json                 # Railway deployment config
```

## 🔧 Technical Details

### Dependencies
- `google-genai>=1.0.0` (new SDK)
- `python-telegram-bot==21.0`
- `aiohttp>=3.9.0` (for MCP async calls)
- `scikit-learn>=1.3.0` (for vector similarity)

### Configuration
- **Model**: `gemini-3-flash-preview`
- **Embeddings**: `models/text-embedding-004`
- **Vector Store**: File-based pickle format
- **Storage**: `./data/chroma/vectors.pkl`

### MCP Tools
- ✅ `list_futures` - Public contract listings
- ✅ `get_future` - Public contract details
- ❌ All personal account tools (blocked)
- ❌ All trading tools (blocked)

## 🚀 Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your keys

# 3. Ingest documentation
python3 scripts/ingest_docs.py

# 4. Run bot
python3 main.py
```

## 📊 Features

### Bot Commands
- `/help` - Show help
- `/tools` - List available API tools
- `/mcp` - MCP setup guide
- `/futures` - List futures contracts
- `/stats` - Bot statistics

### Smart Response
- ✅ Responds when @mentioned (always)
- ✅ Responds to API-related questions (auto-detection)
- ❌ Ignores off-topic messages when not mentioned
- ❌ Rejects DMs with helpful message

## 🔒 Security

- ✅ `.gitignore` excludes `.env`, `*.pkl`, `data/`
- ✅ No API keys in code
- ✅ Personal account queries blocked in code
- ✅ Trading actions blocked
- ✅ Service account model (uses bot owner's key for public data only)

## 📈 Improvements

| Aspect | Before | After |
|--------|--------|-------|
| SDK | Deprecated | Latest `google-genai` |
| Model | `gemini-2.5-flash` | `gemini-3-flash-preview` |
| MCP | Not integrated | Full MCP wrapper |
| Storage | ChromaDB | File-based (portable) |
| Bot Mode | DMs + Groups | Group-only |
| Docs | 4 files | 10 files (29 chunks) |
| Security | Basic | Comprehensive |

## 🐛 Breaking Changes

- ⚠️ Bot no longer responds to DMs (group-only)
- ⚠️ Requires re-ingestion of documents
- ⚠️ New Gemini SDK (different import)

## ✅ Testing

```bash
python3 test_bot.py
```

All tests passing ✅

## 📚 Documentation

- Comprehensive README.md
- Setup guides
- MCP integration guide
- RAG knowledge explanation

## 🚂 Deployment

Railway-ready with `railway.json`. Just connect repo and set environment variables.

---

**Ready for Review & Merge** ✅
