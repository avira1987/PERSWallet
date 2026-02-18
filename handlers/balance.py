from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.generators import format_account_number, generate_payment_link, generate_qr_code
from utils.message_manager import delete_previous_messages, send_and_save_message, edit_and_save_message
from utils.encryption import decrypt_state, encrypt_state
import config


class BalanceHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show account balance - first ask for password"""
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
        
        # Save state to request password first
        state = {
            'action': 'balance',
            'step': 'enter_password'
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request password
        password_text = "💰 موجودی حساب\n\n"
        password_text += "برای مشاهده موجودی حساب خود، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
        password_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, password_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input for balance"""
        from utils.validators import normalize_persian_digits
        
        user_id = str(update.effective_user.id)
        password = update.message.text.strip()
        
        # Normalize Persian digits to English digits
        password = normalize_persian_digits(password)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'balance' or state.get('step') != 'enter_password':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Get account
        account = self.db.get_active_account(user_id)
        if not account:
            await update.message.reply_text("اکانت شما یافت نشد.")
            return
        
        # Verify password
        if not self.db.verify_password(account.account_number, password):
            state['password_attempts'] = state.get('password_attempts', 0) + 1
            remaining = 3 - state.get('password_attempts', 0)
            
            if remaining <= 0:
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن رمز")
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
                lock_text = "تعداد تلاش‌های شما به پایان رسید. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                await send_and_save_message(context, update.effective_chat.id, lock_text, self.db, user_id)
                return
            
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = "رمز وارد شده اشتباه است.\n\n"
            error_text += f"⚠️ {remaining} دفعه دیگر مهلت دارید وارد کنید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            return
        
        # Password correct, delete previous messages and show balance
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Show balance
        balance = float(account.balance)
        balance_text = "💰 موجودی حساب شما\n\n"
        balance_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        balance_text += f"💵 موجودی: {balance:,.2f} PERS\n\n"
        balance_text += f"🔢 شماره اکانت:\n"
        balance_text += f"{format_account_number(account.account_number)}\n\n"
        balance_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        balance_text += "💡 نکته: می‌توانید با استفاده از دکمه «ساخت لینک پرداخت»، لینک پرداخت برای دریافت PERS از دیگران ایجاد کنید."
        
        keyboard = [
            [InlineKeyboardButton("ساخت لینک پرداخت", callback_data="create_payment_link")],
            [InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, balance_text, self.db, user_id, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear state
        self.db.update_user_state(user_id, "")
    
    async def start_create_payment_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start payment link creation - first ask for password"""
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
        
        # Save state to request password first
        state = {
            'action': 'create_payment_link',
            'step': 'enter_password'
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request password
        password_text = "🔗 ساخت لینک پرداخت\n\n"
        password_text += "برای ساخت لینک پرداخت، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
        password_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, password_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_payment_link_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input for payment link creation"""
        from utils.validators import normalize_persian_digits
        
        user_id = str(update.effective_user.id)
        password = update.message.text.strip()
        
        # Normalize Persian digits to English digits
        password = normalize_persian_digits(password)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'create_payment_link' or state.get('step') != 'enter_password':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Get account
        account = self.db.get_active_account(user_id)
        if not account:
            await update.message.reply_text("اکانت شما یافت نشد.")
            return
        
        # Verify password
        if not self.db.verify_password(account.account_number, password):
            state['password_attempts'] = state.get('password_attempts', 0) + 1
            remaining = 3 - state.get('password_attempts', 0)
            
            if remaining <= 0:
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن رمز")
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
                lock_text = "تعداد تلاش‌های شما به پایان رسید. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                await send_and_save_message(context, update.effective_chat.id, lock_text, self.db, user_id)
                return
            
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = "رمز وارد شده اشتباه است.\n\n"
            error_text += f"⚠️ {remaining} دفعه دیگر مهلت دارید وارد کنید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            return
        
        # Password correct, delete previous messages and request amount
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Update state to request amount
        state['step'] = 'enter_amount'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request amount
        amount_text = "🔗 ساخت لینک پرداخت\n\n"
        amount_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        amount_text += "لطفا میزان مبلغ مورد نظر خود را وارد کنید (به PERS):\n\n"
        amount_text += "💡 این لینک برای دریافت پرداخت از دیگران استفاده می‌شود.\n"
        amount_text += "📤 می‌توانید لینک را برای دیگران ارسال کنید تا به شما PERS پرداخت کنند."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        # Get account to include in payment link
        account = self.db.get_active_account(user_id)
        if not account:
            error_text = "شما هیچ اکانت فعالی ندارید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Generate payment link with destination account (one-time use)
        from utils.generators import generate_payment_token
        bot_username = context.bot.username
        token = generate_payment_token()
        
        # Store payment link in database
        self.db.create_payment_link(token, account.account_number, amount, user_id)
        
        # Generate payment link with token
        payment_link = generate_payment_link(bot_username, amount, account.account_number, 
                                            db_manager=self.db, user_id=user_id, token=token)
        
        # Generate QR code
        qr_code = generate_qr_code(payment_link)
        
        # Prepare QR code caption with payment link and all information
        qr_caption = "✅ لینک پرداخت شما آماده است!\n\n"
        qr_caption += "━━━━━━━━━━━━━━━━━━━━\n\n"
        qr_caption += f"💰 مبلغ: {amount:,.2f} PERS\n\n"
        qr_caption += f"🔗 لینک پرداخت:\n{payment_link}\n\n"
        qr_caption += "━━━━━━━━━━━━━━━━━━━━\n\n"
        qr_caption += "📋 نحوه استفاده:\n"
        qr_caption += "• این لینک را برای دریافت‌کننده ارسال کنید\n"
        qr_caption += "• یا QR Code را اسکن کنید\n"
        qr_caption += "• اگر دریافت‌کننده اکانت داشته باشد، وارد مرحله ارسال می‌شود\n"
        qr_caption += "• اگر اکانت نداشته باشد، باید ابتدا اکانت بسازد\n\n"
        qr_caption += "⚠️ توجه: این لینک فقط یکبار قابل استفاده است."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send QR code with caption containing payment link
        photo_message = await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=qr_code,
            caption=qr_caption,
            reply_markup=reply_markup
        )
        
        # Save message ID in state for later deletion and clear action state
        state = {'last_bot_message_id': photo_message.message_id}
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)

