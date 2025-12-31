from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.lock_manager import LockManager
from utils.validators import validate_account_number, validate_amount, validate_password
from utils.encryption import encrypt_state, decrypt_state
from utils.message_manager import delete_previous_messages, send_and_save_message, edit_and_save_message
import config
import asyncio
from datetime import datetime, timedelta


class SendHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def start_send(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start send PERS process"""
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
            'action': 'send_pers',
            'step': 'enter_destination',
            'destination_attempts': 0
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request destination account
        dest_text = "لطفا آدرس اکانت مقصد را وارد کنید (۱۶ رقم):\n\n"
        dest_text += "⚠️ توجه: لطفا شماره حساب را با دقت وارد کنید تا دارایی شما از بین نرود."
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, dest_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, dest_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_destination_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle destination account input"""
        user_id = str(update.effective_user.id)
        destination = update.message.text.strip()
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('action') != 'send_pers' or state.get('step') != 'enter_destination':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate account number
        is_valid, error_message = validate_account_number(destination)
        
        if not is_valid:
            state['destination_attempts'] = state.get('destination_attempts', 0) + 1
            remaining = 3 - state['destination_attempts']
            
            if remaining <= 0:
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن شماره حساب مقصد")
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
                lock_text = "تعداد تلاش‌های شما به پایان رسید. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                await send_and_save_message(context, update.effective_chat.id, lock_text, self.db, user_id)
                return
            
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\n"
            error_text += f"⚠️ {remaining} دفعه دیگر مهلت دارید وارد کنید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            return
        
        # Check if destination account exists
        dest_account = self.db.get_account_by_number(destination)
        if not dest_account:
            state['destination_attempts'] = state.get('destination_attempts', 0) + 1
            remaining = 3 - state['destination_attempts']
            
            if remaining <= 0:
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن شماره حساب مقصد")
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
                lock_text = "تعداد تلاش‌های شما به پایان رسید. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                await send_and_save_message(context, update.effective_chat.id, lock_text, self.db, user_id)
                return
            
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = "شماره حساب وارد شده یافت نشد.\n\n"
            error_text += f"⚠️ {remaining} دفعه دیگر مهلت دارید وارد کنید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            return
        
        # Check if destination is not the same as sender
        account = self.db.get_active_account(user_id)
        if destination == account.account_number:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = "شما نمی‌توانید به خودتان پرس ارسال کنید."
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save destination
        state['destination'] = destination
        
        # Check if amount is pre-filled from payment link
        payment_link_amount = state.get('payment_link_amount')
        if payment_link_amount:
            # Use pre-filled amount from payment link
            state['amount'] = payment_link_amount
            # Calculate fee
            fee = min(payment_link_amount * config.TRANSACTION_FEE_PERCENT, config.MAX_TRANSACTION_FEE)
            state['fee'] = fee
            state['step'] = 'enter_password'
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            
            # Request password directly
            password_text = "لطفا رمز عبور خود را وارد کنید:"
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
        else:
            # Request amount normally
            state['step'] = 'enter_amount'
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            
            amount_text = "لطفا مقدار مورد نظر را وارد کنید (به PERS):"
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
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
        
        if state.get('action') != 'send_pers' or state.get('step') != 'enter_amount':
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
        
        # Calculate fee
        fee = min(amount * config.TRANSACTION_FEE_PERCENT, config.MAX_TRANSACTION_FEE)
        total_needed = amount + fee
        
        # Check balance
        balance = float(account.balance)
        if balance < total_needed:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = f"موجودی شما کافی نیست.\n\n"
            error_text += f"موجودی: {balance:,.2f} PERS\n"
            error_text += f"مبلغ مورد نیاز: {total_needed:,.2f} PERS (مبلغ + کارمزد)"
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            return
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save amount and request password
        state['amount'] = amount
        state['fee'] = fee
        state['step'] = 'enter_password'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        password_text = "لطفا رمز عبور خود را وارد کنید:"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input and process transaction"""
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
        
        if state.get('action') != 'send_pers' or state.get('step') != 'enter_password':
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
        
        # Password correct, delete previous messages and process transaction
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        amount = state.get('amount', 0)
        fee = state.get('fee', 0)
        destination = state.get('destination')
        
        # Show processing message
        processing_text = "در حال پردازش تراکنش...\n\nلطفا صبر کنید."
        processing_msg = await send_and_save_message(context, update.effective_chat.id, processing_text, self.db, user_id)
        
        # Process transaction with retry logic
        success = await self._process_transaction_with_retry(
            account.account_number,
            destination,
            amount,
            fee,
            context,
            update.effective_chat.id,
            processing_msg.message_id
        )
        
        if success:
            # Delete processing message
            try:
                await processing_msg.delete()
            except:
                pass
            
            # Show success message
            success_text = f"✅ تراکنش با موفقیت انجام شد!\n\n"
            success_text += f"مبلغ {amount:,.2f} PERS به حساب {destination} ارسال شد.\n"
            success_text += f"کارمزد: {fee:,.2f} PERS"
            
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
        else:
            # Delete processing message
            try:
                await processing_msg.delete()
            except:
                pass
            
            # Show error message
            error_text = "❌ خطا در پردازش تراکنش.\n\n"
            error_text += "لطفا دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(
                context,
                update.effective_chat.id,
                error_text,
                self.db,
                user_id,
                reply_markup=reply_markup
            )
        
        # Clear state
        self.db.update_user_state(user_id, "")
    
    async def _process_transaction_with_retry(self, from_account: str, to_account: str, 
                                            amount: float, fee: float, context: ContextTypes.DEFAULT_TYPE,
                                            chat_id: int, processing_msg_id: int) -> bool:
        """Process transaction with retry logic and verify 3 accounts"""
        start_time = datetime.utcnow()
        timeout = timedelta(seconds=config.TRANSACTION_RETRY_TIMEOUT_SECONDS)
        
        # Get admin account (assuming admin has account with number starting with '0000000000000000' or similar)
        # For now, we'll use a special account number for admin
        admin_account_number = "0000000000000001"  # Admin account
        
        # Ensure admin account exists
        admin_account = self.db.get_account_by_number(admin_account_number)
        if not admin_account:
            # Create admin account if it doesn't exist
            # Use a default password for admin account (should be changed in production)
            try:
                admin_account = self.db.create_account("admin", admin_account_number, "00000000")
            except:
                # Account might already exist, try to get it again
                admin_account = self.db.get_account_by_number(admin_account_number)
        
        while datetime.utcnow() - start_time < timeout:
            # Get current balances
            from_balance_before = self.db.get_account_balance(from_account)
            to_balance_before = self.db.get_account_balance(to_account)
            admin_balance_before = self.db.get_account_balance(admin_account_number)
            
            # Perform transaction
            self.db.update_account_balance(from_account, -(amount + fee))
            self.db.update_account_balance(to_account, amount)
            self.db.update_account_balance(admin_account_number, fee)
            
            # Create transaction record
            transaction = self.db.create_transaction(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                fee=fee,
                transaction_type='send'
            )
            
            # Verify balances
            from_balance_after = self.db.get_account_balance(from_account)
            to_balance_after = self.db.get_account_balance(to_account)
            admin_balance_after = self.db.get_account_balance(admin_account_number)
            
            # Expected balances
            expected_from = from_balance_before - amount - fee
            expected_to = to_balance_before + amount
            expected_admin = admin_balance_before + fee
            
            # Check if balances match
            if (abs(from_balance_after - expected_from) < 0.01 and
                abs(to_balance_after - expected_to) < 0.01 and
                abs(admin_balance_after - expected_admin) < 0.01):
                # Transaction successful
                self.db.update_transaction_status(transaction.id, 'success')
                return True
            else:
                # Rollback
                self.db.update_account_balance(from_account, amount + fee)
                self.db.update_account_balance(to_account, -amount)
                self.db.update_account_balance(admin_account_number, -fee)
                self.db.update_transaction_status(transaction.id, 'failed')
                
                # Wait a bit before retry
                await asyncio.sleep(0.5)
        
        # Timeout reached
        return False

