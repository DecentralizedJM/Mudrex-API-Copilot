"""
Telegram Bot handlers and logic

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License - See LICENSE file for details.
"""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from ..config import config
from ..rag import RAGPipeline

logger = logging.getLogger(__name__)


class MudrexBot:
    """Telegram bot for Mudrex API documentation"""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Initialize the bot
        
        Args:
            rag_pipeline: RAG pipeline instance
        """
        self.rag_pipeline = rag_pipeline
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Mudrex bot initialized")
    
    def _register_handlers(self):
        """Register command and message handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        
        # Message handler for questions
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        logger.info("Handlers registered")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
👋 Hey! I'm your Mudrex API coding assistant - part of the team that built this API!

*What I do:*
🔧 Review & fix your code
💡 Answer API questions
📝 Provide working code examples
🐛 Debug errors with you
⚡ Suggest best practices

*How to use me:*
• Ask API questions directly
• Share code - I'll review and improve it
• Tag me with @Mudrex_API_bot anytime
• I silently ignore casual chat

Let's build something awesome! 🚀
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
*Commands:*
/start - Welcome & intro
/help - This message
/stats - Bot info

*What I help with:*
🔧 Code review & corrections
💡 API integration questions
📝 Working code examples
🐛 Error debugging
⚡ Best practices & tips

*Example requests:*
• "How do I create an order?"
• "Fix this code: ```python...```"
• "What's wrong with my authentication?"
• "Show me async order placement"

*Pro tips:*
• Share your code - I'll review it
• Ask specific questions for better answers
• Mention me with @ in groups
• I skip non-API chat automatically

Let's code! 🚀
"""
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats = self.rag_pipeline.get_stats()
        
        stats_message = f"""
*Bot Stats* 📊

🤖 AI Model: {stats['model']}
📚 Docs Loaded: {stats['total_documents']} chunks
💡 Capabilities: Code review, debugging, examples
⚡ Status: Online & ready!

Built by the Mudrex API team 🚀
"""
        await update.message.reply_text(stats_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        if not update.message or not update.message.text:
            return
        
        # Check if chat is allowed (if restrictions are enabled)
        if config.ALLOWED_CHAT_IDS:
            if update.effective_chat.id not in config.ALLOWED_CHAT_IDS:
                logger.warning(f"Unauthorized chat: {update.effective_chat.id}")
                return
        
        user_message = update.message.text
        user_name = update.effective_user.first_name
        
        # Check if bot is mentioned (@username or reply)
        bot_mentioned = False
        if update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
            bot_mentioned = True
        elif update.message.entities:
            for entity in update.message.entities:
                if entity.type == "mention" or entity.type == "text_mention":
                    bot_mentioned = True
                    break
        
        logger.info(f"Message from {user_name}: {user_message[:50]}, mentioned={bot_mentioned}")
        
        # Check if message is API-related (only if not mentioned)
        if not bot_mentioned:
            is_api_related = self.rag_pipeline.gemini_client.is_api_related_query(user_message)
            if not is_api_related:
                logger.info(f"Silently ignoring non-API message: {user_message[:50]}")
                return  # Silently ignore non-API messages
        
        # If mentioned with a greeting, respond warmly and invite engagement
        if bot_mentioned:
            lower_msg = user_message.lower().strip()
            # Check for simple greetings
            if lower_msg in ['hi', 'hello', 'hey', 'sup', 'yo', 'ok', 'okay', 'cool', 'thanks', 'thank you']:
                # Don't block - let it go through to Gemini for a friendly response
                pass  # Continue to RAG pipeline
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Get chat history (last few messages from context)
            chat_history = context.user_data.get('history', [])
            
            # Query the RAG pipeline
            result = self.rag_pipeline.query(
                user_message,
                chat_history=chat_history
            )
            
            # Update chat history
            chat_history.append({'role': 'user', 'content': user_message})
            chat_history.append({'role': 'assistant', 'content': result['answer']})
            
            # Keep only last 6 messages (3 exchanges)
            context.user_data['history'] = chat_history[-6:]
            
            # Send response (NO sources - we're confident!)
            response = result['answer']
            
            # Try to send with Markdown, fallback to plain text if it fails
            try:
                await update.message.reply_text(
                    response,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as parse_error:
                logger.warning(f"Markdown parse error, sending as plain text: {parse_error}")
                # Remove markdown formatting and send as plain text
                plain_response = response.replace('*', '').replace('_', '').replace('`', '')
                await update.message.reply_text(
                    plain_response,
                    disable_web_page_preview=True
                )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "Hmm, ran into an issue there. Mind rephrasing your question?"
            )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Mudrex API bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        await self.app.stop()
