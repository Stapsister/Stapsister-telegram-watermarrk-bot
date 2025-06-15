#!/usr/bin/env python3
"""
Minimal Telegram Watermark Bot - Guaranteed Working Version
No config dependencies, direct environment variable usage only
"""

import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalBot:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text("Hello! Watermark bot is running successfully!")
    
    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Echo any message"""
        await update.message.reply_text(f"Received: {update.message.text}")
    
    def run(self):
        """Run the bot"""
        app = Application.builder().token(self.token).build()
        
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))
        
        logger.info("Bot starting...")
        app.run_polling()

def main():
    """Main entry point"""
    try:
        bot = MinimalBot()
        bot.run()
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()