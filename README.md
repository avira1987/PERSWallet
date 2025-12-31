# BalanceBot - Telegram Bot

ربات تلگرام برای مدیریت کیف پول PERS با قابلیت‌های خرید، فروش، ارسال و دریافت.

## ویژگی‌ها

- ساخت و بازیابی اکانت
- خرید و فروش PERS
- ارسال PERS به سایر اکانت‌ها
- مشاهده موجودی و تراکنش‌ها
- تولید لینک پرداخت با QR Code
- گزارش PDF تراکنش‌ها

## نصب

1. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

2. کپی کردن فایل `.env.example` به `.env` و پر کردن مقادیر:
```bash
cp .env.example .env
```

3. ایجاد دیتابیس PostgreSQL و تنظیم `DATABASE_URL` در `.env`

4. اجرای ربات:
```bash
python bot.py
```

## تنظیمات

- `BOT_TOKEN`: توکن ربات از BotFather
- `ADMIN_USER_ID`: User ID عددی اکانت ادمین
- `DATABASE_URL`: آدرس دیتابیس PostgreSQL
- `ENCRYPTION_KEY`: کلید رمزنگاری 32 بایتی

