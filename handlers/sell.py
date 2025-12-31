from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.validators import validate_amount, validate_sheba, validate_bank_account_number, validate_card_number, validate_password
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
        max_sell = balance + (balance * config.SELL_FEE_PERCENT)
        
        amount_text = f"لطفا مقدار مورد نظر را وارد کنید (به PERS):\n\n"
        amount_text += f"موجودی شما: {balance:,.2f} PERS\n"
        amount_text += f"حداکثر مقدار فروش: {max_sell:,.2f} PERS"
        
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
        max_sell = balance + (amount * config.SELL_FEE_PERCENT)
        
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
        
        sheba_text = "لطفا شماره شبا (IBAN) خود را وارد کنید:\n\n"
        sheba_text += "فرمت: IR + 24 رقم"
        
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
        
        # Save Sheba and request account number
        state['sheba'] = sheba
        state['step'] = 'enter_account_number'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        account_text = "لطفا شماره حساب بانکی خود را وارد کنید:"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, account_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_account_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bank account number input"""
        user_id = str(update.effective_user.id)
        account_number = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'sell_pers' or state.get('step') != 'enter_account_number':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate account number
        is_valid, error_message = validate_bank_account_number(account_number)
        
        if not is_valid:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\nلطفا دوباره تلاش کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save account number and request card number
        state['bank_account_number'] = account_number
        state['step'] = 'enter_card_number'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        card_text = "لطفا شماره کارت بانکی خود را وارد کنید:"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, card_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_card_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle card number input"""
        user_id = str(update.effective_user.id)
        card_number = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'sell_pers' or state.get('step') != 'enter_card_number':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate card number
        is_valid, error_message = validate_card_number(card_number)
        
        if not is_valid:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\nلطفا دوباره تلاش کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save card number and show confirmation
        state['card_number'] = card_number
        state['step'] = 'confirm'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Calculate amount in Toman
        amount = state.get('amount', 0)
        amount_toman = amount * config.PERS_TO_TOMAN
        
        confirm_text = f"حداکثر ۴۸ ساعت مبلغ {amount_toman:,.0f} تومان ({amount:,.2f} PERS) برای شما واریز می‌شود.\n\n"
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
        
        password_text = "لطفا رمز عبور خود را وارد کنید:"
        
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
        
        # Deduct from balance
        self.db.update_account_balance(account.account_number, -amount)
        
        # Create transaction record
        self.db.create_transaction(
            from_account=account.account_number,
            to_account=None,
            amount=amount,
            fee=0.0,
            transaction_type='sell'
        )
        
        # Calculate amount in Toman
        amount_toman = amount * config.PERS_TO_TOMAN
        
        # Send to admin
        admin_text = f"درخواست فروش PERS:\n\n"
        admin_text += f"User ID: {user_id}\n"
        admin_text += f"شماره حساب: {account.account_number}\n"
        admin_text += f"مبلغ: {amount:,.2f} PERS ({amount_toman:,.0f} تومان)\n"
        admin_text += f"شبا: {state.get('sheba')}\n"
        admin_text += f"شماره حساب بانکی: {state.get('bank_account_number')}\n"
        admin_text += f"شماره کارت: {state.get('card_number')}"
        
        try:
            await context.bot.send_message(chat_id=config.ADMIN_USER_ID, text=admin_text)
        except:
            pass  # Admin might not be set up yet
        
        # Show success message
        success_text = f"✅ ثبت شد!\n\n"
        success_text += f"حداکثر ۴۸ ساعت مبلغ {amount_toman:,.0f} تومان ({amount:,.2f} PERS) برای شما واریز می‌شود."
        
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

