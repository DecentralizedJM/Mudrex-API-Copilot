# Mudrex Co-pilot </> 

A **GROUP-ONLY** generic Telegram bot for private API traders community. Helps developers with Mudrex API documentation, coding questions, error debugging, and general API help.

> ⚠️ **GROUP-ONLY**: This bot only works in Telegram groups. It does NOT respond to DMs.
> 
> ⚠️ **SERVICE ACCOUNT MODEL**: This bot uses a read-only service account key to fetch PUBLIC data (prices, market info). It cannot access individual user accounts (positions, orders, balance).

## Features

- **Advanced RAG-Powered Answers**: Uses Gemini AI with state-of-the-art RAG techniques (inspired by [RAG_Techniques](https://github.com/NirDiamant/RAG_Techniques)) for accurate, hallucination-free API documentation responses
  - Document relevancy validation (Reliable RAG)
  - LLM-based reranking for improved quality
  - Query transformation for better retrieval
  - Iterative retrieval with query refinement
  - Context-based responses (no generic web knowledge)
- **Hallucination Prevention**: Validates document relevancy before use, uses only Mudrex documentation, and provides honest "I don't know" responses when information isn't available
- **MCP Integration**: Can access public/general information (like listing futures contracts)
- **Group-Only Mode**: Only responds when mentioned/tagged in groups, rejects DMs
- **Community Focus**: Designed for API traders group discussions - feedback, coding help, errors
- **Smart Filtering**: Only responds to API-related questions, ignores off-topic chat
- **Code Examples**: Provides working Python/JavaScript code snippets
- **Error Debugging**: Helps troubleshoot API errors and integration issues

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/DecentralizedJM/Mudrex-API-Intelligent-Assitant-.git
cd Mudrex-API-Intelligent-Assitant-

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy example config
cp .env.example .env

# Edit with your keys
nano .env  # or use any editor
```

Required settings:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

Optional (for public data access):
```env
MUDREX_API_SECRET=your_service_account_read_only_key
```

**Important**: Use your **personal API secret** from Mudrex. The bot uses this to fetch public market data (prices, contracts, status). The bot code is configured to block personal account queries - even though it has your key, it won't fetch user balances, orders, or positions. Users asking for personal data will get a message directing them to use Claude Desktop with MCP or the Mudrex dashboard.

### 3. Ingest Documentation

```bash
# Create/update documentation
python3 scripts/scrape_docs.py

# Ingest into vector store
python3 scripts/ingest_docs.py
```

### 4. Run

```bash
python3 main.py
```

## Bot Commands (Group-Only)

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/stats` | Bot statistics |
| `/tools` | Available MCP tools |
| `/mcp` | MCP setup guide |
| `/futures` | List futures contracts (public info) |

**Usage**: 
- Just ask your API question - bot automatically detects and responds
- Or tag with `@botname` to get attention
- Bot ignores off-topic messages when not tagged

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                         │
│  (Junior Dev + Community Admin personality)             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Advanced RAG Pipeline                    │   │
│  │  1. Initial Retrieval                            │   │
│  │  2. Iterative Retrieval (query transformation)   │   │
│  │  3. Low-Threshold Search (context gathering)     │   │
│  │  4. Document Relevancy Validation (Reliable)     │   │
│  │  5. LLM-based Reranking                          │   │ 
│  │  6. Context-Based Response (no Google Search)    │   │
│  └──────────────────────────────────────────────────┘   │
│         │                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ Vector Store │    │  MCP Client  │    │  Gemini   │  │
│  │ (Embeddings) │    │  (Live Data) │    │  (AI)     │  │
│  └──────────────┘    └──────────────┘    └───────────┘  │
│         │                   │                 │         │
│         ▼                   ▼                 │         │
│  ┌──────────────┐    ┌──────────────┐         │         │
│  │   Docs/FAQs  │    │ Mudrex API   │◄────────┘         │
│  │  (Knowledge) │    │ (Read-Only)  │                   │
│  └──────────────┘    └──────────────┘                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
├── main.py                 # Entry point
├── src/
│   ├── bot/               # Telegram bot handlers
│   │   └── telegram_bot.py
│   ├── rag/               # RAG pipeline
│   │   ├── pipeline.py
│   │   ├── vector_store.py
│   │   ├── gemini_client.py
│   │   └── document_loader.py
│   ├── mcp/               # MCP integration
│   │   ├── client.py
│   │   └── tools.py
│   └── config/            # Configuration
│       └── settings.py
├── scripts/
│   ├── ingest_docs.py     # Document ingestion
│   └── scrape_docs.py     # Documentation scraper
├── docs/                  # API documentation files
├── data/                  # Vector store data
├── requirements.txt
└── .env.example
```

## Advanced RAG Pipeline

The bot uses a sophisticated multi-stage RAG pipeline inspired by [RAG_Techniques](https://github.com/NirDiamant/RAG_Techniques) to prevent hallucinations and improve accuracy:

### Pipeline Flow

1. **Initial Retrieval**: Standard vector similarity search with threshold filtering
2. **Iterative Retrieval**: If no docs found, transforms query (step-back prompting, query expansion) and retries (max 2 iterations)
3. **Low-Threshold Search**: If still empty, searches with lower threshold (0.30) for broader context
4. **Document Relevancy Validation** (Reliable RAG): Uses Gemini to score if retrieved docs actually answer the query (filters out irrelevant docs with score < 0.6)
5. **LLM-based Reranking**: Reranks documents by relevance using Gemini for better quality
6. **Context-Based Response**: Generates response using only validated Mudrex documentation (no Google Search, no generic web knowledge)

### Techniques Applied

- **Reliable RAG**: Validates document relevancy before use
- **Reranking**: LLM-based scoring improves document quality
- **Query Transformations**: Step-back prompting and query expansion improve retrieval
- **Iterative Retrieval**: Multiple retrieval rounds with query refinement
- **Context Enrichment**: Low-threshold search for broader context
- **Hallucination Prevention**: Only uses Mudrex docs, honest "I don't know" responses

### Template Responses

For known missing features (e.g., TradingView integrations, webhooks), the bot provides friendly roadmap responses instead of guessing.

## MCP Integration

The bot integrates with Mudrex's MCP (Model Context Protocol) server for live data:

```python
# Safe endpoints (read-only)
- get_market_price
- get_ticker_24hr
- get_orderbook
- get_klines
- get_account_balance
- get_positions
- get_open_orders

# Blocked endpoints (safety)
- place_order
- cancel_order
- modify_order
- close_position
```

## Bot Personality

The bot acts as a **Junior Dev + Community Admin**:

✅ **Does:**
- Answers API questions directly
- Provides working code examples
- Debugs integration issues
- Asks clarifying questions when needed
- Tags @DecentralizedJM for escalations

❌ **Doesn't:**
- Engage in off-topic chat
- Give trading advice
- Execute order placement
- Mention competitor exchanges

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `MUDREX_API_SECRET` | No | - | Mudrex API key (read-only) |
| `GEMINI_MODEL` | No | gemini-3-flash-preview | Gemini model |
| `MCP_ENABLED` | No | true | Enable MCP integration |
| `ALLOWED_CHAT_IDS` | No | - | Restrict to specific chats |
| `SIMILARITY_THRESHOLD` | No | 0.45 | Vector similarity threshold for retrieval |
| `CONTEXT_SEARCH_THRESHOLD` | No | 0.30 | Lower threshold for context gathering when no high-similarity docs found |
| `RELEVANCY_THRESHOLD` | No | 0.6 | Minimum relevancy score to use a document (Reliable RAG) |
| `RERANK_TOP_K` | No | 5 | Number of top documents after reranking |
| `MAX_ITERATIVE_RETRIEVAL` | No | 2 | Maximum iterations for iterative retrieval with query transformation |

## Development

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python3 main.py

# Update documentation
python3 scripts/scrape_docs.py
python3 scripts/ingest_docs.py

# Test MCP connection
python3 -c "
import asyncio
from src.mcp import MudrexMCPClient
async def test():
    client = MudrexMCPClient()
    await client.connect()
    print(client.get_available_tools())
asyncio.run(test())
"
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

**DecentralizedJM** - [GitHub](https://github.com/DecentralizedJM)

---

*Built with ❤️ for the Mudrex developer community*
