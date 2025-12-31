from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.encryption import encrypt_state, decrypt_state
from utils.lock_manager import LockManager
from utils.validators import validate_password, validate_account_number
from utils.generators import generate_account_number, format_account_number
from utils.message_manager import delete_previous_messages, send_and_save_message, edit_and_save_message
import config
import asyncio
import json


class AccountHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def start_create_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start account creation process"""
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            if update.callback_query:
                await update.callback_query.edit_message_text(lock_message)
            return
        
        # Generate account number
        account_number = generate_account_number()
        
        # Save state
        state = {
            'action': 'create_account',
            'step': 'show_account_number',
            'account_number': account_number,
            'password_attempts': 0,
            'confirm_attempts': 0
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Show account number
        account_text = f"شماره اکانت شما:\n\n{format_account_number(account_number)}\n\n"
        account_text += "این شماره اکانت شماست و برای واریز به اکانت خودتان و پرداخت در سایت‌ها از آن استفاده می‌شود."
        
        keyboard = [[InlineKeyboardButton("مرحله بعد", callback_data="next_step")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, account_text, self.db, user_id, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await send_and_save_message(context, update.effective_chat.id, account_text, self.db, user_id, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_next_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle next step button in account creation"""
        user_id = str(update.effective_user.id)
        
        # Get state
        encrypted_state = self.db.get_user_state(user_id)
        state = decrypt_state(encrypted_state)
        
        if state.get('step') == 'show_account_number':
            # Delete previous message
            if update.callback_query:
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=False)
            
            # Update state
            state['step'] = 'enter_password'
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            
            # Request password
            password_text = "لطفا یک رمز عددی ۸ رقمی وارد کنید:\n\n"
            password_text += "⚠️ توجه: این رمز در همه مراحل تراکنش از شما خواسته می‌شود.\n"
            password_text += "لطفا آن را در جای امنی ذخیره کنید تا گم نشود.\n"
            password_text += "در صورت گم شدن رمز، دارایی شما از بین می‌رود و ما مسئولیتی در قبال آن نداریم.\n"
            password_text += "باید در حفظ و نگهداری آن کوشا باشید!"
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input during account creation"""
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
        
        if state.get('action') != 'create_account' or state.get('step') != 'enter_password':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate password
        is_valid, error_message = validate_password(password)
        
        if not is_valid:
            state['password_attempts'] = state.get('password_attempts', 0) + 1
            remaining = 3 - state['password_attempts']
            
            if remaining <= 0:
                # Lock user
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن رمز")
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
                lock_text = "تعداد تلاش‌های شما به پایان رسید. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                await send_and_save_message(context, update.effective_chat.id, lock_text, self.db, user_id)
                return
            
            # Delete previous messages
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = error_message + "\n\n"
            error_text += f"⚠️ {remaining} دفعه دیگر مهلت دارید وارد کنید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            
            # Update state
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            return
        
        # Password is valid, delete previous messages and request confirmation
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Save password temporarily in state
        state['password'] = password
        state['step'] = 'confirm_password'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        confirm_text = "رمز شما ثبت شد. لطفا برای تایید، دوباره همان رمز را وارد کنید:"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, confirm_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_password_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password confirmation"""
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
        
        if state.get('action') != 'create_account' or state.get('step') != 'confirm_password':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        original_password = state.get('password', '')
        
        if password != original_password:
            state['confirm_attempts'] = state.get('confirm_attempts', 0) + 1
            remaining = 3 - state['confirm_attempts']
            
            if remaining <= 0:
                # Lock user
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای تایید رمز")
                await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
                lock_text = "تعداد تلاش‌های شما به پایان رسید. اکانت شما به مدت ۱۰ دقیقه قفل شد."
                await send_and_save_message(context, update.effective_chat.id, lock_text, self.db, user_id)
                return
            
            # Delete previous messages
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
            
            error_text = "رمز وارد شده با رمز قبلی مطابقت ندارد.\n\n"
            error_text += f"⚠️ {remaining} دفعه دیگر مهلت دارید وارد کنید."
            
            keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
            
            # Update state
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            return
        
        # Password confirmed, delete previous messages and show commitment
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Create account
        account_number = state['account_number']
        self.db.create_account(user_id, account_number, password)
        
        # Update state
        state['step'] = 'show_commitment'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Show commitment
        commitment_text = config.COMMITMENT_TEXT + "\n\n"
        commitment_text += "لطفا متن تعهدنامه را مطالعه کرده و در صورت موافقت، دکمه زیر را بزنید."
        
        keyboard = [[InlineKeyboardButton("موافقم و قبول می‌کنم", callback_data="accept_commitment")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, commitment_text, self.db, user_id, reply_markup=reply_markup)
        
        # Set timeout to delete message after 5 minutes
        asyncio.create_task(self._timeout_delete_message(context, update.effective_chat.id, update.message.message_id + 1))
    
    async def handle_accept_commitment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle commitment acceptance"""
        user_id = str(update.effective_user.id)
        
        # Delete commitment message
        if update.callback_query:
            await delete_previous_messages(update, context, self.db, user_id, delete_user_message=False)
        
        # Clear state
        self.db.update_user_state(user_id, "")
        
        # Show main menu
        from handlers.start import StartHandler
        start_handler = StartHandler(self.db, self.lock_manager)
        await start_handler.show_main_menu(update, context)
    
    async def start_recover_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start account recovery process"""
        user_id = str(update.effective_user.id)
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            if update.callback_query:
                await update.callback_query.edit_message_text(lock_message)
            return
        
        # Save state
        state = {
            'action': 'recover_account',
            'step': 'enter_account_number',
            'account_attempts': 0,
            'password_attempts': 0
        }
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        # Request account number
        account_text = "لطفا ۱۶ رقم شماره اکانت خود را وارد کنید:"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await edit_and_save_message(update, context, account_text, self.db, user_id, reply_markup=reply_markup)
        else:
            await send_and_save_message(context, update.effective_chat.id, account_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_recover_account_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle account number input during recovery"""
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
        
        if state.get('action') != 'recover_account' or state.get('step') != 'enter_account_number':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        # Validate account number
        is_valid, error_message = validate_account_number(account_number)
        
        if not is_valid:
            state['account_attempts'] = state.get('account_attempts', 0) + 1
            remaining = 3 - state['account_attempts']
            
            if remaining <= 0:
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن شماره حساب")
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
        
        # Check if account exists
        account = self.db.get_account_by_number(account_number)
        if not account:
            state['account_attempts'] = state.get('account_attempts', 0) + 1
            remaining = 3 - state['account_attempts']
            
            if remaining <= 0:
                self.lock_manager.lock_user(user_id, "تعداد تلاش‌های ناموفق برای وارد کردن شماره حساب")
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
        
        # Account exists, delete previous messages and request password
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        state['account_number'] = account_number
        state['step'] = 'enter_password'
        encrypted_state = encrypt_state(state)
        self.db.update_user_state(user_id, encrypted_state)
        
        password_text = "لطفا رمز عبور خود را وارد کنید:"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, password_text, self.db, user_id, reply_markup=reply_markup)
    
    async def handle_recover_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input during recovery"""
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
        
        if state.get('action') != 'recover_account' or state.get('step') != 'enter_password':
            await update.message.reply_text("لطفا از منوی اصلی شروع کنید.")
            return
        
        account_number = state.get('account_number')
        
        # Verify password
        if not self.db.verify_password(account_number, password):
            state['password_attempts'] = state.get('password_attempts', 0) + 1
            remaining = 3 - state['password_attempts']
            
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
        
        # Password correct, activate account and link to current user
        self.db.update_account_user_and_activate(account_number, user_id)
        
        # Delete previous messages
        await delete_previous_messages(update, context, self.db, user_id, delete_user_message=True)
        
        # Clear state
        self.db.update_user_state(user_id, "")
        
        # Show main menu
        success_text = "اکانت شما با موفقیت بازیابی شد!"
        
        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_and_save_message(context, update.effective_chat.id, success_text, self.db, user_id, reply_markup=reply_markup)
    
    async def _timeout_delete_message(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
        """Delete message after timeout"""
        await asyncio.sleep(config.MESSAGE_TIMEOUT_MINUTES * 60)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except:
            pass

