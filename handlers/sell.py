from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.validators import validate_amount, validate_sheba, validate_password
from utils.encryption import encrypt_state, decrypt_state
from utils.message_manager import delete_previous_messages, send_and_save_message, edit_and_save_message
import config


class SellHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def start_sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start sell PERS process"""
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
        
        # Save state
        state = {
            'action': 'sell_pers',
            'step': 'enter_amount'
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request amount
        balance = float(account.balance)
        # User can sell up to 99% of balance, 1% must remain after deducting amount + commission
        # max_sell * (1 + commission_rate) <= balance * 0.99
        max_sell = (balance * 0.99) / (1 + config.SELL_FEE_PERCENT)
        
        amount_text = "💸 فروش PERS\n\n"
        amount_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        amount_text += f"💼 موجودی فعلی: {balance:,.2f} PERS\n"
        amount_text += f"📊 حداکثر مقدار فروش: {max_sell:,.2f} PERS\n"
        amount_text += f"💡 حداقل موجودی باقیمانده: {balance * 0.01:,.2f} PERS (1%)\n\n"
        amount_text += "لطفا مقدار مورد نظر را برای فروش وارد کنید (به PERS):\n\n"
        amount_text += "⚠️ توجه: پس از فروش، مبلغ به حساب بانکی شما واریز می‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, amount_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, amount_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle amount input"""
        user_id = str(update.effective_user.id)
        amount_str = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'sell_pers' or state.get('step') != 'enter_amount':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate amount
        is_valid, error_message, amount = validate_amount(amount_str, min_value=0.01)
        
        if not is_valid:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\nلطفا دوباره تلاش کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Get account
        account = self.db.get_active_account(user_id)
        if not account:
            await update.message.reply_text("اکانت شما یافت نشد.")
            return
        
        # Check max sell amount
        balance = float(account.balance)
        # User can sell up to 99% of balance, 1% must remain after deducting amount + commission
        # max_sell * (1 + commission_rate) <= balance * 0.99
        max_sell = (balance * 0.99) / (1 + config.SELL_FEE_PERCENT)
        
        if amount > max_sell:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = f"مقدار وارد شده بیش از حد مجاز است.\n\n"
            error_text += f"حداکثر مقدار فروش: {max_sell:,.2f} PERS"
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save amount and request Sheba
        state['amount'] = amount
        state['step'] = 'enter_sheba'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        sheba_text = "🏦 اطلاعات حساب بانکی\n\n"
        sheba_text += "لطفا شماره شبا (IBAN) خود را وارد کنید:\n\n"
        sheba_text += "📝 فرمت: IR + 24 رقم\n\n"
        sheba_text += "مثال: IR123456789012345678901234"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, sheba_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_sheba_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Sheba input"""
        user_id = str(update.effective_user.id)
        sheba = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'sell_pers' or state.get('step') != 'enter_sheba':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate Sheba
        is_valid, error_message = validate_sheba(sheba)
        
        if not is_valid:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\nلطفا دوباره تلاش کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save Sheba and show confirmation
        state['sheba'] = sheba
        state['step'] = 'confirm'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Calculate amount in Toman
        amount = state.get('amount', 0)
        amount_toman = amount * config.PERS_TO_TOMAN
        
        # Get current balance
        account = self.db.get_active_account(user_id)
        balance = float(account.balance) if account else 0
        
        # Calculate commission
        commission = amount * config.SELL_FEE_PERCENT
        # Calculate transfer amount (amount to be transferred to user)
        transfer_amount = amount - commission
        
        confirm_text = "✅ تایید نهایی فروش\n\n"
        confirm_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        confirm_text += f"💰 مقدار فروش: {amount:,.2f} PERS\n"
        confirm_text += f"💸 کارمزد: {commission:,.2f} PERS (یک درصد)\n"
        confirm_text += f"💵 مبلغی واریزی به شما: {transfer_amount:,.2f} PERS (مقدار فروش منهای یک درصد)\n\n"
        confirm_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        confirm_text += "آیا تایید می‌کنید؟"
        
        keyboard = [
            [InlineKeyboardButton("بله، تایید می‌کنم", callback_data="confirm_sell")],
            [InlineKeyboardButton("خیر، انصراف", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, confirm_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_confirm_sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle sell confirmation"""
        user_id = str(update.effective_user.id)
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'sell_pers' or state.get('step') != 'confirm':
            if update.callback_query:
                await update.callback_query.edit_message_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Delete confirmation message
        if update.callback_query:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=False)
        
        # Update state to request password
        state['step'] = 'enter_password'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        password_text = "🔐 تایید هویت\n\n"
        password_text += "لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
        password_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input and process sell"""
        user_id = str(update.effective_user.id)
        password = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'sell_pers' or state.get('step') != 'enter_password':
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
        
        # Password correct, delete previous messages and process sell
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        amount = state.get('amount', 0)
        
        # Calculate commission (1% of amount)
        commission = amount * config.SELL_FEE_PERCENT
        total_deduction = amount + commission
        
        # Final safety check: ensure at least 1% of balance remains after deduction
        balance = float(account.balance)
        # Account for commission: max_sell * (1 + commission_rate) <= balance * 0.99
        max_sell = (balance * 0.99) / (1 + config.SELL_FEE_PERCENT)
        if amount > max_sell:
            error_text = f"مقدار وارد شده بیش از حد مجاز است.\n\n"
            error_text += f"حداکثر مقدار فروش: {max_sell:,.2f} PERS\n"
            error_text += f"حداقل موجودی باقیمانده: {balance * 0.01:,.2f} PERS (1%)"
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Get admin account number for commission
        admin_account_number = self.db.get_admin_account_number()
        if not admin_account_number:
            error_text = "خطا در پردازش: حساب ادمین یافت نشد."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Ensure admin account exists
        admin_account = self.db.get_account_by_number(admin_account_number)
        if not admin_account:
            error_text = "خطا در پردازش: حساب ادمین یافت نشد."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Deduct amount + commission from user's balance
        self.db.update_account_balance(account.account_number, -total_deduction)
        
        # Add commission to admin's account
        self.db.update_account_balance(admin_account_number, commission)
        
        # Create transaction record
        transaction = self.db.create_transaction(
            from_account=account.account_number,
            to_account=None,
            amount=amount,
            fee=commission,
            transaction_type='sell'
        )
        
        # Create comprehensive transaction log with sheba number
        username = update.effective_user.username if update.effective_user else None
        self.db.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='sell',
            from_account=account.account_number,
            to_account=None,
            amount=amount,
            fee=commission,
            sheba=state.get('sheba'),
            status='success',
            transaction_id=transaction.id
        )
        
        # Calculate amount in Toman
        amount_toman = amount * config.PERS_TO_TOMAN
        
        # Create withdrawal request
        withdrawal_request = self.db.create_withdrawal_request(
            user_id=user_id,
            account_number=account.account_number,
            amount_pers=amount,
            amount_toman=amount_toman,
            sheba=state.get('sheba'),
            transaction_id=transaction.id
        )
        
        # Send notification to @PERS_coin_bot_support
        support_text = f"🔔 درخواست واریز ریالی جدید\n\n"
        support_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        support_text += f"👤 User ID: {user_id}\n"
        support_text += f"💼 شماره حساب: {account.account_number}\n"
        support_text += f"💰 مبلغ: {amount:,.2f} PERS ({amount_toman:,.0f} تومان)\n"
        support_text += f"💸 کارمزد: {commission:,.2f} PERS (1%)\n"
        support_text += f"🏦 شبا: {state.get('sheba')}\n"
        support_text += f"🆔 شماره درخواست: #{withdrawal_request.id}\n\n"
        support_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        support_text += f"⏰ زمان ثبت: {withdrawal_request.created_at.strftime('%Y-%m-%d %H:%M:%S') if withdrawal_request.created_at else 'نامشخص'}"
        
        # Send to support channel/group or admin
        support_chat_id = config.SUPPORT_CHAT_ID if config.SUPPORT_CHAT_ID else config.ADMIN_USER_ID
        if support_chat_id:
            try:
                await context.bot.send_message(chat_id=support_chat_id, text=support_text)
            except Exception as e:
                # Log error but don't fail the transaction
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send notification to support: {e}")
        
        # Also send to admin if different from support
        if config.ADMIN_USER_ID and config.ADMIN_USER_ID != support_chat_id:
            try:
                await context.bot.send_message(chat_id=config.ADMIN_USER_ID, text=support_text)
            except:
                pass  # Admin might not be set up yet
        
        # Show success message
        new_balance = float(self.db.get_account_balance(account.account_number))
        success_text = "✅ درخواست فروش با موفقیت ثبت شد!\n\n"
        success_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        success_text += f"💼 موجودی: {new_balance:,.2f} PERS\n"
        success_text += f"💰 مبلغ فروش: {amount:,.2f} PERS\n"
        success_text += f"💸 کارمزد: ۱ درصد مقدار فروش ({commission:,.2f} PERS)\n"
        success_text += f"💵 معادل تومان: {amount_toman:,.0f} تومان\n\n"
        success_text += "⏰ زمان واریز: حداکثر ۴۸ ساعت\n\n"
        success_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        success_text += "🎉 درخواست شما در حال پردازش است. پس از واریز، به شما اطلاع داده می‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(
            context,
            update.effective_chat.id,
            success_text,
            self.db,
            user_id,
            reply_markup=reply_markup
        )
        
        # Clear state
        self.db.update_user_state(user_id, "")

