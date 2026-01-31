# Mudrex API Copilot

An **API Copilot** for the Mudrex Futures API community. Helps developers with code examples, API integration, error debugging, and onboarding.

> **Reactive Mode**: The bot only responds when explicitly engaged (@mentioned, replied to, or via quote+mention). It does NOT auto-respond to keyword detection.

## Features

- **Code-First Responses**: Working Python/JavaScript snippets for every "how to" question
- **Error Debugging**: Analyzes logs, error codes, and provides fixes
- **Advanced RAG Pipeline**: Gemini AI with document relevancy validation, LLM reranking, and query transformation
- **Hallucination Prevention**: Uses only Mudrex documentation, never guesses
- **MCP Integration**: Live market data via Mudrex MCP server (500+ futures pairs)
- **Redis Caching**: Query/response caching to reduce Gemini API calls
- **Community SDK Recommendations**: Suggests the [community Python SDK](https://github.com/DecentralizedJM/mudrex-api-trading-python-sdk) for easier onboarding

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/DecentralizedJM/Mudrex-API-Copilot.git
cd Mudrex-API-Copilot

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

**Required:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

**Optional:**
```env
MUDREX_API_SECRET=your_api_secret          # For live market data
REDIS_URL=redis://localhost:6379           # For caching
ADMIN_USER_IDS=123456789,987654321         # Admin Telegram IDs
```

### 3. Run

```bash
python3 main.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help and usage examples |
| `/endpoints` | List all API endpoints with doc links |
| `/listfutures` | Count of available futures pairs |
| `/tools` | MCP server tools list |
| `/mcp` | MCP setup guide for Claude Desktop |
| `/stats` | Bot statistics (admin only) |

**Admin Commands:**
| Command | Description |
|---------|-------------|
| `/learn <text>` | Teach the bot new information |
| `/set_fact KEY value` | Set a strict fact |
| `/delete_fact KEY` | Delete a fact |

## When Does the Bot Respond?

The bot is **reactive only** — it responds when:

1. **@mentioned** directly in a message
2. **Replied to** (conversation continuation)
3. **Quote + mention** — someone quotes another user's message and tags the bot

It does **NOT** auto-detect keywords and respond proactively.

## MCP Integration

The bot integrates with Mudrex's MCP (Model Context Protocol) server for live data.

### Safe Tools (Read-Only)

| Tool | Description |
|------|-------------|
| `list_futures` | List all available futures contracts (500+ pairs) |
| `get_future` | Get details for a specific contract |
| `get_orders` | List all open orders |
| `get_order` | Fetch a specific order by ID |
| `get_order_history` | Get historical orders |
| `get_positions` | List all open positions |
| `get_position_history` | Get historical positions |
| `get_leverage` | Get current leverage for a contract |
| `get_liquidation_price` | Compute liquidation price for a position |
| `get_available_funds` | Get available funds for trading |
| `get_fee_history` | Get trading fee history |

### Confirmation Required (User must confirm)

| Tool | Description |
|------|-------------|
| `place_order` | Place LONG/SHORT order with optional SL/TP |
| `amend_order` | Amend an existing order |
| `cancel_order` | Cancel an order |
| `close_position` | Close a position at market |
| `reverse_position` | Flip long to short or vice versa |
| `place_risk_order` | Set stop-loss / take-profit |
| `amend_risk_order` | Modify SL/TP on a position |
| `set_leverage` | Set leverage for a contract |
| `add_margin` | Add margin to a position |

### MCP Setup for Claude Desktop

```json
{
  "mcpServers": {
    "mcp-futures-trading": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mudrex.com/mcp", "--header", "X-Authentication:${API_SECRET}"],
      "env": {"API_SECRET": "<your-api-secret>"}
    }
  }
}
```

Docs: https://docs.trade.mudrex.com/docs/mcp

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot (Reactive)                   │
│                    API Copilot Persona                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Advanced RAG Pipeline                  │     │
│  │  1. Query Transformation (step-back, expansion)     │     │
│  │  2. Vector Similarity Search (embeddings)           │     │
│  │  3. Document Relevancy Validation (Reliable RAG)    │     │
│  │  4. LLM-based Reranking                             │     │
│  │  5. Context-Based Response (no generic knowledge)   │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                   │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │ Vector Store │  │ Redis Cache │  │   Gemini AI       │   │
│  │ (Embeddings) │  │ (Responses) │  │ gemini-3-flash    │   │
│  └──────────────┘  └─────────────┘  └───────────────────┘   │
│         │                │                    │              │
│         ▼                │                    ▼              │
│  ┌──────────────┐        │           ┌──────────────┐       │
│  │   Docs/FAQs  │        │           │  MCP Client  │       │
│  │  (Markdown)  │        │           │ (Live Data)  │       │
│  └──────────────┘        │           └──────────────┘       │
│                          │                    │              │
│                          ▼                    ▼              │
│                   ┌─────────────────────────────────┐       │
│                   │      Mudrex Futures API         │       │
│                   │  https://trade.mudrex.com/fapi  │       │
│                   └─────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
├── main.py                 # Entry point
├── src/
│   ├── bot/                # Telegram bot handlers
│   │   └── telegram_bot.py
│   ├── rag/                # RAG pipeline
│   │   ├── pipeline.py
│   │   ├── vector_store.py
│   │   ├── gemini_client.py
│   │   ├── document_loader.py
│   │   ├── cache.py            # Redis caching
│   │   ├── context_manager.py  # Conversation context
│   │   └── semantic_memory.py  # Long-term memory
│   ├── mcp/                # MCP integration
│   │   ├── client.py
│   │   └── tools.py
│   ├── tasks/              # Scheduled tasks
│   │   ├── scheduler.py
│   │   ├── changelog_watcher.py
│   │   └── futures_listing_watcher.py
│   ├── lib/                # Utilities
│   │   └── error_reporter.py
│   └── config/             # Configuration
│       └── settings.py
├── docs/                   # API documentation (RAG source)
├── scripts/
│   ├── ingest_docs.py
│   └── scrape_docs.py
├── requirements.txt
└── .env.example
```

