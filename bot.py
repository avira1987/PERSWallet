import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.encryption import decrypt_state, encrypt_state
from utils.message_manager import send_and_save_message, edit_and_save_message
from handlers.start import StartHandler
from handlers.account import AccountHandler
from handlers.balance import BalanceHandler
from handlers.buy import BuyHandler
from handlers.send import SendHandler
from handlers.sell import SellHandler
from handlers.transactions import TransactionsHandler
from handlers.contact import ContactHandler
import config

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BalanceBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.lock_manager = LockManager(self.db)
        
        # Initialize handlers
        self.start_handler = StartHandler(self.db, self.lock_manager)
        self.account_handler = AccountHandler(self.db, self.lock_manager)
        self.balance_handler = BalanceHandler(self.db, self.lock_manager)
        self.buy_handler = BuyHandler(self.db, self.lock_manager)
        self.send_handler = SendHandler(self.db, self.lock_manager)
        self.sell_handler = SellHandler(self.db, self.lock_manager)
        self.transactions_handler = TransactionsHandler(self.db, self.lock_manager)
        self.contact_handler = ContactHandler(self.db, self.lock_manager)
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await self.start_handler.handle_start(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await query.answer()
            await edit_and_save_message(update, context, lock_message, self.db, user_id)
            return
        
        callback_data = query.data
        
        # Check agreement acceptance (except for agreement-related callbacks)
        if callback_data not in ["accept_agreement", "decline_agreement"]:
            if not self.db.has_accepted_agreement(user_id):
                await query.answer()
                await self.start_handler.show_agreement(update, context)
                return
        
        # Route to appropriate handler (handlers will answer the callback query)
        if callback_data == "accept_agreement":
            await query.answer("موافقت‌نامه پذیرفته شد")
            await self.start_handler.handle_accept_agreement(update, context)
        elif callback_data == "decline_agreement":
            await query.answer("موافقت‌نامه رد شد")
            await self.start_handler.handle_decline_agreement(update, context)
        elif callback_data == "main_menu":
            await self.start_handler.show_main_menu(update, context)
        elif callback_data == "create_account":
            await self.account_handler.start_create_account(update, context)
        elif callback_data == "recover_account":
            await self.account_handler.start_recover_account(update, context)
        elif callback_data == "next_step":
            await self.account_handler.handle_next_step(update, context)
        elif callback_data == "accept_commitment":
            await self.account_handler.handle_accept_commitment(update, context)
        elif callback_data == "balance":
            await self.balance_handler.show_balance(update, context)
        elif callback_data == "create_payment_link":
            await self.balance_handler.start_create_payment_link(update, context)
        elif callback_data == "buy_pers":
            await self.buy_handler.start_buy(update, context)
        elif callback_data == "send_pers":
            await self.send_handler.start_send(update, context)
        elif callback_data == "sell_pers":
            await self.sell_handler.start_sell(update, context)
        elif callback_data == "transactions":
            await self.transactions_handler.start_transactions(update, context)
        elif callback_data == "contact":
            await self.contact_handler.start_contact(update, context)
        elif callback_data == "confirm_sell":
            await self.sell_handler.handle_confirm_sell(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Check agreement acceptance
        if not self.db.has_accepted_agreement(user_id):
            # Handle /start command even without agreement
            if update.message.text and update.message.text.startswith('/start'):
                await self.start_handler.handle_start(update, context)
            else:
                await self.start_handler.show_agreement(update, context)
            return
        
        # Get user state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        action = state.get('action', '')
        step = state.get('step', '')
        
        # Route based on state
        if action == 'create_account':
            if step == 'enter_password':
                await self.account_handler.handle_password_input(update, context)
            elif step == 'confirm_password':
                await self.account_handler.handle_password_confirm(update, context)
        elif action == 'recover_account':
            if step == 'enter_account_number':
                await self.account_handler.handle_recover_account_number(update, context)
            elif step == 'enter_password':
                await self.account_handler.handle_recover_password(update, context)
        elif action == 'create_payment_link':
            if step == 'enter_amount':
                await self.balance_handler.handle_payment_link_amount(update, context)
        elif action == 'buy_pers':
            if step == 'enter_amount':
                await self.buy_handler.handle_amount_input(update, context)
            elif step == 'enter_password':
                await self.buy_handler.handle_password_input(update, context)
        elif action == 'send_pers':
            if step == 'enter_destination':
                await self.send_handler.handle_destination_input(update, context)
            elif step == 'enter_amount':
                await self.send_handler.handle_amount_input(update, context)
            elif step == 'enter_password':
                await self.send_handler.handle_password_input(update, context)
        elif action == 'sell_pers':
            if step == 'enter_amount':
                await self.sell_handler.handle_amount_input(update, context)
            elif step == 'enter_sheba':
                await self.sell_handler.handle_sheba_input(update, context)
            elif step == 'enter_account_number':
                await self.sell_handler.handle_account_number_input(update, context)
            elif step == 'enter_card_number':
                await self.sell_handler.handle_card_number_input(update, context)
            elif step == 'enter_password':
                await self.sell_handler.handle_password_input(update, context)
        elif action == 'transactions':
            if step == 'enter_password':
                await self.transactions_handler.handle_password_input(update, context)
        elif action == 'contact':
            if step == 'enter_password':
                await self.contact_handler.handle_password_input(update, context)
            elif step == 'enter_message':
                await self.contact_handler.handle_message_input(update, context)
        else:
                # Unknown message, show error
                error_text = "لطفا از دکمه‌های منو استفاده کنید."
                
                # Check if user has account
                account = self.db.get_active_account(user_id)
                if account:
                    # Count invalid messages
                    invalid_count = state.get('invalid_message_count', 0) + 1
                    state['invalid_message_count'] = invalid_count
                    encrypted_state = encrypt_state(state)
                    self.db.update_user_state(user_id, encrypted_state)
                    
                    if invalid_count >= 3:
                        self.lock_manager.lock_user(user_id, "ارسال پیام‌های نامربوط بیش از حد")
                        lock_text = "تعداد پیام‌های نامربوط شما بیش از حد مجاز بود. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                        await update.message.reply_text(lock_text)
                    else:
                        remaining = 3 - invalid_count
                        error_text += f"\n\n⚠️ {remaining} دفعه دیگر مهلت دارید."
                        await update.message.reply_text(error_text)
                else:
                    await update.message.reply_text(error_text)
    
    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.handle_start))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start the bot
        logger.info("Bot is starting...")
        print("به ربات پرس بات خوش آمدید.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main function"""
    try:
        # Check if .env file exists
        import os
        if not os.path.exists('.env'):
            logger.error(".env file not found!")
            print("\n" + "="*60)
            print("[ERROR] File .env not found!")
            print("="*60)
            print("\nPlease create a .env file with the following variables:")
            print("1. Copy .env.example to .env: copy .env.example .env")
            print("2. Edit .env and add your BOT_TOKEN from @BotFather")
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
        logger.info("Bot is starting...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n[INFO] Bot stopped by user.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        error_msg = str(e)
        print(f"\n[ERROR] Error starting bot: {error_msg}")
        print("\nPlease check the following:")
        print("1. .env file exists and BOT_TOKEN is set")
        print("2. PostgreSQL is installed and running")
        print("3. Database 'balancebot' exists")
        print("4. All dependencies are installed: pip install -r requirements.txt")
        print("\nFor more details, check the logs above.")


if __name__ == '__main__':
    main()

