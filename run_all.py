#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified launcher for Telegram bot and web admin panel
"""

import logging
import sys
import os
import threading
import signal
import time
import asyncio
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
bot_thread = None
web_thread = None
bot_application = None
web_app = None
shutdown_event = threading.Event()


def run_bot():
    """Run the Telegram bot"""
    try:
        from bot import BalanceBot
        import config
        
        logger.info("="*60)
        logger.info("Starting Telegram bot...")
        logger.info("="*60)
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            logger.error(".env file not found!")
            print("\n" + "="*60)
            print("[ERROR] .env file not found!")
            print("="*60)
            print("\nPlease create a .env file:")
            print("1. Copy .env.example to .env: copy .env.example .env")
            print("2. Edit .env and add BOT_TOKEN from @BotFather")
            print("3. Configure DATABASE_URL for PostgreSQL connection")
            print("\n" + "="*60)
            return
        
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN is not set in environment variables!")
            print("\n" + "="*60)
            print("[ERROR] BOT_TOKEN is not set!")
            print("="*60)
            print("\nPlease add BOT_TOKEN to your .env file.")
            print("Get your bot token from @BotFather on Telegram")
            print("\n" + "="*60)
            return
        
        logger.info("Initializing bot...")
        bot = BalanceBot()
        
        # Create application
        from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
        from telegram import Update
        
        global bot_application
        bot_application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Add handlers
        bot_application.add_handler(CommandHandler("start", bot.handle_start))
        bot_application.add_handler(CallbackQueryHandler(bot.handle_callback))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
        
        logger.info("Bot is running...")
        print("Welcome to BalanceBot.")
        print("Bot is running...")
        
        # Create and set event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run polling
        bot_application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        print(f"\n[ERROR] Error starting bot: {str(e)}")
        print("\nPlease check the following:")
        print("1. .env file exists and BOT_TOKEN is set")
        print("2. PostgreSQL is installed and running")
        print("3. Database 'balancebot' exists")
        print("4. All dependencies are installed: pip install -r requirements.txt")


def run_web():
    """Run the Flask web application"""
    try:
        # Import web app
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from web.app import app
        
        global web_app
        web_app = app
        
        logger.info("="*60)
        logger.info("Starting web admin panel...")
        logger.info("="*60)
        print("\n" + "="*60)
        print("Starting web admin panel...")
        print("="*60)
        print("\nAccess panel at:")
        print("  http://localhost:5000")
        print("\nLogin:")
        print("  Username: admin")
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        print(f"  Password: {admin_password}")
        print("  (from ADMIN_PASSWORD in .env)")
        print("\n" + "="*60 + "\n")
        
        # Run Flask app (disable reloader in threaded mode)
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        logger.info("Web panel stopped by user")
    except Exception as e:
        logger.error(f"Error starting web panel: {e}", exc_info=True)
        print(f"\n[ERROR] Error starting web panel: {str(e)}")


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("\nReceived shutdown signal...")
    print("\n" + "="*60)
    print("Stopping application...")
    print("="*60)
    
    # Stop bot
    if bot_application:
        try:
            logger.info("Stopping bot...")
            bot_application.stop()
            bot_application.shutdown()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    # Stop web (Flask will stop when main thread exits)
    logger.info("Stopping web panel...")
    
    # Set shutdown event
    shutdown_event.set()
    
    # Wait a bit for threads to finish
    time.sleep(1)
    
    logger.info("Application stopped.")
    print("\nApplication stopped successfully.")
    sys.exit(0)


def main():
    """Main function to start both bot and web"""
    print("\n" + "="*60)
    print("  BalanceBot - Launching Bot and Web Admin Panel")
    print("="*60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot in a separate thread
    global bot_thread
    bot_thread = threading.Thread(target=run_bot, name="BotThread", daemon=True)
    bot_thread.start()
    logger.info("Bot thread started")
    
    # Wait a bit to ensure bot starts
    time.sleep(2)
    
    # Start web in a separate thread
    global web_thread
    web_thread = threading.Thread(target=run_web, name="WebThread", daemon=True)
    web_thread.start()
    logger.info("Web thread started")
    
    print("\n" + "="*60)
    print("Both services are running!")
    print("="*60)
    print("\nPress Ctrl+C to stop.")
    print()
    
    # Keep main thread alive
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
            # Check if threads are alive
            if bot_thread and not bot_thread.is_alive():
                logger.warning("Bot thread stopped!")
            if web_thread and not web_thread.is_alive():
                logger.warning("Web thread stopped!")
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    main()
