from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.validators import validate_amount, validate_password, normalize_persian_digits
from utils.encryption import encrypt_state, decrypt_state
from utils.message_manager import delete_previous_messages, send_and_save_message, edit_and_save_message
import config


class BuyHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def start_buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start buy PERS process - first ask for password"""
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
            'action': 'buy_pers',
            'step': 'enter_password'
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request password
        password_text = "🛒 خرید PERS\n\n"
        password_text += "برای خرید PERS، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
        password_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, password_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle amount input after password verification"""
        await self.handle_amount_input_after_password(update, context)
    
    async def handle_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input - after password verification, request amount"""
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
        
        if state.get('action') != 'buy_pers' or state.get('step') != 'enter_password':
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
        
        # Password correct, delete previous messages and check if amount is already set (from payment link)
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        amount = state.get('amount', 0)
        from_payment_link = state.get('from_payment_link', False)
        
        if from_payment_link and amount > 0:
            # Coming from payment link, directly charge account
            # Update balance immediately
            self.db.update_account_balance(account.account_number, amount)
            
            # Create transaction record
            transaction = self.db.create_transaction(
                from_account=None,
                to_account=account.account_number,
                amount=amount,
                fee=0.0,
                transaction_type='buy'
            )
            
            # Create comprehensive transaction log
            username = update.effective_user.username if update.effective_user else None
            self.db.create_transaction_log(
                user_id=user_id,
                username=username,
                transaction_type='buy',
                from_account=None,
                to_account=account.account_number,
                amount=amount,
                fee=0.0,
                sheba=None,
                status='success',
                transaction_id=transaction.id
            )
            
            # Show success message
            new_balance = float(self.db.get_account_balance(account.account_number))
            success_text = "✅ پرداخت با موفقیت انجام شد!\n\n"
            success_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            success_text += f"💰 مبلغ اضافه شده: {amount:,.2f} PERS\n"
            success_text += f"💼 موجودی جدید: {new_balance:,.2f} PERS\n\n"
            success_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            success_text += "🎉 از خرید شما متشکریم!"
            
            keyboard = [
                [InlineKeyboardButton("موجودی حساب", callback_data="balance")],
                [InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]
            ]
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
        else:
            # Normal buy flow, request amount
            state['step'] = 'enter_amount'
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            
            balance = float(account.balance)
            amount_text = "🛒 خرید PERS\n\n"
            amount_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            amount_text += f"💼 موجودی فعلی: {balance:,.2f} PERS\n\n"
            amount_text += "لطفا مقدار مورد نظر خود را برای خرید وارد کنید (به PERS):\n\n"
            amount_text += "⚠️ توجه: حداقل مبلغ خرید ۱ PERS است."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, amount_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_amount_input_after_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle amount input after password verification"""
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
        
        if state.get('action') != 'buy_pers' or state.get('step') != 'enter_amount':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate amount
        is_valid, error_message, amount = validate_amount(amount_str, min_value=1.0)
        
        if not is_valid:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\nلطفا دوباره تلاش کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Check if only digits
        if not amount_str.isdigit():
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = "مقدار باید فقط شامل اعداد انگلیسی باشد."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Get account
        account = self.db.get_active_account(user_id)
        if not account:
            await update.message.reply_text("اکانت شما یافت نشد.")
            return
        
        # Normal buy flow, show payment link (mock Shaparak)
        payment_text = "لینک پرداخت بانکی (شاپرک):\n\n"
        payment_text += f"https://shaparak.ir/payment/mock?amount={amount * config.PERS_TO_TOMAN}\n\n"
        payment_text += "⚠️ توجه: لطفا فیلترشکن خود را خاموش کنید."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        processing_msg = await send_and_save_message(
            context,
            update.effective_chat.id,
            payment_text,
            self.db,
            user_id,
            reply_markup=reply_markup
        )
        
        # Simulate payment processing (in real implementation, this would be webhook)
        # For now, we'll simulate success after a delay
        import asyncio
        await asyncio.sleep(3)  # Simulate processing time
        
        # Update balance
        self.db.update_account_balance(account.account_number, amount)
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Create transaction record
        transaction = self.db.create_transaction(
            from_account=None,
            to_account=account.account_number,
            amount=amount,
            fee=0.0,
            transaction_type='buy'
        )
        
        # Create comprehensive transaction log
        username = update.effective_user.username if update.effective_user else None
        self.db.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='buy',
            from_account=None,
            to_account=account.account_number,
            amount=amount,
            fee=0.0,
            sheba=None,
            status='success',
            transaction_id=transaction.id
        )
        
        # Show success message
        new_balance = float(self.db.get_account_balance(account.account_number))
        success_text = "✅ پرداخت با موفقیت انجام شد!\n\n"
        success_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        success_text += f"💰 مبلغ اضافه شده: {amount:,.2f} PERS\n"
        success_text += f"💼 موجودی جدید: {new_balance:,.2f} PERS\n\n"
        success_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        success_text += "🎉 از خرید شما متشکریم!"
        
        keyboard = [
            [InlineKeyboardButton("موجودی حساب", callback_data="balance")],
            [InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]
        ]
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

