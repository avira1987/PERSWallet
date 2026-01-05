import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Conflict
import uuid

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن بات
BOT_TOKEN = "320315592:AAFXTfKLrcqjuLk7Fv151-IgYzhZRyI07A0"

# فایل ذخیره‌سازی داده‌ها
DATA_FILE = "users_data.json"

# مقدار اعتباری که از حساب دعوت‌کننده کسر می‌شود (پیش‌فرض - برای سازگاری)
CREDIT_COST_PER_REFERRAL = 10


def load_data():
    """بارگذاری داده‌های کاربران از فایل JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {}
    return {}

def save_data(data):
    """ذخیره داده‌های کاربران در فایل JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def get_or_create_user(user_id, username=None):
    """دریافت یا ایجاد کاربر جدید"""
    data = load_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        data[user_id_str] = {
            "username": username,
            "credits": 100,  # اعتبار اولیه
            "referral_code": str(uuid.uuid4())[:8].upper(),
            "referrals": [],
            "referred_by": None,
            "joined_at": datetime.now().isoformat()
        }
        save_data(data)
    
    return data[user_id_str]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    # بررسی اینکه آیا کاربر از طریق لینک دعوت آمده است
    referral_code = None
    if context.args and len(context.args) > 0:
        referral_code = context.args[0]
        logger.info(f"User {user_id} started with referral_code: {referral_code}")
    
    # اگر کاربر از طریق لینک دعوت آمده باشد
    if referral_code:
        data = load_data()
        user_id_str = str(user_id)
        
        # بررسی اینکه آیا referral_code شامل تعداد امتیاز است (فرمت: code_points)
        points_amount = None
        actual_referral_code = referral_code
        
        logger.info(f"Processing referral_code: {referral_code}")
        
        # اگر شامل underscore باشد، split کن
        if '_' in referral_code:
            parts = referral_code.split('_', 1)
            logger.info(f"Split referral_code into parts: {parts}")
            if len(parts) == 2:
                try:
                    points_amount = int(parts[1])
                    actual_referral_code = parts[0]
                    logger.info(f"Extracted points_amount: {points_amount}, actual_referral_code: {actual_referral_code}")
                except ValueError:
                    logger.warning(f"Could not parse points_amount from: {parts[1]}")
                    pass  # اگر عدد نبود، همان referral_code اصلی استفاده می‌شود
        
        # اطمینان از وجود کاربر در دیتا
        if user_id_str not in data:
            logger.info(f"User {user_id_str} not found, creating new user")
            get_or_create_user(user_id, username)
            # بارگذاری مجدد data برای اطمینان از به‌روز بودن
            data = load_data()
            user_data = data[user_id_str]
        else:
            user_data = data[user_id_str]
            logger.info(f"User {user_id_str} found, referred_by: {user_data.get('referred_by')}")
            # به‌روزرسانی username در صورت تغییر
            if username and user_data.get("username") != username:
                user_data["username"] = username
                data[user_id_str] = user_data
                save_data(data)
        
        # پیدا کردن دعوت‌کننده (حتی اگر کاربر قبلاً دعوت شده باشد)
        logger.info(f"Looking for referrer with code: {actual_referral_code}")
        # پیدا کردن دعوت‌کننده
        referrer_id = None
        for uid, udata in data.items():
            if udata.get("referral_code") == actual_referral_code and uid != user_id_str:
                referrer_id = uid
                logger.info(f"Found referrer: {referrer_id} with code: {udata.get('referral_code')}")
                break
        
        if referrer_id and referrer_id in data:
            referrer_data = data[referrer_id]
            
            # استفاده از تعداد امتیاز سفارشی یا مقدار پیش‌فرض
            credit_amount = points_amount if points_amount is not None else CREDIT_COST_PER_REFERRAL
            logger.info(f"Credit amount to transfer: {credit_amount} (points_amount: {points_amount})")
            
            # کسر اعتبار از حساب دعوت‌کننده
            referrer_credits = referrer_data.get("credits", 0)
            logger.info(f"Referrer {referrer_id} has {referrer_credits} credits, need {credit_amount}")
            if referrer_credits >= credit_amount:
                # کسر از دعوت‌کننده
                referrer_data["credits"] = referrer_data.get("credits", 0) - credit_amount
                referrer_data.setdefault("referrals", []).append({
                    "user_id": user_id,
                    "username": username,
                    "joined_at": datetime.now().isoformat(),
                    "points_transferred": credit_amount
                })
                
                # اضافه کردن امتیاز به کاربر جدید
                # اطمینان از اینکه user_data به data متصل است
                if user_data is not data.get(user_id_str):
                    user_data = data[user_id_str]
                
                old_credits = user_data.get("credits", 0)
                user_data["credits"] = old_credits + credit_amount
                user_data["referred_by"] = referrer_id
                user_data["referral_code_used"] = actual_referral_code
                user_data["points_received"] = credit_amount
                
                # اطمینان از اینکه تغییرات در data اعمال شده است
                data[user_id_str] = user_data
                data[referrer_id] = referrer_data
                
                # لاگ برای دیباگ
                logger.info(f"Transferring {credit_amount} credits from {referrer_id} to {user_id_str}")
                logger.info(f"User {user_id_str} credits: {old_credits} -> {user_data['credits']}")
                logger.info(f"Referrer {referrer_id} credits before: {referrer_credits}, after: {referrer_data['credits']}")
                
                save_data(data)
                
                # بررسی اینکه داده‌ها درست ذخیره شده‌اند
                verify_data = load_data()
                if user_id_str in verify_data:
                    logger.info(f"Verification: User {user_id_str} credits in file: {verify_data[user_id_str].get('credits', 0)}")
                if referrer_id in verify_data:
                    logger.info(f"Verification: Referrer {referrer_id} credits in file: {verify_data[referrer_id].get('credits', 0)}")
            
                # اطلاع دادن به دعوت‌کننده
                try:
                    await context.bot.send_message(
                        chat_id=int(referrer_id),
                        text=f"✅ کاربر جدیدی از طریق لینک دعوت شما به بات پیوست!\n"
                             f"👤 کاربر: @{username if username else user_id}\n"
                             f"💳 از حساب شما {credit_amount} اعتبار کسر شد.\n"
                             f"💰 اعتبار باقیمانده: {referrer_data['credits']}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification to referrer {referrer_id}: {e}")
                
                # بارگذاری مجدد داده‌ها برای اطمینان از به‌روز بودن
                data = load_data()
                user_data = data.get(user_id_str, user_data)
                final_credits = user_data.get('credits', 0)
                logger.info(f"Final credits for user {user_id_str} after transfer: {final_credits}")
                
                welcome_message = f"""
🎉 به بات خوش آمدید!

✅ شما از طریق لینک دعوت کاربر دیگری وارد شدید.
💰 شما {credit_amount} اعتبار دریافت کردید!
💰 اعتبار شما: {final_credits}

💡 برای دریافت لینک دعوت خودتان از دستور زیر استفاده کنید:
/ref
                """
            else:
                # بارگذاری مجدد داده‌ها
                user_data = load_data().get(user_id_str, user_data)
                
                welcome_message = f"""
🎉 به بات خوش آمدید!

⚠️ لینک دعوت شما معتبر است اما دعوت‌کننده اعتبار کافی ندارد.
💰 اعتبار شما: {user_data.get('credits', 0)}

💡 برای دریافت لینک دعوت خودتان از دستور زیر استفاده کنید:
/ref
                """
        else:
            # referrer پیدا نشد یا اعتبار کافی نداشت
            logger.warning(f"Referrer not found or insufficient credits for code: {actual_referral_code}, user: {user_id_str}")
            user_data = load_data().get(user_id_str, user_data)
            welcome_message = f"""
🎉 به بات خوش آمدید!

❌ لینک دعوت شما معتبر نیست یا دعوت‌کننده اعتبار کافی ندارد.
💰 اعتبار شما: {user_data.get('credits', 0)}

💡 برای دریافت لینک دعوت خودتان از دستور زیر استفاده کنید:
/ref
            """
    else:
        # کاربر بدون لینک دعوت وارد شده
        user_data = get_or_create_user(user_id, username)
        welcome_message = f"""
🎉 به بات خوش آمدید!

💰 اعتبار شما: {user_data.get('credits', 0)}

💡 برای دریافت لینک دعوت خودتان از دستور زیر استفاده کنید:
/ref
        """
    
    # اطمینان از اینکه welcome_message تعریف شده است
    if 'welcome_message' not in locals():
        # اگر welcome_message تعریف نشده باشد (مثلاً در حالت else)
        data = load_data()
        user_id_str = str(user_id)
        if user_id_str in data:
            user_data = data[user_id_str]
        else:
            user_data = get_or_create_user(user_id, username)
        welcome_message = f"""
🎉 به بات خوش آمدید!

💰 اعتبار شما: {user_data.get('credits', 0)}

💡 برای دریافت لینک دعوت خودتان از دستور زیر استفاده کنید:
/ref
        """
    
    keyboard = [
        [InlineKeyboardButton("📊 پروفایل", callback_data="profile"),
         InlineKeyboardButton("🔗 لینک دعوت", callback_data="referral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.info(f"Sending welcome message to user {user_id}")
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /ref برای نمایش لینک دعوت"""
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    user_data = get_or_create_user(user_id, username)
    
    # پرسیدن تعداد امتیاز از کاربر
    context.user_data['waiting_for_points'] = True
    message = """
💰 لطفاً تعداد امتیازی که می‌خواهید به دعوت‌شونده انتقال دهید را وارد کنید:

📌 مثال: 50

⚠️ توجه: این تعداد امتیاز از حساب شما کسر و به حساب کسی که روی لینک کلیک می‌کند اضافه می‌شود.
    """
    
    keyboard = [
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_points")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /profile برای نمایش پروفایل"""
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    user_data = get_or_create_user(user_id, username)
    
    referrals_count = len(user_data.get('referrals', []))
    credits = user_data.get('credits', 0)
    referral_code = user_data.get('referral_code')
    referred_by = user_data.get('referred_by')
    
    message = f"""
📊 پروفایل شما:

👤 نام کاربری: @{username if username else 'بدون نام'}
🆔 شناسه: `{user_id}`
💰 اعتبار: {credits}
🔗 کد دعوت: `{referral_code}`
📈 تعداد دعوت‌های موفق: {referrals_count}

"""
    
    if referred_by:
        message += f"✅ شما توسط کاربر دیگری دعوت شده‌اید.\n"
    else:
        message += f"ℹ️ شما به صورت مستقیم وارد شده‌اید.\n"
    
    keyboard = [
        [InlineKeyboardButton("🔗 لینک دعوت", callback_data="referral"),
         InlineKeyboardButton("🔄 بروزرسانی", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک روی دکمه‌های اینلاین"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    user_data = get_or_create_user(user_id, username)
    
    if query.data == "profile":
        referrals_count = len(user_data.get('referrals', []))
        credits = user_data.get('credits', 0)
        referral_code = user_data.get('referral_code')
        referred_by = user_data.get('referred_by')
        
        message = f"""
📊 پروفایل شما:

👤 نام کاربری: @{username if username else 'بدون نام'}
🆔 شناسه: `{user_id}`
💰 اعتبار: {credits}
🔗 کد دعوت: `{referral_code}`
📈 تعداد دعوت‌های موفق: {referrals_count}
"""
        
        if referred_by:
            message += f"✅ شما توسط کاربر دیگری دعوت شده‌اید.\n"
        else:
            message += f"ℹ️ شما به صورت مستقیم وارد شده‌اید.\n"
        
        keyboard = [
            [InlineKeyboardButton("🔗 لینک دعوت", callback_data="referral"),
             InlineKeyboardButton("🔄 بروزرسانی", callback_data="profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "referral":
        # پرسیدن تعداد امتیاز از کاربر
        context.user_data['waiting_for_points'] = True
        message = """
💰 لطفاً تعداد امتیازی که می‌خواهید به دعوت‌شونده انتقال دهید را وارد کنید:

📌 مثال: 50

⚠️ توجه: این تعداد امتیاز از حساب شما کسر و به حساب کسی که روی لینک کلیک می‌کند اضافه می‌شود.
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_points")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif query.data == "cancel_points":
        # انصراف از ساخت لینک دعوت
        context.user_data.pop('waiting_for_points', None)
        await query.answer("❌ عملیات لغو شد")
        
        # بازگشت به پروفایل
        referrals_count = len(user_data.get('referrals', []))
        credits = user_data.get('credits', 0)
        referral_code = user_data.get('referral_code')
        referred_by = user_data.get('referred_by')
        
        message = f"""
📊 پروفایل شما:

👤 نام کاربری: @{username if username else 'بدون نام'}
🆔 شناسه: `{user_id}`
💰 اعتبار: {credits}
🔗 کد دعوت: `{referral_code}`
📈 تعداد دعوت‌های موفق: {referrals_count}
"""
        
        if referred_by:
            message += f"✅ شما توسط کاربر دیگری دعوت شده‌اید.\n"
        else:
            message += f"ℹ️ شما به صورت مستقیم وارد شده‌اید.\n"
        
        keyboard = [
            [InlineKeyboardButton("🔗 لینک دعوت", callback_data="referral"),
             InlineKeyboardButton("🔄 بروزرسانی", callback_data="profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def receive_points_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تعداد امتیاز از کاربر و ساخت لینک دعوت"""
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    if not context.user_data.get('waiting_for_points'):
        # اگر در حالت waiting نیست، پیام را به start بفرست
        return await start(update, context)
    
    try:
        points_amount = int(update.message.text.strip())
        
        if points_amount <= 0:
            await update.message.reply_text("❌ تعداد امتیاز باید بیشتر از صفر باشد!\n\nلطفاً یک عدد معتبر وارد کنید:")
            return
        
        user_data = get_or_create_user(user_id, username)
        current_credits = user_data.get('credits', 0)
        
        if current_credits < points_amount:
            await update.message.reply_text(f"❌ اعتبار کافی ندارید!\n\n💰 اعتبار فعلی شما: {current_credits}\n\nلطفاً تعداد کمتری وارد کنید:")
            return
        
        # ساخت لینک دعوت با تعداد امتیاز
        referral_code = user_data.get("referral_code")
        bot_username = context.bot.username
        referral_link_code = f"{referral_code}_{points_amount}"
        referral_link = f"https://t.me/{bot_username}?start={referral_link_code}"
        
        message = f"""
✅ لینک دعوت شما ساخته شد!

🔗 لینک دعوت:
{referral_link}

💰 تعداد امتیاز انتقالی: {points_amount}
📝 کد دعوت: {referral_code}

⚠️ توجه: هنگام کلیک روی این لینک، {points_amount} امتیاز از حساب شما کسر و به حساب کلیک‌کننده اضافه می‌شود.

📊 تعداد دعوت‌های شما: {len(user_data.get('referrals', []))}
💰 اعتبار فعلی: {current_credits}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔗 اشتراک‌گذاری لینک", url=f"https://t.me/share/url?url={referral_link}&text=به این بات بپیوندید و {points_amount} امتیاز دریافت کنید!")],
            [InlineKeyboardButton("📊 پروفایل", callback_data="profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.user_data.pop('waiting_for_points', None)
        await update.message.reply_text(message, reply_markup=reply_markup)
        
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!\n\nمثال: 50")
    except Exception as e:
        logger.error(f"Error in receive_points_message: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        context.user_data.pop('waiting_for_points', None)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاهای بات"""
    error = context.error
    
    # نادیده گرفتن خطای Conflict (چند instance در حال اجرا)
    if isinstance(error, Conflict):
        logger.warning(f"Conflict error (likely multiple bot instances): {error}")
        return
    
    logger.error(f"Update {update} caused error {error}", exc_info=error)

def main():
    """تابع اصلی برای اجرای بات"""
    # ایجاد اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن handler برای دکمه‌های اینلاین
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # اضافه کردن handler ها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ref", referral))
    application.add_handler(CommandHandler("profile", profile))
    
    # اضافه کردن handler برای دریافت تعداد امتیاز (باید قبل از handler عمومی باشد)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_points_message))
    
    # اضافه کردن error handler
    application.add_error_handler(error_handler)
    
    # حذف webhook برای اطمینان از polling
    try:
        application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted successfully")
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")
    
    # شروع بات
    logger.info("Bot is starting...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Conflict as e:
        logger.error(f"Conflict error - Another bot instance is running. Please stop other instances: {e}")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
