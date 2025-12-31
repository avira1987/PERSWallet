from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.generators import format_account_number, generate_payment_link, generate_qr_code
from utils.message_manager import delete_previous_messages, send_and_save_message, edit_and_save_message
import config


class BalanceHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show account balance"""
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            if update.callback_query:
                await update.callback_query.edit_message_text(lock_message)
            return
        
        # Get active account
        account = self.db.get_active_account(user_id)
        if not account:
            error_text = "شما هیچ اکانت فعالی ندارید. لطفا ابتدا اکانت بسازید."
            keyboard = [[InlineKeyboardButton("ساخت اکانت", callback_data="create_account")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(error_text, reply_markup=reply_markup)
            return
        
        # Show balance
        balance_text = f"موجودی حساب شما:\n\n"
        balance_text += f"💰 {float(account.balance):,.2f} PERS\n\n"
        balance_text += f"شماره اکانت:\n{format_account_number(account.account_number)}"
        
        keyboard = [
            [InlineKeyboardButton("ساخت لینک پرداخت", callback_data="create_payment_link")],
            [InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def start_create_payment_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start payment link creation"""
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            if update.callback_query:
                await update.callback_query.edit_message_text(lock_message)
            return
        
        # Get active account
        account = self.db.get_active_account(user_id)
        if not account:
            error_text = "شما هیچ اکانت فعالی ندارید."
            if update.callback_query:
                await update.callback_query.edit_message_text(error_text)
            return
        
        # Save state
        from utils.encryption import encrypt_state
        state = {
            'action': 'create_payment_link',
            'step': 'enter_amount'
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request amount
        amount_text = "لطفا میزان مبلغ مورد نظر خود را وارد کنید (به PERS):\n\n"
        amount_text += "این لینک برای دریافت پرداخت استفاده می‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, amount_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, amount_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_payment_link_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle amount input for payment link"""
        user_id = str(update.effective_user.id)
        amount_str = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        from utils.encryption import decrypt_state, encrypt_state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'create_payment_link' or state.get('step') != 'enter_amount':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate amount
        from utils.validators import validate_amount
        is_valid, error_message, amount = validate_amount(amount_str, min_value=0.01)
        
        if not is_valid:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\nلطفا دوباره تلاش کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Generate payment link
        bot_username = context.bot.username
        payment_link = generate_payment_link(bot_username, amount)
        
        # Generate QR code
        qr_code = generate_qr_code(payment_link)
        
        # Show payment link
        link_text = f"لینک پرداخت شما:\n\n"
        link_text += f"{payment_link}\n\n"
        link_text += f"مبلغ: {amount:,.2f} PERS\n\n"
        link_text += "اگر کسی روی این لینک کلیک کند:\n"
        link_text += "- اگر اکانت داشته باشد، وارد مرحله ارسال PERS می‌شود\n"
        link_text += "- اگر اکانت نداشته باشد، پیامی نمایش داده می‌شود که باید اکانت بسازد"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send QR code
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=qr_code,
            caption=link_text,
            reply_markup=reply_markup
        )
        
        # Clear state
        self.db.update_user_state(user_id, "")

