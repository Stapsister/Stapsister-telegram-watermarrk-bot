import os
import logging
from telegram.ext import Application
from simple_bot import SimpleBotHandler
from database import init_db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7862951291:AAFLCXBgekpq_do1yl63TIFvgtCADjCr66k")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Initialize bot handler
    bot_handler = SimpleBotHandler()
    
    # Add handlers
    bot_handler.setup_handlers(application)
    
    # Run the bot
    print("Starting Telegram Watermark Bot...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
