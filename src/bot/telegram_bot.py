"""
Mudrex API Bot - Telegram Handler
GROUP-ONLY bot for private API traders community
Responds only when mentioned/tagged in groups

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import asyncio
import logging
import os
import re
from typing import Optional, Dict, Tuple, List, Any
from collections import defaultdict
import time

from telegram import Update, BotCommand, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode, ChatAction, ChatType
from telegram.error import Conflict, TimedOut, NetworkError

from ..config import config
from ..rag import RAGPipeline
from ..mcp import MudrexMCPClient, MudrexTools
from ..tasks.futures_listing_watcher import fetch_all_futures_symbols, fetch_all_futures_symbols_via_rest
from ..lib.error_reporter import report_error

logger = logging.getLogger(__name__)

# Intro message when bot is added to a group
GROUP_INTRO_MESSAGE = """Hi community! 👋

I'm your **Mudrex API copilot**. You can:
• Ask me questions about the API — auth, endpoints, errors, code examples
• Tag me with @ when you need help in the group
• Use /help to see what I can do
• Use /endpoints for API endpoints, /listfutures for futures count

Just mention me or reply to my messages to get started."""

# Warning to append when user has shared their API secret in the chat
API_KEY_EXPOSED_WARNING = (
    "⚠️ **Your API key is now exposed.** Please rotate or revoke it immediately in the "
    "API Management Dashboard. Do not use this key anymore."
)


def _user_shared_api_secret(message: str) -> bool:
    """Return True if the message looks like the user pasted their API secret (e.g. 'my API secret is X')."""
    if not message or len(message) < 10:
        return False
    lower = message.lower()
    # Patterns that suggest they shared the key: "api secret is", "api key is", "my api secret", "secret is"
    if "api secret is" in lower or "api key is" in lower:
        return True
    if "my api secret" in lower or "my api key" in lower:
        # Likely shared if there's more text after (the key or "help me connect")
        return True
    return False


def _extract_shared_api_secret(message: str) -> Optional[str]:
    """
    Try to extract the API secret the user pasted.
    Looks for phrases like "api secret is" or "api key is" and returns the first non-empty line after it.
    """
    if not message:
        return None
    lower = message.lower()
    markers = ["api secret is", "api key is", "my api secret", "my api key"]
    pos = -1
    for m in markers:
        idx = lower.find(m)
        if idx != -1:
            pos = idx + len(m)
            break
    if pos == -1:
        return None
    # Get the substring after the marker and look for the first non-empty line
    tail = message[pos:]
    for line in tail.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return None


class RateLimiter:
    """
    Enhanced rate limiter with multi-level limits and Redis backend.
    
    Implements token bucket algorithm with:
    - Per-user limits: 10 requests/minute
    - Per-group limits: 50 requests/minute
    - Global limits: 500 requests/minute
    
    Falls back to in-memory storage if Redis unavailable.
    """
    
    # Rate limit configurations
    USER_LIMIT = 10  # requests per minute per user
    GROUP_LIMIT = 50  # requests per minute per group
    GLOBAL_LIMIT = 500  # requests per minute globally
    WINDOW_SECONDS = 60
    
    def __init__(self, max_messages: int = 50, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window = window_seconds
        
        # In-memory storage (fallback)
        self.user_messages: Dict[int, list] = defaultdict(list)
        self.group_messages: Dict[int, list] = defaultdict(list)
        self.global_messages: List[float] = []
        
        # Try to get Redis client
        self.redis_client = None
        try:
            from ..rag.cache import RedisCache
            cache = RedisCache()
            if cache.connected and cache.redis_client:
                self.redis_client = cache.redis_client
                logger.info("RateLimiter using Redis backend")
        except Exception as e:
            logger.debug(f"RateLimiter using in-memory backend: {e}")
    
    def _clean_old_entries(self, entries: List[float], now: float) -> List[float]:
        """Remove entries older than the window"""
        return [t for t in entries if now - t < self.window]
    
    def _check_redis_limit(self, key: str, limit: int) -> bool:
        """Check rate limit using Redis with sliding window"""
        if not self.redis_client:
            return True  # If Redis unavailable, skip this check
        
        try:
            now = time.time()
            window_start = now - self.WINDOW_SECONDS
            
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
            pipe.zcard(key)  # Count current entries
            pipe.zadd(key, {str(now): now})  # Add current request
            pipe.expire(key, self.WINDOW_SECONDS + 10)  # Set expiry
            results = pipe.execute()
            
            current_count = results[1]
            return current_count < limit
            
        except Exception as e:
            logger.debug(f"Redis rate limit check failed: {e}")
            return True  # Fail open
    
    def _check_memory_limit(self, storage: Dict[int, list], key: int, limit: int) -> bool:
        """Check rate limit using in-memory storage"""
        now = time.time()
        storage[key] = self._clean_old_entries(storage[key], now)
        
        if len(storage[key]) >= limit:
            return False
        
        storage[key].append(now)
        return True
    
    def is_allowed(self, chat_id: int, user_id: int = None) -> bool:
        """
        Check if request is allowed under all rate limits.
        
        Args:
            chat_id: The group/chat ID
            user_id: Optional user ID for per-user limits
            
        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        
        # 1. Check global limit
        if self.redis_client:
            if not self._check_redis_limit("ratelimit:global", self.GLOBAL_LIMIT):
                logger.warning("Global rate limit exceeded")
                return False
        else:
            self.global_messages = self._clean_old_entries(self.global_messages, now)
            if len(self.global_messages) >= self.GLOBAL_LIMIT:
                logger.warning("Global rate limit exceeded (in-memory)")
                return False
            self.global_messages.append(now)
        
        # 2. Check group limit
        group_key = f"ratelimit:group:{chat_id}"
        if self.redis_client:
            if not self._check_redis_limit(group_key, self.GROUP_LIMIT):
                logger.info(f"Group rate limit exceeded for {chat_id}")
                return False
        else:
            if not self._check_memory_limit(self.group_messages, chat_id, self.GROUP_LIMIT):
                logger.info(f"Group rate limit exceeded for {chat_id} (in-memory)")
                return False
        
        # 3. Check user limit (if user_id provided)
        if user_id:
            user_key = f"ratelimit:user:{user_id}"
            if self.redis_client:
                if not self._check_redis_limit(user_key, self.USER_LIMIT):
                    logger.info(f"User rate limit exceeded for {user_id}")
                    return False
            else:
                if not self._check_memory_limit(self.user_messages, user_id, self.USER_LIMIT):
                    logger.info(f"User rate limit exceeded for {user_id} (in-memory)")
                    return False
        
        return True
    
    def get_remaining(self, chat_id: int, user_id: int = None) -> Dict[str, int]:
        """Get remaining requests for each limit level"""
        now = time.time()
        
        # Calculate remaining for each level
        remaining = {
            "global": self.GLOBAL_LIMIT,
            "group": self.GROUP_LIMIT,
            "user": self.USER_LIMIT if user_id else None
        }
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.zcount("ratelimit:global", now - self.WINDOW_SECONDS, now)
                pipe.zcount(f"ratelimit:group:{chat_id}", now - self.WINDOW_SECONDS, now)
                if user_id:
                    pipe.zcount(f"ratelimit:user:{user_id}", now - self.WINDOW_SECONDS, now)
                results = pipe.execute()
                
                remaining["global"] = max(0, self.GLOBAL_LIMIT - results[0])
                remaining["group"] = max(0, self.GROUP_LIMIT - results[1])
                if user_id:
                    remaining["user"] = max(0, self.USER_LIMIT - results[2])
            except Exception:
                pass  # Return defaults on error
        else:
            self.global_messages = self._clean_old_entries(self.global_messages, now)
            remaining["global"] = max(0, self.GLOBAL_LIMIT - len(self.global_messages))
            
            self.group_messages[chat_id] = self._clean_old_entries(self.group_messages[chat_id], now)
            remaining["group"] = max(0, self.GROUP_LIMIT - len(self.group_messages[chat_id]))
            
            if user_id:
                self.user_messages[user_id] = self._clean_old_entries(self.user_messages[user_id], now)
                remaining["user"] = max(0, self.USER_LIMIT - len(self.user_messages[user_id]))
        
        return remaining