## Advanced RAG Pipeline

The bot uses a multi-stage RAG pipeline for accurate, hallucination-free responses:

### Pipeline Stages

1. **Query Transformation**: Step-back prompting and query expansion for better retrieval
2. **Vector Similarity Search**: Embeddings-based document retrieval with threshold filtering
3. **Iterative Retrieval**: If no docs found, transforms query and retries (max 2 iterations)
4. **Document Relevancy Validation**: Gemini scores if docs actually answer the query (filters score < 0.6)
5. **LLM-based Reranking**: Reorders documents by relevance
6. **Context-Based Response**: Generates response using only validated Mudrex documentation

### Hallucination Prevention

- Uses only Mudrex documentation (no generic web knowledge)
- Validates document relevancy before use
- Template responses for known missing features (webhooks, TradingView, etc.)
- Honest "Couldn't find that" responses with doc links

## Bot Persona

The bot acts as an **API Copilot** (like GitHub Copilot for Mudrex API):

**Does:**
- Provides working code examples (Python/JS)
- Debugs API errors and integration issues
- Explains authentication (`X-Authentication` header)
- Links to official documentation
- Suggests the community SDK for easier onboarding

**Doesn't:**
- Auto-respond to keywords (reactive only)
- Give trading advice or strategies
- Mention competitor exchanges
- Guess at Mudrex-specific details

**Out-of-scope response:**
> Couldn't find that. Docs: https://docs.trade.mudrex.com — @DecentralizedJM can help with specifics.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `MUDREX_API_SECRET` | No | - | Mudrex API secret (for live data) |
| `GEMINI_MODEL` | No | `gemini-3-flash-preview` | Gemini model |
| `EMBEDDING_MODEL` | No | `models/gemini-embedding-001` | Embedding model |
| `REDIS_ENABLED` | No | `false` | Enable Redis caching |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection URL |
| `ADMIN_USER_IDS` | No | - | Comma-separated admin Telegram IDs |
| `ALLOWED_CHAT_IDS` | No | - | Restrict to specific chat IDs |
| `SIMILARITY_THRESHOLD` | No | `0.45` | Vector similarity threshold |
| `RELEVANCY_THRESHOLD` | No | `0.6` | Min relevancy score for docs |
| `RERANK_TOP_K` | No | `5` | Top documents after reranking |
| `MAX_RESPONSE_LENGTH` | No | `4096` | Telegram message char limit |

## Community Resources

- **Python SDK**: https://github.com/DecentralizedJM/mudrex-api-trading-python-sdk
  - Symbol-first trading, 500+ pairs, MCP support, handles auth
- **Trade Ideas Broadcaster**: https://github.com/DecentralizedJM/TIA-Service-Broadcaster
  - WebSocket streaming for signals
- **API Docs**: https://docs.trade.mudrex.com
- **MCP Docs**: https://docs.trade.mudrex.com/docs/mcp

## Development

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python3 main.py

# Update documentation
python3 scripts/scrape_docs.py
python3 scripts/ingest_docs.py

# Test imports
python3 -c "from src.bot import MudrexBot; print('OK')"
```

## Deployment (Railway)

1. Create a new Railway project
2. Connect your GitHub repo
3. Add environment variables in Railway dashboard
4. Deploy

For Redis, add a Redis service in Railway and use the internal URL.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

**DecentralizedJM** - [GitHub](https://github.com/DecentralizedJM)

---

*Built for the Mudrex developer community*
