from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.encryption import encrypt_state, decrypt_state
from utils.lock_manager import LockManager
import asyncio


class StartHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get or create user
        user = self.db.get_or_create_user(user_id)
        
        # Check if user has active account
        active_account = self.db.get_active_account(user_id)
        
        if active_account:
            # User has account, show main menu
            await self.show_main_menu(update, context)
        else:
            # New user or no active account, show welcome
            await self.show_welcome(update, context)
    
    async def show_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message with two buttons"""
        keyboard = [
            [InlineKeyboardButton("ساخت اکانت جدید", callback_data="create_account")],
            [InlineKeyboardButton("بازیابی اکانت قبلی", callback_data="recover_account")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = "به ربات پرس بات خوش آمدید.\n\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:"
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        keyboard = [
            [InlineKeyboardButton("موجودی حساب", callback_data="balance")],
            [InlineKeyboardButton("خرید پرس", callback_data="buy_pers")],
            [InlineKeyboardButton("ارسال پرس", callback_data="send_pers")],
            [InlineKeyboardButton("فروش پرس", callback_data="sell_pers")],
            [InlineKeyboardButton("۱۰ گردش آخر", callback_data="transactions")],
            [InlineKeyboardButton("ارتباط با ما", callback_data="contact")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = "منوی اصلی:\n\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:"
        
        if update.message:
            await update.message.reply_text(menu_text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await query.edit_message_text(lock_message)
            return
        
        callback_data = query.data
        
        if callback_data == "main_menu":
            await self.show_main_menu(update, context)
        elif callback_data in ["create_account", "recover_account"]:
            # These will be handled by account handler
            from handlers.account import AccountHandler
            account_handler = AccountHandler(self.db, self.lock_manager)
            if callback_data == "create_account":
                await account_handler.start_create_account(update, context)
            else:
                await account_handler.start_recover_account(update, context)
        else:
            # Route to appropriate handler
            if callback_data == "balance":
                from handlers.balance import BalanceHandler
                handler = BalanceHandler(self.db, self.lock_manager)
                await handler.show_balance(update, context)
            elif callback_data == "buy_pers":
                from handlers.buy import BuyHandler
                handler = BuyHandler(self.db, self.lock_manager)
                await handler.start_buy(update, context)
            elif callback_data == "send_pers":
                from handlers.send import SendHandler
                handler = SendHandler(self.db, self.lock_manager)
                await handler.start_send(update, context)
            elif callback_data == "sell_pers":
                from handlers.sell import SellHandler
                handler = SellHandler(self.db, self.lock_manager)
                await handler.start_sell(update, context)
            elif callback_data == "transactions":
                from handlers.transactions import TransactionsHandler
                handler = TransactionsHandler(self.db, self.lock_manager)
                await handler.start_transactions(update, context)
            elif callback_data == "contact":
                from handlers.contact import ContactHandler
                handler = ContactHandler(self.db, self.lock_manager)
                await handler.start_contact(update, context)