class MudrexBot:
    """
    AI co-pilot for the Mudrex API community. Uses MCP whenever needed for live data.
    GROUP-ONLY: Responds in groups when mentioned or when the message is API-related.
    """
    
    def __init__(self, rag_pipeline: RAGPipeline, mcp_client: Optional[MudrexMCPClient] = None):
        self.rag_pipeline = rag_pipeline
        self.mcp_client = mcp_client
        self.rate_limiter = RateLimiter(
            max_messages=config.RATE_LIMIT_MESSAGES,
            window_seconds=config.RATE_LIMIT_WINDOW
        )
        
        # Conflict tracking
        self.conflict_count = 0
        self.max_conflicts = 5  # Stop after 5 consecutive conflicts
        
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        self._register_handlers()
        self._register_error_handlers()
        
        logger.info("MudrexBot initialized (AI co-pilot, GROUP-ONLY)")
    
    def _register_handlers(self):
        """Register command and message handlers"""
        # Commands - Available in Groups AND DMs
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        self.app.add_handler(CommandHandler("tools", self.cmd_tools))
        self.app.add_handler(CommandHandler("mcp", self.cmd_mcp))
        
        # Futures Tools
        self.app.add_handler(CommandHandler("futures", self.cmd_futures))
        self.app.add_handler(CommandHandler("listfutures", self.cmd_futures))  # Alias
        self.app.add_handler(CommandHandler("endpoints", self.cmd_endpoints))
        
        # Admin Commands (Work in Groups & DM for admins ideally, but keeping group-only filter for consistency unless DM needed)
        # Actually, let's allow admins to teach in DMs too! 
        # But wait, self.reject_dm blocks DMs. Let's keep it simple: Admin commands work in GROUPS for now.
        self.app.add_handler(CommandHandler("learn", self.cmd_learn)) # Removed ChatType filter to allow flexibility if we open DMs later
        self.app.add_handler(CommandHandler("set_fact", self.cmd_set_fact))
        self.app.add_handler(CommandHandler("delete_fact", self.cmd_delete_fact))
        self.app.add_handler(CommandHandler("clearcache", self.cmd_clearcache))
        
        # Message handler - ONLY in groups, only when mentioned/tagged
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
                self.handle_message
            )
        )
        
        # Bot added to a group — send intro
        self.app.add_handler(
            ChatMemberHandler(self.on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER)
        )

        # Reject DMs
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.PRIVATE,
                self.handle_dm
            )
        )
        
        # Document Handler (File Uploads)
        self.app.add_handler(
            MessageHandler(
                filters.Document.ALL & filters.ChatType.PRIVATE,
                self.handle_document
            )
        )
    
    def _register_error_handlers(self):
        """Register error handlers for runtime errors"""
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
            """Handle errors during polling and message processing"""
            error = context.error
            
            if isinstance(error, Conflict):
                self.conflict_count += 1
                logger.error("=" * 60)
                logger.error(f"RUNTIME CONFLICT ERROR #{self.conflict_count} - Multiple bot instances detected!")
                logger.error("=" * 60)
                logger.error("Another bot instance started polling while this one was running.")
                logger.error("This usually means:")
                logger.error("  1. A new deployment started while old one is still running")
                logger.error("  2. Local dev instance conflicts with production")
                logger.error("  3. Railway auto-restarted but old container didn't stop")
                logger.error("")
                
                if self.conflict_count >= self.max_conflicts:
                    logger.error(f"⚠️  STOPPING POLLING: {self.max_conflicts} consecutive conflicts detected!")
                    logger.error("This instance will stop polling to prevent log spam.")
                    logger.error("ACTION REQUIRED:")
                    logger.error("  1. Check Railway for duplicate deployments")
                    logger.error("  2. Stop ALL other bot instances")
                    logger.error("  3. Wait 60 seconds for Telegram to release the connection")
                    logger.error("  4. Restart this instance")
                    logger.error("=" * 60)
                    # Stop polling gracefully
                    try:
                        await self.app.updater.stop()
                        logger.info("Polling stopped due to repeated conflicts")
                    except Exception as stop_error:
                        logger.error(f"Error stopping updater: {stop_error}")
                    return
                else:
                    logger.error(f"Action: Continuing (conflict {self.conflict_count}/{self.max_conflicts})")
                    logger.error("Check Railway for duplicate deployments and stop them.")
                    logger.error("=" * 60)
                
                # Report to Station Master
                try:
                    await report_error(error, "exception", context={
                        "error_type": "telegram_runtime_conflict",
                        "conflict_count": self.conflict_count
                    })
                except Exception:
                    pass
                # Don't crash - just log and continue (until max conflicts)
                return
            
            # Log other errors
            logger.error(f"Unhandled error in update handler: {error}", exc_info=error)
            try:
                await report_error(error, "exception", context={"handler": "telegram_error_handler"})
            except Exception:
                pass
        
        # Register the error handler
        self.app.add_error_handler(error_handler)
        logger.info("Handlers registered (GROUP-ONLY)")
    
    async def handle_dm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Direct Messages
        - Admins: Teacher Mode active (can teach via natural language)
        - Users: Rejected (Bot is group-only)
        """
        user_id = update.effective_user.id
        
        # 1. ADMIN LOGIC (Teacher Mode)
        if self._is_admin(user_id):
            message = update.message.text
            if not message:
                return

            await update.message.chat.send_action(ChatAction.TYPING)
            
            # Analyze intent for teaching
            intent = self.rag_pipeline.gemini_client.parse_learning_instruction(message)
            
            if intent.get('action') == 'SET_FACT':
                key = intent.get('key')
                value = intent.get('value')
                if key and value:
                    self.rag_pipeline.set_fact(key, value)
                    await update.message.reply_text(f"Got it — **{key}** = {value}", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("Couldn't parse that. Try: \"X is Y\" or `/set_fact KEY value`", parse_mode=ParseMode.MARKDOWN)
                return
            
            elif intent.get('action') == 'LEARN':
                content = intent.get('content') or message
                self.rag_pipeline.learn_text(content)
                await update.message.reply_text("Got it — I'll remember that.", parse_mode=ParseMode.MARKDOWN)
                return
            
            # If no teaching intent, normal RAG query (for testing)
            result = self.rag_pipeline.query(message)
            await self._send_response(update, result['answer'])
            return

        # 2. NON-ADMIN LOGIC (Reject)
        if update.message:
            await update.message.reply_text(
                "Hey! I only answer questions in the group — tag me there with @ and I'll help out."
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle File Uploads (Admin Only)
        Allows bulk learning from files (.txt, .md, .json, .py)
        """
        user_id = update.effective_user.id
        
        # 1. Access Control
        if not self._is_admin(user_id):
            await update.message.reply_text(f"Admin only. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return

        doc = update.message.document
        file_name = doc.file_name or "document"
        
        # 2. File Type Validation
        allowed_extensions = {'.txt', '.md', '.json', '.py', '.yaml', '.yml', '.rst'}
        is_valid = any(file_name.lower().endswith(ext) for ext in allowed_extensions)
        
        if not is_valid:
            await update.message.reply_text("Supported formats: .txt, .md, .json, .py, .yaml")
            return

        # 3. Process File
        status_msg = await update.message.reply_text("Processing...")
        try:
            # Download file
            new_file = await doc.get_file()
            file_content = await new_file.download_as_bytearray()
            text_content = file_content.decode('utf-8')
            
            # Learn Text (prepend filename; pass metadata)
            knowledge = f"file: {file_name}\n\n{text_content}"
            self.rag_pipeline.learn_text(knowledge, metadata={"source": "admin_upload", "filename": file_name})
            
            await status_msg.edit_text(f"Added **{file_name}**.", parse_mode=ParseMode.MARKDOWN)
            
        except UnicodeDecodeError:
            await status_msg.edit_text("Couldn't read that — needs to be a text file (UTF-8).")
        except Exception as e:
            logger.error(f"File upload error: {e}")
            await status_msg.edit_text("Something went wrong processing the file.")

    async def on_my_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """When the bot is added to a group, send an intro message."""
        result = update.my_chat_member
        if not result or not context.bot:
            return
        chat = result.chat
        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            return
        # Only react when *our* bot was added (not some other chat_member update)
        if result.new_chat_member.user.id != context.bot.id:
            return
        diff = result.difference()
        status_change = diff.get("status")
        if not status_change:
            return
        old_status, new_status = status_change
        was_member = old_status in (
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ) or (old_status == ChatMember.RESTRICTED and diff.get("is_member", (None, None))[0] is True)
        is_member = new_status in (
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ) or (new_status == ChatMember.RESTRICTED and diff.get("is_member", (None, None))[1] is True)
        if was_member or not is_member:
            return
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=GROUP_INTRO_MESSAGE,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            logger.info(f"Sent group intro to chat {chat.id} ({chat.title})")
        except Exception as e:
            logger.warning(f"Could not send group intro to {chat.id}: {e}")

    async def setup_commands(self):
        """Set up bot commands menu"""
        commands = [
            BotCommand("help", "Show help"),
            BotCommand("tools", "MCP server tools list"),
            BotCommand("mcp", "MCP setup guide"),
            BotCommand("listfutures", "List futures contracts (count)"),
            BotCommand("endpoints", "API endpoints"),

            BotCommand("stats", "Bot statistics"),
        ]
        await self.app.bot.set_my_commands(commands)
    
    # ==================== Commands ====================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome = """Hey! I help with Mudrex API questions — auth, endpoints, errors, code examples.

Just ask your question or tag me with @.

/help — what I can do
/endpoints — API endpoints
/listfutures — list futures pairs (count)"""
        
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """*What I help with:*
• API auth — just `X-Authentication`, no HMAC/signatures
• Endpoints and code examples (Python/JS)
• Error debugging (-1121, 404, etc.)
• Live futures data when you ask

*Example questions:*
"How do I authenticate?"
"What's error -1121?"
"List futures"
"Show me how to place an order"

*Commands:*
/endpoints — API endpoints list
/listfutures — count of futures pairs
/mcp — setup guide for Claude Desktop

For personal account data (positions, orders), use Claude Desktop with your own API key."""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command — admin only"""
        user_id = update.effective_user.id
        if not self._is_admin(user_id):
            await update.message.reply_text(f"Admin only. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return
        stats = self.rag_pipeline.get_stats()
        
        mcp_status = "Connected" if self.mcp_client and self.mcp_client.is_connected() else "Not connected"
        
        auth_status = "Service Account" if self.mcp_client and self.mcp_client.is_authenticated() else "Not configured"
        
        stats_text = f"""*Bot Stats*

Model: {stats['model']}
Docs indexed: {stats['total_documents']}
MCP: {mcp_status}
Auth: {auth_status}"""
        
        # Add cache statistics if available
        if self.rag_pipeline.cache:
            cache_stats = self.rag_pipeline.cache.get_stats()
            if cache_stats.get('enabled'):
                cache_status = "Connected" if cache_stats.get('connected') else "Not connected"
                hit_rate = cache_stats.get('hit_rate', 0.0)
                hits = cache_stats.get('hits', 0)
                misses = cache_stats.get('misses', 0)
                stats_text += f"\n\n*Cache*: {cache_status}"
                if cache_stats.get('connected'):
                    stats_text += f"\nHit rate: {hit_rate:.1f}% ({hits} hits, {misses} misses)"
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_tools(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tools command — MCP server tools list. Plain text to avoid Telegram Markdown parse errors."""
        tools_text = MudrexTools.get_tools_summary()
        tools_text += "\n\nFor personal data (positions, orders), use Claude Desktop with your own API key.\n/mcp — setup guide"
        await update.message.reply_text(tools_text)
    
    async def cmd_mcp(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mcp command"""
        mcp_text = """*MCP Setup (Claude Desktop)*

MCP lets Claude interact with your Mudrex account directly.

*Steps:*
1. Install Node.js (nodejs.org)
2. Claude Desktop → Settings → Developer → Edit Config
3. Add:
```
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
4. Get your API secret from trade.mudrex.com
5. Restart Claude Desktop

Docs: docs.trade.mudrex.com/docs/mcp"""
        
        await update.message.reply_text(mcp_text, parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_futures(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /futures and /listfutures — count via GET /fapi/v1/futures (REST) or MCP fallback."""
        await update.message.chat.send_action(ChatAction.TYPING)
        doc_url = "https://docs.trade.mudrex.com/docs/get-asset-listing"
        msg_tail = f"To see the full list: GET /fapi/v1/futures — {doc_url}"

        if config.MUDREX_API_SECRET:
            symbols = await fetch_all_futures_symbols_via_rest(config.MUDREX_API_SECRET)
        elif self.mcp_client:
            symbols = await fetch_all_futures_symbols(self.mcp_client)
        else:
            await update.message.reply_text(
                f"*List futures*\n\n{msg_tail}\n\nSet MUDREX_API_SECRET in .env to show the count here.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        n = len(symbols)
        await update.message.reply_text(
            f"There are **{n}** futures pairs listed. {msg_tail}",
            parse_mode=ParseMode.MARKDOWN
        )

    # (name, method, path, doc_slug) — doc_slug → https://docs.trade.mudrex.com/docs/{slug}
    _API_ENDPOINTS = [
        ("Get spot funds", "GET", "/fapi/v1/wallet/funds", "get-spot-funds"),
        ("Transfer funds (spot ↔ futures)", "POST", "/fapi/v1/wallet/futures/transfer", "post-transfer-funds"),
        ("Get futures funds", "GET", "/fapi/v1/futures/funds", "get-available-funds-futures"),
        ("Get asset listing", "GET", "/fapi/v1/futures", "get-asset-listing"),
        ("Get asset by id", "GET", "/fapi/v1/futures/:asset_id", "get"),
        ("Get leverage", "GET", "/fapi/v1/futures/:asset_id/leverage", "get-leverage-by-asset-id"),
        ("Set leverage", "POST", "/fapi/v1/futures/:asset_id/leverage", "set"),
        ("Place order", "POST", "/fapi/v1/futures/:asset_id/order", "post-market-order"),
        ("Get open orders", "GET", "/fapi/v1/futures/orders", "get-open-orders"),
        ("Get order by id", "GET", "/fapi/v1/futures/orders/:order_id", "get-order-by-id"),
        ("Amend order", "PATCH", "/fapi/v1/futures/orders/:order_id", "orders"),
        ("Cancel order", "DELETE", "/fapi/v1/futures/orders/:order_id", "delete-order"),
        ("Get order history", "GET", "/fapi/v1/futures/orders/history", "get-order-history"),
        ("Get open positions", "GET", "/fapi/v1/futures/positions", "get-open-positions"),
        ("Get liquidation price", "GET", "/fapi/v1/futures/positions/:position_id/liq-price", "get-liquidation-price"),
        ("Add margin", "POST", "/fapi/v1/futures/positions/:position_id/add-margin", "add-margin"),
        ("Place risk order", "POST", "/fapi/v1/futures/positions/:position_id/riskorder", "set-sl-tp"),
        ("Amend risk order", "PATCH", "/fapi/v1/futures/positions/:position_id/riskorder", "edit-sl-tp"),
        ("Reverse position", "POST", "/fapi/v1/futures/positions/:position_id/reverse", "reverse"),
        ("Partial close position", "POST", "/fapi/v1/futures/positions/:position_id/close/partial", "partial-close"),
        ("Close position", "POST", "/fapi/v1/futures/positions/:position_id/close", "square-off"),
        ("Get position history", "GET", "/fapi/v1/futures/positions/history", "get-position-history"),
        ("Get fee history", "GET", "/fapi/v1/futures/fee/history", "fees"),
    ]

    async def cmd_endpoints(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /endpoints — paths and doc links"""
        base = "https://docs.trade.mudrex.com/docs"
        lines = ["*Mudrex API — Endpoints*\n_Base: https://trade.mudrex.com_ · Auth: X-Authentication\n"]
        for name, method, path, slug in self._API_ENDPOINTS:
            url = f"{base}/{slug}"
            lines.append(f"• {name} — `{method} {path}` · [doc]({url})")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    
    # ==================== Admin Commands (Teacher Mode) ====================
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        if not config.ADMIN_USER_IDS:
            return False
        return user_id in config.ADMIN_USER_IDS
    
    async def cmd_learn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /learn <text>
        Ingest new knowledge into the vector store immediately.
        """
        user_id = update.effective_user.id
        if not self._is_admin(user_id):
            await update.message.reply_text(f"Admin only. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return

        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("Usage: `/learn The new rate limit is 50 requests per minute.`", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            self.rag_pipeline.learn_text(text)
            # Check if changelog watcher is enabled (warns about daily clearing)
            from ..config import config
            if getattr(config, "ENABLE_CHANGELOG_WATCHER", True):
                await update.message.reply_text(
                    "Got it — I'll remember that.\n\n"
                    "⚠️ Note: Daily job clears learned content. For permanent storage, add to `docs/` directory.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("Got it — I'll remember that.", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error learning text: {e}", exc_info=True)
            await update.message.reply_text(f"Couldn't save that: {e}")

    async def cmd_set_fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /set_fact <key> <value>
        Set a strict fact (Key-Value) that overrides RAG.
        """
        user_id = update.effective_user.id
        if not self._is_admin(user_id):
            await update.message.reply_text(f"Admin only. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return

        if len(context.args) < 2:
            await update.message.reply_text("Usage: `/set_fact LATENCY 200ms`", parse_mode=ParseMode.MARKDOWN)
            return

        key = context.args[0].upper()
        value = " ".join(context.args[1:])
        
        try:
            self.rag_pipeline.set_fact(key, value)
            await update.message.reply_text(f"Set **{key}** = `{value}`", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"Couldn't set that: {e}")

    async def cmd_delete_fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /delete_fact <key>
        Delete a strict fact.
        """
        user_id = update.effective_user.id
        if not self._is_admin(user_id):
            await update.message.reply_text(f"Admin only. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return

        if not context.args:
            await update.message.reply_text("Usage: `/delete_fact LATENCY`", parse_mode=ParseMode.MARKDOWN)
            return

        key = context.args[0].upper()
        
        if self.rag_pipeline.delete_fact(key):
            await update.message.reply_text(f"Deleted **{key}**.", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"Couldn't find **{key}**.", parse_mode=ParseMode.MARKDOWN)

    async def cmd_clearcache(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /clearcache [type]
        Clear cached responses. Types: all, semantic, response
        Useful when bot was returning wrong answers due to bugs.
        """
        user_id = update.effective_user.id
        if not self._is_admin(user_id):
            await update.message.reply_text(f"Admin only. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return

        cache_type = context.args[0].lower() if context.args else "all"
        
        cleared = []
        
        try:
            # Clear semantic cache
            if cache_type in ["all", "semantic"]:
                if self.rag_pipeline.semantic_cache:
                    self.rag_pipeline.semantic_cache.clear()
                    cleared.append("semantic cache")
            
            # Clear response cache (Redis)
            if cache_type in ["all", "response"]:
                if self.rag_pipeline.cache and self.rag_pipeline.cache.connected:
                    # Clear response keys
                    keys = self.rag_pipeline.cache.redis_client.keys("response:*")
                    if keys:
                        self.rag_pipeline.cache.redis_client.delete(*keys)
                    cleared.append("response cache")
            
            if cleared:
                await update.message.reply_text(
                    f"Cleared: {', '.join(cleared)}.\n\nBot will now generate fresh responses.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("No caches to clear.")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            await update.message.reply_text(f"Error clearing cache: {e}")

    # ==================== MCP (AI co-pilot: use whenever needed) ====================
    
    def _resolve_mcp_call(self, message: str) -> Optional[Tuple[str, dict]]:
        """If the message should be answered with MCP, return (tool_name, params). Else None."""
        low = message.lower().strip()
        # list_futures: list/available/show futures or contracts
        if re.search(r'\b(list|show|available|all|what)\s+(futures|contracts?)\b', low):
            return ("list_futures", {})
        if re.search(r'\b(futures|contracts?)\s+(list|available)\b', low):
            return ("list_futures", {})
        # get_future: contract details for a symbol
        sym_map = {"btc": "BTCUSDT", "eth": "ETHUSDT", "xrp": "XRPUSDT", "sol": "SOLUSDT", "bnb": "BNBUSDT", "doge": "DOGEUSDT"}
        m = re.search(r'\b(btc|eth|xrp|sol|bnb|doge|ada|avax|link|dot|matic)\b', low)
        if m:
            base = m.group(1).upper()
            sym = sym_map.get(m.group(1).lower(), base + "USDT")
            if re.search(r'\b(get|detail|info|spec|future|contract)\b', low):
                return ("get_future", {"symbol": sym})
        # Explicit symbol: BTC/USDT or similar
        m = re.search(r'\b([A-Z]{2,6})/?(?:USDT)?\b', message, re.I)
        if m and re.search(r'\b(get|detail|info|spec|future|contract)\b', low):
            s = m.group(1).upper().replace("/", "")
            if not s.endswith("USDT"):
                s = s + "USDT"
            return ("get_future", {"symbol": s})
        return None

    def _format_mcp_for_context(self, result: dict) -> str:
        """Format MCP call result for the LLM context. Truncate if large."""
        if not result.get("success"):
            return ""
        data = result.get("data")
        if not data:
            return ""
        # MCP often returns { "content": [ {"type":"text", "text": "..."} ] }
        if isinstance(data, dict) and "content" in data:
            parts = [c.get("text", "") for c in data["content"] if isinstance(c, dict) and c.get("type") == "text"]
            raw = "\n".join(parts) if parts else str(data)
        elif isinstance(data, str):
            raw = data
        else:
            raw = str(data)
        return (raw[:3200] + "\n... (truncated)") if len(raw) > 3200 else raw

    # ==================== Message Handler ====================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming messages in groups - REACTIVE ONLY
        
        Responds ONLY when explicitly engaged:
        1. Bot is @mentioned directly
        2. Reply to bot's message (conversation continuation)
        3. Quote + mention (someone quotes another user's message AND tags bot)
        
        Does NOT auto-detect keywords or respond proactively.
        """
        if not update.message or not update.message.text:
            return
        
        # Ensure we're in a group
        if update.effective_chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            logger.debug(f"Ignored non-group message from {update.effective_chat.type}")
            return
        
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        message = update.message.text
        
        # Check if bot is @mentioned in this message (direct tag)
        bot_mentioned = self._is_bot_mentioned_direct(update)
        
        # Check if this is a reply to the bot's own message (continuation)
        is_reply_to_bot = (
            update.message.reply_to_message and 
            update.message.reply_to_message.from_user and 
            update.message.reply_to_message.from_user.is_bot and
            self.app.bot and
            update.message.reply_to_message.from_user.id == self.app.bot.id
        )
        
        # Quote + mention: User replies to ANOTHER user's message AND tags the bot
        # This is how admins/peers can ask the bot to help with someone else's question
        is_quote_with_mention = (
            update.message.reply_to_message and
            update.message.reply_to_message.from_user and
            not update.message.reply_to_message.from_user.is_bot and
            bot_mentioned
        )
        
        # REACTIVE ONLY: Respond ONLY when explicitly engaged
        # 1. Bot is @mentioned
        # 2. Reply to bot's message (continuation)
        # 3. Quote + mention (someone quotes another user and tags bot)
        if not bot_mentioned and not is_reply_to_bot:
            logger.debug(f"Not engaged, ignoring message from {user_name}")
            return
        
        # Strip bot @mention from the message for processing
        cleaned_message = message
        if self.app.bot and self.app.bot.username:
            try:
                pattern = re.compile(rf"@{re.escape(self.app.bot.username)}\b", re.IGNORECASE)
                cleaned_message = pattern.sub("", message).strip()
            except re.error:
                cleaned_message = message.strip()
        else:
            cleaned_message = message.strip()
        
        # For quote+mention: use the quoted message
        if is_quote_with_mention and update.message.reply_to_message.text:
            quoted_text = update.message.reply_to_message.text
            # If user just tagged bot without adding their own question, use the quoted message
            if not cleaned_message or cleaned_message.lower() in ['help', 'please', 'can you help', '?']:
                cleaned_message = quoted_text
            else:
                # Prepend quoted context so the bot knows what they're asking about
                cleaned_message = f"[Quoted message: {quoted_text}]\n\nUser's question: {cleaned_message}"
        
        # Handle empty message after stripping mention (just a tag with no content)
        if not cleaned_message:
            await update.message.reply_text(
                "Hey! What's up? Ask me about the API, code, or errors."
            )
            return
        
        # Lightweight handling for pure greetings when tagged (no RAG, no script)
        lower_clean = cleaned_message.lower()
        if re.fullmatch(r"(hi|hello|hey|yo|gm|gn|sup|what'?s up|how are you|how'?re you)[\s!,.?]*", lower_clean):
            await update.message.reply_text("Hey! What's up? Ask me about the API, code, or errors.")
            return
        
        # Access control (if configured)
        if config.ALLOWED_CHAT_IDS and chat_id not in config.ALLOWED_CHAT_IDS:
            logger.warning(f"Unauthorized group: {chat_id}")
            return
        
        # Rate limiting (per user + per group + global)
        if not self.rate_limiter.is_allowed(chat_id, user_id):
            remaining = self.rate_limiter.get_remaining(chat_id, user_id)
            if remaining.get("user", 1) == 0:
                await update.message.reply_text(
                    "You're sending too many messages. Wait a minute before trying again."
                )
            else:
                await update.message.reply_text(
                    "Too many messages in this group. Give it a minute and try again."
                )
            return

        # If user pasted their API secret, return deterministic connection snippet + warning
        shared_secret = _extract_shared_api_secret(cleaned_message)
        if shared_secret:
            snippet = (
                "To connect, use the X-Authentication header with your API secret. "
                "Here is a snippet to verify your connection by fetching account details.\n\n"
                "```python\n"
                "import requests\n\n"
                'BASE_URL = "https://trade.mudrex.com/fapi/v1"\n'
                "headers = {\n"
                f' "X-Authentication": "{shared_secret}"\n'
                "}\n\n"
                'response = requests.get(f"{BASE_URL}/account", headers=headers)\n'
                "print(response.json())\n"
                "```"
            )
            answer = f"{snippet}\n\n{API_KEY_EXPOSED_WARNING}"
            await self._send_response(update, answer)
            return
        
        logger.info(f"[REACTIVE] {user_name} in {chat_id}: {message[:50]}... | reply_to_bot={is_reply_to_bot} | mentioned={bot_mentioned} | quote={is_quote_with_mention}")
        
        # API down / connectivity: one reply "Let me check.", then typing, then ping result + script + footer
        if self.rag_pipeline.is_connectivity_question(cleaned_message):
            await update.message.reply_text("Let me check.")
            await update.message.chat.send_action(ChatAction.TYPING)
            await asyncio.sleep(1.5)  # brief "checking" feel
            second_message = self.rag_pipeline.run_connectivity_check()
            await self._send_response(update, second_message)
            return
        
        await update.message.chat.send_action(ChatAction.TYPING)
        
        try:
            history_key = f"history_{chat_id}"
            chat_history = context.chat_data.get(history_key, [])
            
            # AI co-pilot: live data via REST (GET /fapi/v1/futures) or MCP
            mcp_context = None
            mcp_info = self._resolve_mcp_call(cleaned_message)
            # list_futures: REST (preferred) or MCP, reply with count and GET /fapi/v1/futures doc
            if mcp_info and mcp_info[0] == "list_futures" and (config.MUDREX_API_SECRET or (self.mcp_client and self.mcp_client.is_authenticated())):
                symbols = await fetch_all_futures_symbols_via_rest(config.MUDREX_API_SECRET) if config.MUDREX_API_SECRET else await fetch_all_futures_symbols(self.mcp_client)
                n = len(symbols)
                doc_url = "https://docs.trade.mudrex.com/docs/get-asset-listing"
                await update.message.reply_text(
                    f"There are **{n}** futures pairs listed. To see the full list: GET /fapi/v1/futures — {doc_url}",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            if self.mcp_client and self.mcp_client.is_authenticated() and mcp_info:
                tool_name, params = mcp_info
                res = await self.mcp_client.call_tool(tool_name, params)
                if res.get("success") and res.get("data"):
                    mcp_context = self._format_mcp_for_context(res)
                    logger.info(f"MCP co-pilot: {tool_name} -> {len(mcp_context or '')} chars")
            
            # Use context manager if available, otherwise fallback to old method
            try:
                if self.rag_pipeline.context_manager:
                    # Use enhanced context management
                    logger.info(f"Using context manager for chat {chat_id}, message: {cleaned_message[:50]}...")
                    result = self.rag_pipeline.query(
                        cleaned_message,
                        chat_history=None,  # Will be loaded by context manager
                        mcp_context=mcp_context,
                        chat_id=str(chat_id)
                    )
                    logger.info(f"Query completed successfully, answer length: {len(result.get('answer', ''))}")
                    
                    # Save conversation to persistent storage
                    try:
                        self.rag_pipeline.context_manager.add_message(str(chat_id), 'user', message)
                        self.rag_pipeline.context_manager.add_message(str(chat_id), 'assistant', result['answer'])
                        
                        # Extract facts from conversation periodically
                        session = self.rag_pipeline.context_manager.load_session(str(chat_id))
                        if len(session) % 5 == 0 and len(session) > 0:
                            recent = session[-5:]
                            self.rag_pipeline.context_manager.extract_facts(str(chat_id), recent)
                    except Exception as ctx_error:
                        logger.warning(f"Context manager error (non-critical): {ctx_error}")
                else:
                    # Fallback to old method
                    result = self.rag_pipeline.query(cleaned_message, chat_history=chat_history, mcp_context=mcp_context)
                    
                    # Update history
                    chat_history.append({'role': 'user', 'content': cleaned_message})
                    chat_history.append({'role': 'assistant', 'content': result['answer']})
                    context.chat_data[history_key] = chat_history[-6:]  # Keep last 6 per group
            except AttributeError as attr_error:
                # Context manager not available, use fallback
                logger.warning(f"Context manager not available, using fallback: {attr_error}")
                result = self.rag_pipeline.query(cleaned_message, chat_history=chat_history, mcp_context=mcp_context)
                
                # Update history
                chat_history.append({'role': 'user', 'content': cleaned_message})
                chat_history.append({'role': 'assistant', 'content': result['answer']})
                context.chat_data[history_key] = chat_history[-6:]  # Keep last 6 per group
            except Exception as query_error:
                # Error in query processing, log and try fallback
                logger.error(f"Error in query processing: {query_error}", exc_info=True)
                logger.info("Attempting fallback without context manager...")
                try:
                    result = self.rag_pipeline.query(cleaned_message, chat_history=chat_history, mcp_context=mcp_context)
                    chat_history.append({'role': 'user', 'content': cleaned_message})
                    chat_history.append({'role': 'assistant', 'content': result['answer']})
                    context.chat_data[history_key] = chat_history[-6:]
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                    raise  # Re-raise to be caught by outer handler
            
            # If user shared their API secret in the message, append exposure warning
            answer = result['answer']
            if _user_shared_api_secret(cleaned_message) and "API key is now exposed" not in answer:
                answer = f"{answer}\n\n{API_KEY_EXPOSED_WARNING}"
            # Send response
            await self._send_response(update, answer)
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg_str = str(e)
            logger.error(f"Error handling message: {error_type}: {error_msg_str}", exc_info=True)
            # Log more details for debugging
            import traceback
            full_traceback = traceback.format_exc()
            logger.error(f"Full traceback:\n{full_traceback}")
            
            # Log specific error types for better debugging
            if "Conflict" in error_type or "conflict" in error_msg_str.lower():
                logger.error("CONFLICT ERROR: Multiple bot instances detected. Stop other instances immediately.")
            elif "Connection" in error_type or "timeout" in error_msg_str.lower():
                logger.error("CONNECTION ERROR: Check Redis, Qdrant, or Gemini API connectivity")
            elif "AttributeError" in error_type:
                logger.error(f"ATTRIBUTE ERROR: {error_msg_str} - Check component initialization")
            elif "KeyError" in error_type:
                logger.error(f"KEY ERROR: {error_msg_str} - Missing configuration or data")
            
            # Report to Station Master
            try:
                await report_error(e, "exception", context={
                    "handler": "handle_message", 
                    "message_preview": message[:100] if message else "no message",
                    "error_type": error_type,
                    "error_message": error_msg_str[:200]
                })
            except Exception:
                pass  # Don't let error reporting break the bot
            
            # Check if we can send a response (update might be None in some error cases)
            try:
                if update and update.message:
                    # More helpful error message based on error type
                    if "Conflict" in error_type:
                        error_msg = "⚠️ Multiple bot instances detected. Please stop other instances and try again."
                    elif "Connection" in error_type or "timeout" in error_msg_str.lower():
                        error_msg = "⚠️ Connection issue. Check Redis/Qdrant/Gemini connectivity. Try again in a moment."
                    elif "ClientError" in error_type and "NOT_FOUND" in error_msg_str:
                        error_msg = "⚠️ An AI model used by the bot is unavailable. The team has been notified — please try again shortly."
                    else:
                        error_msg = f"That didn't work — try again? Error: {error_type}. If it keeps failing, might be a temporary issue."
                    await update.message.reply_text(error_msg)
            except Exception as send_error:
                logger.error(f"Could not send error message to user: {send_error}")
    
    def _is_bot_mentioned(self, update: Update) -> bool:
        """
        Check if bot is mentioned/tagged in the message
        Returns True if:
        - Bot is @mentioned
        - Message is a reply to bot's message
        - Bot username is in the message
        """
        if not update.message:
            return False
        
        # Check if replying to bot
        if update.message.reply_to_message:
            if update.message.reply_to_message.from_user and update.message.reply_to_message.from_user.is_bot:
                return True
        
        # Check for @mentions
        if update.message.entities:
            bot_username = self.app.bot.username.lower() if self.app.bot.username else None
            for entity in update.message.entities:
                if entity.type == "mention":
                    # Extract mentioned username
                    mention = update.message.text[entity.offset:entity.offset + entity.length].lower()
                    if bot_username and bot_username in mention:
                        return True
                elif entity.type == "text_mention":
                    # Direct user mention
                    if entity.user and entity.user.is_bot:
                        return True
        
        # Check if bot username appears in text (case-insensitive)
        if self.app.bot.username:
            if f"@{self.app.bot.username.lower()}" in update.message.text.lower():
                return True
        
        return False
    
    def _is_bot_mentioned_direct(self, update: Update) -> bool:
        """
        Check if bot is @mentioned directly in this message.
        Does NOT count replies to bot's messages as mentions.
        
        Returns True ONLY if:
        - Bot is @mentioned in the message text
        - Bot username appears in the message
        """
        if not update.message or not update.message.text:
            return False
        
        # Check for @mentions in entities
        if update.message.entities:
            bot_username = self.app.bot.username.lower() if self.app.bot.username else None
            for entity in update.message.entities:
                if entity.type == "mention":
                    mention = update.message.text[entity.offset:entity.offset + entity.length].lower()
                    if bot_username and bot_username in mention:
                        return True
                elif entity.type == "text_mention":
                    if entity.user and self.app.bot and entity.user.id == self.app.bot.id:
                        return True
        
        # Check if bot username appears in text (case-insensitive)
        if self.app.bot and self.app.bot.username:
            if f"@{self.app.bot.username.lower()}" in update.message.text.lower():
                return True
        
        return False
    
    def _split_message(self, text: str, max_length: int = None) -> List[str]:
        """
        Split long messages into chunks that fit within Telegram's limit.
        Tries to split at paragraph boundaries (double newlines) or sentence boundaries.
        """
        if max_length is None:
            max_length = config.MAX_RESPONSE_LENGTH
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        remaining = text
        
        while len(remaining) > max_length:
            # Try to split at paragraph boundary (double newline)
            para_split = remaining.rfind('\n\n', 0, max_length)
            if para_split > max_length * 0.5:  # Only use if we get at least 50% of max_length
                chunks.append(remaining[:para_split + 2].strip())
                remaining = remaining[para_split + 2:].strip()
                continue
            
            # Try to split at single newline
            newline_split = remaining.rfind('\n', 0, max_length)
            if newline_split > max_length * 0.5:
                chunks.append(remaining[:newline_split + 1].strip())
                remaining = remaining[newline_split + 1:].strip()
                continue
            
            # Try to split at sentence boundary (period + space)
            sentence_split = remaining.rfind('. ', 0, max_length)
            if sentence_split > max_length * 0.5:
                chunks.append(remaining[:sentence_split + 2].strip())
                remaining = remaining[sentence_split + 2:].strip()
                continue
            
            # Last resort: hard split at max_length, but avoid cutting @mentions
            # Try to find a space before max_length to avoid cutting tags
            space_split = remaining.rfind(' ', 0, max_length)
            if space_split > max_length * 0.8:  # Use if we get at least 80% of max_length
                chunks.append(remaining[:space_split].strip())
                remaining = remaining[space_split:].strip()
            else:
                chunks.append(remaining[:max_length].strip())
                remaining = remaining[max_length:].strip()
        
        if remaining:
            chunks.append(remaining)
        
        return chunks
    
    async def _send_response(self, update: Update, response: str):
        """Send response with markdown fallback, splitting long messages"""
        max_length = config.MAX_RESPONSE_LENGTH
        chunks = self._split_message(response, max_length)
        
        for i, chunk in enumerate(chunks):
            try:
                # Add continuation indicator for multi-part messages
                if len(chunks) > 1:
                    if i == 0:
                        chunk = f"{chunk}\n\n_..._"
                    elif i < len(chunks) - 1:
                        chunk = f"_..._\n\n{chunk}\n\n_..._"
                    else:
                        chunk = f"_..._\n\n{chunk}"
                
                await update.message.reply_text(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except Exception:
                # Strip markdown if parsing fails
                plain = chunk.replace('*', '').replace('_', '').replace('`', '')
                # Remove continuation markers if markdown failed
                plain = plain.replace('...', '')
                await update.message.reply_text(plain, disable_web_page_preview=True)
    
    
    def run(self):
        """Start the bot (blocking)"""
        logger.info("Starting MudrexBot (GROUP-ONLY)...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def start_async(self):
        """Start the bot (async)"""
        try:
            await self.app.initialize()
            await self.setup_commands()
            await self.app.start()
            # Reset conflict counter on successful start
            self.conflict_count = 0
            # On Railway: drop pending updates so we don't fight with the previous instance's getUpdates
            drop_pending = os.getenv("RAILWAY_ENVIRONMENT", "").strip() != ""
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=drop_pending,
            )
            logger.info("MudrexBot started (GROUP-ONLY mode)")
        except Conflict as e:
            logger.error("=" * 60)
            logger.error("TELEGRAM BOT CONFLICT ERROR")
            logger.error("=" * 60)
            logger.error("Another bot instance is already running!")
            logger.error("This happens when:")
            logger.error("  1. Multiple deployments are running (local + production)")
            logger.error("  2. Previous instance didn't shut down properly")
            logger.error("  3. Another process is using the same bot token")
            logger.error("")
            logger.error("Solutions:")
            logger.error("  1. Stop all other bot instances")
            logger.error("  2. Wait 60 seconds for Telegram to release the connection")
            logger.error("  3. Check Railway/deployment logs for other running instances")
            logger.error("  4. Use webhook mode instead of polling if needed")
            logger.error("=" * 60)
            await report_error(e, "exception", context={"error_type": "telegram_conflict"})
            raise
        except (TimedOut, NetworkError) as e:
            logger.warning(f"Network error during startup: {e}")
            logger.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)
            # Retry once
            try:
                drop_pending = os.getenv("RAILWAY_ENVIRONMENT", "").strip() != ""
                await self.app.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=drop_pending,
                )
                logger.info("MudrexBot started after retry (GROUP-ONLY mode)")
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                await report_error(retry_error, "exception", context={"error_type": "telegram_startup_retry"})
                raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping MudrexBot...")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
