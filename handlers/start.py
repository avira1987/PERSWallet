from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.encryption import encrypt_state, decrypt_state
from utils.lock_manager import LockManager
import asyncio
import os
import logging


class StartHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username  # Get username from Telegram
        
        # Check if user is locked
        is_locked, lock_message = self.lock_manager.check_lock(user_id)
        if is_locked:
            await update.message.reply_text(lock_message)
            return
        
        # Get or create user (and update username if available)
        user = self.db.get_or_create_user(user_id, username)
        
        # Check for payment link parameter (deep link)
        # Format: /start pay_{destination_account}_{amount}
        # Log for debugging
        logger = logging.getLogger(__name__)
        if context.args:
            logger.info(f"Deep link args received: {context.args}")
        
        if context.args and len(context.args) > 0 and context.args[0].startswith('pay_'):
            # This is a payment link click
            try:
                # Parse payment link: pay_{destination_account}_{amount}
                link_parts = context.args[0].replace('pay_', '').split('_')
                if len(link_parts) == 2:
                    destination_account = link_parts[0]
                    amount = float(link_parts[1])
                else:
                    # Old format support: pay_{amount} (backward compatibility)
                    amount = float(context.args[0].replace('pay_', ''))
                    destination_account = None
                
                # Check if user has accepted agreement
                if not self.db.has_accepted_agreement(user_id):
                    # Store payment link info in state for later use after agreement
                    from utils.encryption import encrypt_state
                    state = {
                        'pending_payment_link': True,
                        'payment_link_amount': amount,
                        'payment_link_destination': destination_account
                    }
                    encrypted_state = encrypt_state(state)
                    self.db.update_user_state(user_id, encrypted_state)
                    # Show agreement first
                    await self.show_agreement(update, context)
                    return
                
                # Check if user has account
                account = self.db.get_active_account(user_id)
                if not account:
                    # User doesn't have account
                    from utils.message_manager import send_and_save_message
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    
                    error_text = "⚠️ برای استفاده از این لینک پرداخت\n\n"
                    error_text += "شما باید ابتدا یک اکانت در ربات بسازید.\n\n"
                    error_text += "💡 پس از ساخت اکانت، می‌توانید از لینک پرداخت استفاده کنید."
                    keyboard = [[InlineKeyboardButton("ساخت اکانت", callback_data="create_account")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                    return
                
                # Check if destination account exists
                if destination_account:
                    dest_account = self.db.get_account_by_number(destination_account)
                    if not dest_account:
                        from utils.message_manager import send_and_save_message
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        
                        error_text = "❌ خطا در لینک پرداخت\n\n"
                        error_text += "شماره حساب مقصد در لینک پرداخت معتبر نیست."
                        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                        return
                    
                    # Check if user is trying to send to themselves
                    if destination_account == account.account_number:
                        from utils.message_manager import send_and_save_message
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        
                        error_text = "⚠️ شما نمی‌توانید به خودتان پرس ارسال کنید."
                        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                        return
                    
                    # Check balance before proceeding
                    import config
                    balance = float(account.balance)
                    fee = min(amount * config.TRANSACTION_FEE_PERCENT, config.MAX_TRANSACTION_FEE)
                    total_needed = amount + fee
                    
                    if balance < total_needed:
                        from utils.message_manager import send_and_save_message
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        
                        error_text = f"❌ موجودی شما کافی نیست.\n\n"
                        error_text += f"موجودی: {balance:,.2f} PERS\n"
                        error_text += f"مبلغ مورد نیاز: {total_needed:,.2f} PERS (مبلغ + کارمزد)"
                        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                        return
                
                # User has account, start send process with pre-filled destination and amount
                from utils.encryption import encrypt_state
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                import config
                
                if destination_account:
                    # New format: start send process with destination and amount pre-filled
                    # Calculate fee (already calculated above if balance check passed)
                    if 'fee' not in locals():
                        fee = min(amount * config.TRANSACTION_FEE_PERCENT, config.MAX_TRANSACTION_FEE)
                    
                    state = {
                        'action': 'send_pers',
                        'step': 'enter_password',
                        'destination': destination_account,
                        'amount': amount,
                        'fee': fee,
                        'payment_link_amount': amount,
                        'from_payment_link': True
                    }
                    encrypted_state = encrypt_state(state)
                    self.db.update_user_state(user_id, encrypted_state)
                    
                    send_text = "🔗 لینک پرداخت\n\n"
                    send_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
                    send_text += f"💰 مبلغ: {amount:,.2f} PERS\n\n"
                    send_text += "برای ارسال این مبلغ، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
                    send_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
                    
                    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await send_and_save_message(context, update.effective_chat.id, send_text, self.db, user_id, reply_markup=reply_markup)
                else:
                    # Old format: treat as buy (backward compatibility)
                    state = {
                        'action': 'buy_pers',
                        'step': 'enter_password',
                        'amount': amount,
                        'from_payment_link': True
                    }
                    encrypted_state = encrypt_state(state)
                    self.db.update_user_state(user_id, encrypted_state)
                    
                    buy_text = "🔗 لینک پرداخت\n\n"
                    buy_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
                    buy_text += f"💰 مبلغ: {amount:,.2f} PERS\n\n"
                    buy_text += "برای شارژ حساب خود، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
                    buy_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
                    
                    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await send_and_save_message(context, update.effective_chat.id, buy_text, self.db, user_id, reply_markup=reply_markup)
                return
            except (ValueError, IndexError):
                # Invalid payment link format, continue to normal start flow
                pass
        
        # Check if user has accepted agreement
        if not self.db.has_accepted_agreement(user_id):
            # Show agreement first
            await self.show_agreement(update, context)
            return
        
        # Check if user has active account
        active_account = self.db.get_active_account(user_id)
        
        if active_account:
            # User has account, show main menu
            await self.show_main_menu(update, context)
        else:
            # New user or no active account, show welcome
            await self.show_welcome(update, context)
    
    async def show_agreement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show agreement/terms of service"""
        agreement_text = """📋 موافقت‌نامه استفاده از ربات پرس بات

با استفاده از این ربات، شما موافقت می‌کنید که:

1️⃣ تمام قوانین و مقررات استفاده از این سرویس را رعایت کنید
2️⃣ مسئولیت تمام تراکنش‌های انجام شده بر عهده شماست
3️⃣ اطلاعات حساب خود را محرمانه نگه دارید
4️⃣ از ربات برای اهداف قانونی و مجاز استفاده کنید
5️⃣ در صورت سوء استفاده، حساب شما ممکن است مسدود شود

⚠️ توجه: استفاده از این ربات به معنای پذیرش کامل این شرایط است.

📄 فایل کامل تعهدنامه و شرایط استفاده از سامانه در زیر ارسال شده است. لطفا آن را مطالعه فرمایید.

آیا موافقت‌نامه را می‌پذیرید؟"""

        # Get PDF file path
        project_root = os.path.dirname(os.path.dirname(__file__))
        pdf_path = os.path.join(project_root, "متن تعهدنامه و شرایط استفاده از سامانه.pdf")
        
        chat_id = update.effective_chat.id
        
        # Send PDF document with agreement text as caption
        pdf_message_id = None
        if os.path.exists(pdf_path):
            try:
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_message = await context.bot.send_document(
                        chat_id=chat_id,
                        document=pdf_file,
                        caption=agreement_text
                    )
                    pdf_message_id = pdf_message.message_id
                    # Store PDF message ID in user_data for later deletion
                    if 'agreement_messages' not in context.user_data:
                        context.user_data['agreement_messages'] = []
                    context.user_data['agreement_messages'].append(pdf_message_id)
            except Exception as e:
                # If PDF sending fails, send text message instead
                logging.error(f"Error sending PDF: {e}")
                keyboard = [
                    [InlineKeyboardButton("✅ بله، می‌پذیرم", callback_data="accept_agreement")],
                    [InlineKeyboardButton("❌ خیر", callback_data="decline_agreement")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if update.message:
                    await update.message.reply_text(agreement_text + "\n\n⚠️ خطا در ارسال فایل PDF", reply_markup=reply_markup)
                elif update.callback_query:
                    await update.callback_query.edit_message_text(agreement_text + "\n\n⚠️ خطا در ارسال فایل PDF", reply_markup=reply_markup)
                return
        else:
            # If PDF doesn't exist, send text message with buttons
            logging.warning(f"PDF file not found: {pdf_path}")
            keyboard = [
                [InlineKeyboardButton("✅ بله، می‌پذیرم", callback_data="accept_agreement")],
                [InlineKeyboardButton("❌ خیر", callback_data="decline_agreement")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.message:
                await update.message.reply_text(agreement_text, reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.edit_message_text(agreement_text, reply_markup=reply_markup)
            return
        
        # Send agreement question with buttons (after PDF is sent)
        question_text = "آیا موافقت‌نامه را می‌پذیرید؟"
        keyboard = [
            [InlineKeyboardButton("✅ بله، می‌پذیرم", callback_data="accept_agreement")],
            [InlineKeyboardButton("❌ خیر", callback_data="decline_agreement")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            question_message = await update.message.reply_text(question_text, reply_markup=reply_markup)
            if 'agreement_messages' not in context.user_data:
                context.user_data['agreement_messages'] = []
            context.user_data['agreement_messages'].append(question_message.message_id)
        elif update.callback_query:
            # After sending PDF, we need to send a new message, not edit
            question_message = await context.bot.send_message(
                chat_id=chat_id,
                text=question_text,
                reply_markup=reply_markup
            )
            if 'agreement_messages' not in context.user_data:
                context.user_data['agreement_messages'] = []
            context.user_data['agreement_messages'].append(question_message.message_id)
    
    async def handle_accept_agreement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle agreement acceptance"""
        user_id = str(update.effective_user.id)
        
        # Mark agreement as accepted
        self.db.accept_agreement(user_id)
        
        # Send confirmation message
        confirmation_text = """✅ موافقت‌نامه با موفقیت پذیرفته شد!

📋 با استفاده از این ربات، شما شرایط استفاده و قوانین را پذیرفته‌اید.

⚠️ توجه: استفاده از ربات به معنای پذیرش کامل شرایط استفاده و قوانین است."""
        
        # Delete previous message and send confirmation
        confirmation_message_id = None
        if update.callback_query:
            # Delete the message with buttons
            try:
                await update.callback_query.message.delete()
            except:
                pass
            # Send confirmation message
            confirmation_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=confirmation_text
            )
            confirmation_message_id = confirmation_message.message_id
            # Store confirmation message ID for later deletion
            if 'agreement_messages' not in context.user_data:
                context.user_data['agreement_messages'] = []
            context.user_data['agreement_messages'].append(confirmation_message_id)
        elif update.message:
            confirmation_message = await update.message.reply_text(confirmation_text)
            confirmation_message_id = confirmation_message.message_id
            if 'agreement_messages' not in context.user_data:
                context.user_data['agreement_messages'] = []
            context.user_data['agreement_messages'].append(confirmation_message_id)
        
        # Check if there's a pending payment link
        encrypted_state = self.db.get_user_state(user_id)
        if encrypted_state:
            state = decrypt_state(encrypted_state)
            if state.get('pending_payment_link') and state.get('payment_link_amount'):
                # User clicked payment link before accepting agreement
                amount = state.get('payment_link_amount')
                destination_account = state.get('payment_link_destination')
                active_account = self.db.get_active_account(user_id)
                
                if not active_account:
                    # User doesn't have account yet
                    await self.show_welcome(update, context)
                    return
                
                # Check if destination account exists
                if destination_account:
                    dest_account = self.db.get_account_by_number(destination_account)
                    if not dest_account:
                        from utils.message_manager import send_and_save_message
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        
                        error_text = "❌ خطا در لینک پرداخت\n\n"
                        error_text += "شماره حساب مقصد در لینک پرداخت معتبر نیست."
                        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                        return
                    
                    # Check if user is trying to send to themselves
                    if destination_account == active_account.account_number:
                        from utils.message_manager import send_and_save_message
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        
                        error_text = "⚠️ شما نمی‌توانید به خودتان پرس ارسال کنید."
                        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                        return
                    
                    # Check balance before proceeding
                    from utils.message_manager import send_and_save_message
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    from utils.encryption import encrypt_state
                    import config
                    
                    balance = float(active_account.balance)
                    fee = min(amount * config.TRANSACTION_FEE_PERCENT, config.MAX_TRANSACTION_FEE)
                    total_needed = amount + fee
                    
                    if balance < total_needed:
                        error_text = f"❌ موجودی شما کافی نیست.\n\n"
                        error_text += f"موجودی: {balance:,.2f} PERS\n"
                        error_text += f"مبلغ مورد نیاز: {total_needed:,.2f} PERS (مبلغ + کارمزد)"
                        keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                        return
                    
                    # Start send process with destination and amount pre-filled
                    
                    state = {
                        'action': 'send_pers',
                        'step': 'enter_password',
                        'destination': destination_account,
                        'amount': amount,
                        'fee': fee,
                        'payment_link_amount': amount,
                        'from_payment_link': True
                    }
                    encrypted_state = encrypt_state(state)
                    self.db.update_user_state(user_id, encrypted_state)
                    
                    send_text = "🔗 لینک پرداخت\n\n"
                    send_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
                    send_text += f"💰 مبلغ: {amount:,.2f} PERS\n\n"
                    send_text += "برای ارسال این مبلغ، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
                    send_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
                    
                    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await send_and_save_message(context, update.effective_chat.id, send_text, self.db, user_id, reply_markup=reply_markup)
                else:
                    # Old format: start buy process with pre-filled amount (backward compatibility)
                    from utils.message_manager import send_and_save_message
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    from utils.encryption import encrypt_state
                    
                    state = {
                        'action': 'buy_pers',
                        'step': 'enter_password',
                        'amount': amount,
                        'from_payment_link': True
                    }
                    encrypted_state = encrypt_state(state)
                    self.db.update_user_state(user_id, encrypted_state)
                    
                    buy_text = "🔗 لینک پرداخت\n\n"
                    buy_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
                    buy_text += f"💰 مبلغ: {amount:,.2f} PERS\n\n"
                    buy_text += "برای شارژ حساب خود، لطفا رمز عبور ۸ رقمی خود را وارد کنید:\n\n"
                    buy_text += "⚠️ توجه: برای امنیت بیشتر، رمز عبور شما نمایش داده نمی‌شود."
                    
                    keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await send_and_save_message(context, update.effective_chat.id, buy_text, self.db, user_id, reply_markup=reply_markup)
                
                # Clear the pending payment link state
                return
        
        # Show welcome or main menu
        active_account = self.db.get_active_account(user_id)
        
        if active_account:
            await self.show_main_menu(update, context)
        else:
            await self.show_welcome(update, context)
        
        # Delete agreement messages (PDF and confirmation) after showing menu
        if 'agreement_messages' in context.user_data:
            chat_id = update.effective_chat.id
            for msg_id in context.user_data['agreement_messages']:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except:
                    pass
            # Clear the list
            context.user_data['agreement_messages'] = []
    
    async def handle_decline_agreement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle agreement decline"""
        decline_text = "❌ برای استفاده از ربات، باید موافقت‌نامه را بپذیرید.\n\nلطفا /start را دوباره ارسال کنید."
        
        if update.callback_query:
            await update.callback_query.edit_message_text(decline_text)
    
    async def show_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message with two buttons"""
        keyboard = [
            [InlineKeyboardButton("ساخت اکانت جدید", callback_data="create_account")],
            [InlineKeyboardButton("بازیابی اکانت قبلی", callback_data="recover_account")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = "👋 به ربات پرس بات خوش آمدید!\n\n"
        welcome_text += "🎉 ربات پرس بات یک سیستم مدیریت دارایی دیجیتال است که به شما امکان خرید، فروش و انتقال PERS را می‌دهد.\n\n"
        welcome_text += "✨ ویژگی‌های ربات:\n"
        welcome_text += "• خرید PERS با پرداخت آنلاین\n"
        welcome_text += "• ارسال PERS به سایر کاربران\n"
        welcome_text += "• فروش PERS و دریافت تومان\n"
        welcome_text += "• مشاهده موجودی و تراکنش‌ها\n"
        welcome_text += "• ساخت لینک پرداخت\n\n"
        welcome_text += "برای شروع، لطفا یکی از گزینه‌های زیر را انتخاب کنید:"
        
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        elif update.callback_query:
            # Try to edit, if message was deleted, send new message
            try:
                await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
            except Exception:
                # Message was deleted, send new message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=welcome_text,
                    reply_markup=reply_markup
                )
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        user_id = str(update.effective_user.id)
        
        # Get account info for personalized welcome
        account = self.db.get_active_account(user_id)
        
        keyboard = [
            [InlineKeyboardButton("💰 موجودی حساب", callback_data="balance")],
            [InlineKeyboardButton("🛒 خرید پرس", callback_data="buy_pers")],
            [InlineKeyboardButton("📤 ارسال پرس", callback_data="send_pers")],
            [InlineKeyboardButton("💸 فروش پرس", callback_data="sell_pers")],
            [InlineKeyboardButton("📋 ۱۰ گردش آخر", callback_data="transactions")],
            [InlineKeyboardButton("📞 ارتباط با ما", callback_data="contact")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = "👋 خوش آمدید!\n\n"
        menu_text += "🎯 منوی اصلی ربات پرس بات\n\n"
        
        if account:
            balance = float(account.balance)
            menu_text += f"💼 موجودی فعلی شما: {balance:,.2f} PERS\n\n"
        
        menu_text += "📌 گزینه‌های موجود:\n"
        menu_text += "• 💰 موجودی حساب: مشاهده موجودی و ساخت لینک پرداخت\n"
        menu_text += "• 🛒 خرید پرس: خرید PERS با پرداخت آنلاین\n"
        menu_text += "• 📤 ارسال پرس: ارسال PERS به سایر کاربران\n"
        menu_text += "• 💸 فروش پرس: فروش PERS و دریافت تومان\n"
        menu_text += "• 📋 ۱۰ گردش آخر: مشاهده آخرین تراکنش‌ها\n"
        menu_text += "• 📞 ارتباط با ما: ارسال پیام به پشتیبانی\n\n"
        menu_text += "لطفا یکی از گزینه‌های بالا را انتخاب کنید:"
        
        if update.message:
            await update.message.reply_text(menu_text, reply_markup=reply_markup)
        elif update.callback_query:
            # Try to edit, if message was deleted, send new message
            try:
                await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
            except Exception:
                # Message was deleted, send new message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=menu_text,
                    reply_markup=reply_markup
                )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        username = update.effective_user.username  # Get username from Telegram
        
        # Update username if available (in case it changed)
        if username:
            self.db.get_or_create_user(user_id, username)
        
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

