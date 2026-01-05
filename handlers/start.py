from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.encryption import encrypt_state, decrypt_state
from utils.lock_manager import LockManager
from typing import Optional
import asyncio
import os
import logging


class StartHandler:
    def __init__(self, db_manager: DatabaseManager, lock_manager: LockManager):
        self.db = db_manager
        self.lock_manager = lock_manager
    
    async def handle_payment_link_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                            destination_account: Optional[str], amount: float, 
                                            token: Optional[str] = None) -> bool:
        """
        Process payment link - extracted to be reusable from both /start and text messages
        Returns: True if payment link was processed, False otherwise
        """
        user_id = str(update.effective_user.id)
        
        # If token is provided, check if it's a token-based link
        if token:
            # Check if payment link exists and is not used
            payment_link = self.db.get_payment_link(token)
            if not payment_link:
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                error_text = "❌ خطا در لینک پرداخت\n\nلینک پرداخت معتبر نیست."
                keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                return True
            
            # Check if link has already been used
            if payment_link.is_used:
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                error_text = "❌ این لینک پرداخت قبلا استفاده شده است.\n\n"
                error_text += "⚠️ لینک‌های پرداخت فقط یکبار قابل استفاده هستند."
                keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                return True
            
            # Get destination account and amount from payment link
            destination_account = payment_link.destination_account
            amount = float(payment_link.amount)
        
        # Check if user has accepted agreement
        if not self.db.has_accepted_agreement(user_id):
            # Store payment link info in state for later use after agreement
            from utils.encryption import encrypt_state
            state = {
                'pending_payment_link': True,
                'payment_link_amount': amount,
                'payment_link_destination': destination_account,
                'payment_link_token': token
            }
            encrypted_state = encrypt_state(state)
            self.db.update_user_state(user_id, encrypted_state)
            # Show agreement first (with payment link indicator)
            await self.show_agreement(update, context, from_payment_link=True)
            return True
        
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
            return True
        
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
                return True
            
            # Check if user is trying to send to themselves
            if destination_account == account.account_number:
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                error_text = "⚠️ شما نمی‌توانید به خودتان پرس ارسال کنید."
                keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                return True
            
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
                return True
            
            # ✅ انتقال اعتبار به صورت خودکار (مثل bot__.py)
            # Get admin account for fee
            admin_account_number = self.db.get_admin_account_number()
            if not admin_account_number:
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                error_text = "❌ خطا در سیستم\n\nحساب ادمین یافت نشد. لطفا با پشتیبانی تماس بگیرید."
                keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                return True
            
            # Ensure admin account exists
            admin_account = self.db.get_account_by_number(admin_account_number)
            if not admin_account:
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                error_text = f"❌ خطا در سیستم\n\nحساب ادمین {admin_account_number} در دیتابیس یافت نشد."
                keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                return True
            
            # Perform transaction directly (like bot__.py)
            logger = logging.getLogger(__name__)
            try:
                # Get balances before transaction
                from_balance_before = self.db.get_account_balance(account.account_number)
                to_balance_before = self.db.get_account_balance(destination_account)
                admin_balance_before = self.db.get_account_balance(admin_account_number)
                
                logger.info(f"Processing payment link - From: {account.account_number}, To: {destination_account}, Amount: {amount}, Fee: {fee}")
                logger.info(f"Balances before - From: {from_balance_before}, To: {to_balance_before}, Admin: {admin_balance_before}")
                
                # Perform transaction
                self.db.update_account_balance(account.account_number, -(amount + fee))
                self.db.update_account_balance(destination_account, amount)
                self.db.update_account_balance(admin_account_number, fee)
                
                # Verify balances after transaction
                from_balance_after = self.db.get_account_balance(account.account_number)
                to_balance_after = self.db.get_account_balance(destination_account)
                admin_balance_after = self.db.get_account_balance(admin_account_number)
                
                logger.info(f"Balances after - From: {from_balance_after}, To: {to_balance_after}, Admin: {admin_balance_after}")
                
                # Create transaction record
                transaction = self.db.create_transaction(
                    from_account=account.account_number,
                    to_account=destination_account,
                    amount=amount,
                    fee=fee,
                    transaction_type='send'
                )
                
                # Update transaction status
                self.db.update_transaction_status(transaction.id, 'success')
                
                # Create comprehensive transaction log
                username = update.effective_user.username if update.effective_user else None
                self.db.create_transaction_log(
                    user_id=user_id,
                    username=username,
                    transaction_type='send',
                    from_account=account.account_number,
                    to_account=destination_account,
                    amount=amount,
                    fee=fee,
                    sheba=None,
                    status='success',
                    transaction_id=transaction.id
                )
                
                logger.info(f"Transaction successful - ID: {transaction.id}")
                
                # Mark payment link as used and notify creator if token was provided
                if token:
                    # Get payment link before marking as used
                    payment_link = self.db.get_payment_link(token)
                    self.db.mark_payment_link_as_used(token, user_id)
                    
                    # Send notification to payment link creator
                    if payment_link and payment_link.created_by:
                        try:
                            creator_user_id = payment_link.created_by
                            
                            notification_text = "🔔 اطلاع از استفاده لینک پرداخت\n\n"
                            notification_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
                            notification_text += f"✅ لینک پرداخت شما استفاده شد!\n\n"
                            notification_text += f"💰 مبلغ واریز شده: {amount:,.2f} PERS\n"
                            notification_text += f"💳 کارمزد: {fee:,.2f} PERS\n"
                            notification_text += f"📤 از حساب: {account.account_number}\n"
                            notification_text += f"📥 به حساب شما: {destination_account}\n\n"
                            
                            # Get creator's account balance for destination account
                            dest_account = self.db.get_account_by_number(destination_account)
                            if dest_account:
                                creator_balance = float(self.db.get_account_balance(destination_account))
                                notification_text += f"💼 موجودی جدید حساب شما: {creator_balance:,.2f} PERS\n\n"
                            
                            notification_text += "━━━━━━━━━━━━━━━━━━━━"
                            
                            await context.bot.send_message(chat_id=int(creator_user_id), text=notification_text)
                            logger.info(f"Notification sent to payment link creator: {creator_user_id}")
                        except Exception as e:
                            # User might have blocked the bot, ignore the error
                            logger.warning(f"Could not send notification to payment link creator: {e}")
                
                # Send success message to sender
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                success_text = f"✅ پرداخت با موفقیت انجام شد!\n\n"
                success_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
                success_text += f"💰 مبلغ: {amount:,.2f} PERS\n"
                success_text += f"📤 به حساب: {destination_account}\n"
                success_text += f"💳 کارمزد: {fee:,.2f} PERS\n\n"
                new_balance = float(self.db.get_account_balance(account.account_number))
                success_text += f"💼 موجودی جدید شما: {new_balance:,.2f} PERS\n\n"
                success_text += f"━━━━━━━━━━━━━━━━━━━━"
                
                keyboard = [
                    [InlineKeyboardButton("💰 موجودی حساب", callback_data="balance")],
                    [InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, success_text, self.db, user_id, reply_markup=reply_markup)
                
                # Send notification to recipient (like bot__.py does)
                try:
                    dest_account = self.db.get_account_by_number(destination_account)
                    if dest_account:
                        recipient_user_id = dest_account.user_id
                        recipient_balance = float(self.db.get_account_balance(destination_account))
                        
                        notification_text = "✅ واریز به حساب شما\n\n"
                        notification_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
                        notification_text += f"💰 مبلغ واریزی: {amount:,.2f} PERS\n\n"
                        notification_text += f"از حساب: {account.account_number}\n\n"
                        notification_text += f"💼 موجودی جدید حساب: {recipient_balance:,.2f} PERS\n\n"
                        notification_text += "━━━━━━━━━━━━━━━━━━━━"
                        
                        await context.bot.send_message(chat_id=int(recipient_user_id), text=notification_text)
                        logger.info(f"Notification sent to recipient: {recipient_user_id}")
                except Exception as e:
                    # User might have blocked the bot, ignore the error
                    logger.warning(f"Could not send notification to recipient {destination_account}: {e}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error processing payment link transaction: {e}", exc_info=True)
                from utils.message_manager import send_and_save_message
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                error_text = "❌ خطا در پردازش پرداخت\n\n"
                error_text += "متأسفانه در پردازش تراکنش خطایی رخ داد.\n\n"
                error_text += "لطفا:\n"
                error_text += "• دوباره تلاش کنید\n"
                error_text += "• یا با پشتیبانی تماس بگیرید\n\n"
                error_text += "⚠️ توجه: در صورت کسر موجودی، مبلغ به حساب شما بازگردانده می‌شود."
                
                keyboard = [[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_and_save_message(context, update.effective_chat.id, error_text, self.db, user_id, reply_markup=reply_markup)
                return True
        else:
            # Old format: treat as buy (backward compatibility)
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
        
        return True
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        logger = logging.getLogger(__name__)
        
        try:
            user_id = str(update.effective_user.id)
            username = update.effective_user.username  # Get username from Telegram
            
            # Check if user is locked
            is_locked, lock_message = self.lock_manager.check_lock(user_id)
            if is_locked:
                if update.message:
                    await update.message.reply_text(lock_message)
                elif update.callback_query:
                    await update.callback_query.message.reply_text(lock_message)
                else:
                    # Fallback: send message directly
                    chat_id = update.effective_chat.id
                    await context.bot.send_message(chat_id=chat_id, text=lock_message)
                return
            
            # Get or create user (and update username if available)
            user = self.db.get_or_create_user(user_id, username)
            
            # Check for payment link parameter (deep link)
            # Format: /start pay_{destination_account}_{amount}
            # Log for debugging
            logger.info(f"Start command received - user_id: {user_id}, args: {context.args}")
            
            if context.args and len(context.args) > 0 and context.args[0].startswith('pay_'):
                # This is a payment link click
                logger.info(f"Payment link detected: {context.args[0]}")
                try:
                    # Parse payment link using the utility function
                    from utils.generators import parse_payment_link
                    url = f"https://t.me/{context.bot.username}?start={context.args[0]}"
                    is_payment_link, destination_account, amount, token = parse_payment_link(url)
                    
                    if not is_payment_link:
                        raise ValueError("Invalid payment link format")
                    
                    # Process payment link using the extracted method
                    logger.info(f"Calling handle_payment_link_processing - token: {token}, destination: {destination_account}, amount: {amount}")
                    await self.handle_payment_link_processing(update, context, destination_account, amount, token)
                    logger.info("Payment link processing completed")
                    return
                except (ValueError, IndexError) as e:
                    # Invalid payment link format, continue to normal start flow
                    logger.error(f"Error parsing payment link: {e}", exc_info=True)
                    # Send error message to user but continue to normal start flow
                    try:
                        error_text = "❌ خطا در لینک پرداخت\n\nلینک پرداخت معتبر نیست. لطفا از لینک صحیح استفاده کنید."
                        if update.message:
                            await update.message.reply_text(error_text)
                        else:
                            chat_id = update.effective_chat.id
                            await context.bot.send_message(chat_id=chat_id, text=error_text)
                    except Exception as send_error:
                        logger.error(f"Error sending error message: {send_error}", exc_info=True)
                    # Continue to normal start flow (show agreement or menu)
                except Exception as e:
                    # Log any other errors
                    logger.error(f"Unexpected error processing payment link: {e}", exc_info=True)
                    # Send error message to user but continue to normal start flow
                    try:
                        error_text = "❌ خطا در پردازش لینک پرداخت\n\nلطفا دوباره تلاش کنید."
                        if update.message:
                            await update.message.reply_text(error_text)
                        else:
                            chat_id = update.effective_chat.id
                            await context.bot.send_message(chat_id=chat_id, text=error_text)
                    except Exception as send_error:
                        logger.error(f"Error sending error message: {send_error}", exc_info=True)
                    # Continue to normal start flow
            
            # Check if user has accepted agreement
            if not self.db.has_accepted_agreement(user_id):
                # Show agreement first
                try:
                    await self.show_agreement(update, context)
                except Exception as e:
                    # If show_agreement fails, send a fallback message
                    logger.error(f"Error showing agreement: {e}", exc_info=True)
                    chat_id = update.effective_chat.id
                    error_text = "❌ خطا در نمایش موافقت‌نامه\n\nلطفا دوباره تلاش کنید: /start"
                    try:
                        if update.message:
                            await update.message.reply_text(error_text)
                        else:
                            await context.bot.send_message(chat_id=chat_id, text=error_text)
                    except Exception as send_error:
                        logger.error(f"Error sending error message: {send_error}", exc_info=True)
                return
            
            # Check if user has active account
            active_account = self.db.get_active_account(user_id)
            
            if active_account:
                # User has account, show main menu
                try:
                    await self.show_main_menu(update, context)
                except Exception as e:
                    logger.error(f"Error showing main menu: {e}", exc_info=True)
                    # Fallback: send simple message
                    chat_id = update.effective_chat.id
                    error_text = "❌ خطا در نمایش منو\n\nلطفا دوباره تلاش کنید: /start"
                    try:
                        if update.message:
                            await update.message.reply_text(error_text)
                        else:
                            await context.bot.send_message(chat_id=chat_id, text=error_text)
                    except:
                        pass
            else:
                # New user or no active account, show welcome
                try:
                    await self.show_welcome(update, context)
                except Exception as e:
                    logger.error(f"Error showing welcome: {e}", exc_info=True)
                    # Fallback: send simple message
                    chat_id = update.effective_chat.id
                    error_text = "❌ خطا در نمایش پیام خوش‌آمدگویی\n\nلطفا دوباره تلاش کنید: /start"
                    try:
                        if update.message:
                            await update.message.reply_text(error_text)
                        else:
                            await context.bot.send_message(chat_id=chat_id, text=error_text)
                    except:
                        pass
        except Exception as e:
            # Catch any unexpected errors and ensure a message is always sent
            logger.error(f"Unexpected error in handle_start: {e}", exc_info=True)
            chat_id = update.effective_chat.id
            error_text = "❌ خطا در پردازش درخواست\n\nلطفا دوباره تلاش کنید: /start"
            try:
                if update.message:
                    await update.message.reply_text(error_text)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=error_text)
            except Exception as send_error:
                logger.error(f"Error sending error message: {send_error}", exc_info=True)
    
    async def show_agreement(self, update: Update, context: ContextTypes.DEFAULT_TYPE, from_payment_link: bool = False):
        """Show agreement/terms of service"""
        user_id = str(update.effective_user.id)
        
        # Check if user came from payment link
        if not from_payment_link:
            encrypted_state = self.db.get_user_state(user_id)
            if encrypted_state:
                state = decrypt_state(encrypted_state)
                from_payment_link = state.get('pending_payment_link', False)
        
        agreement_text = """📋 موافقت‌نامه استفاده از ربات پرس بات

با استفاده از این ربات، شما موافقت می‌کنید که:

1️⃣ تمام قوانین و مقررات استفاده از این سرویس را رعایت کنید
2️⃣ مسئولیت تمام تراکنش‌های انجام شده بر عهده شماست
3️⃣ اطلاعات حساب خود را محرمانه نگه دارید
4️⃣ از ربات برای اهداف قانونی و مجاز استفاده کنید
5️⃣ در صورت سوء استفاده، حساب شما ممکن است مسدود شود

⚠️ توجه: استفاده از این ربات به معنای پذیرش کامل این شرایط است.

📄 فایل کامل تعهدنامه و شرایط استفاده از سامانه در زیر ارسال شده است. لطفا آن را مطالعه فرمایید."""
        
        # Add payment link message if user came from payment link
        if from_payment_link:
            agreement_text += "\n\n" + "🔗 توجه:\n"
            agreement_text += "شما از طریق لینک پرداخت وارد شده‌اید.\n"
            agreement_text += "پس از پذیرش موافقت‌نامه، پردازش لینک پرداخت ادامه خواهد یافت."
        
        agreement_text += "\n\nآیا موافقت‌نامه را می‌پذیرید؟"

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
                token = state.get('payment_link_token')
                
                # ✅ استفاده از همان تابع handle_payment_link_processing برای پردازش
                # Clear pending state first
                self.db.update_user_state(user_id, "")
                
                # Process payment link using the same method
                await self.handle_payment_link_processing(update, context, destination_account, amount, token)
                
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
            [InlineKeyboardButton("🔗 ساخت لینک پرداخت", callback_data="create_payment_link")],
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
        menu_text += "• 🔗 ساخت لینک پرداخت: ساخت لینک پرداخت برای دریافت PERS از دیگران\n"
        menu_text += "• 💰 موجودی حساب: مشاهده موجودی حساب\n"
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

