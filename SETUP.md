# راهنمای نصب و اجرای BalanceBot

## پیش‌نیازها

1. **Python 3.8 یا بالاتر** - [دانلود Python](https://www.python.org/downloads/)
2. **PostgreSQL** - [دانلود PostgreSQL](https://www.postgresql.org/download/)
3. **توکن ربات تلگرام** - از [@BotFather](https://t.me/BotFather) دریافت کنید

## مراحل نصب

### 1. نصب وابستگی‌های Python

در ترمینال (PowerShell یا CMD) در پوشه پروژه اجرا کنید:

```bash
pip install -r requirements.txt
```

یا اگر از pip3 استفاده می‌کنید:

```bash
pip3 install -r requirements.txt
```

### 2. راه‌اندازی دیتابیس PostgreSQL

#### الف) نصب PostgreSQL (اگر نصب نشده)

1. PostgreSQL را از [اینجا](https://www.postgresql.org/download/windows/) دانلود و نصب کنید
2. هنگام نصب، رمز عبور برای کاربر `postgres` را یادداشت کنید

#### ب) ایجاد دیتابیس

1. PostgreSQL را اجرا کنید
2. pgAdmin را باز کنید یا از خط فرمان استفاده کنید:

```sql
-- اتصال به PostgreSQL
psql -U postgres

-- ایجاد دیتابیس
CREATE DATABASE balancebot;

-- خروج
\q
```

یا از pgAdmin:
- راست کلیک روی "Databases" → "Create" → "Database"
- نام: `balancebot`
- Save

### 3. تنظیم فایل .env

1. فایل `.env.example` را کپی کنید و نام آن را به `.env` تغییر دهید:

```bash
copy .env.example .env
```

2. فایل `.env` را باز کنید و مقادیر زیر را پر کنید:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_USER_ID=123456789
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/balancebot
ENCRYPTION_KEY=your_32_byte_key_here_change_this!!
```

#### نحوه دریافت مقادیر:

**BOT_TOKEN:**
1. در تلگرام به [@BotFather](https://t.me/BotFather) پیام دهید
2. دستور `/newbot` را ارسال کنید
3. نام و username ربات را وارد کنید
4. توکن را کپی کنید

**ADMIN_USER_ID:**
1. در تلگرام به [@userinfobot](https://t.me/userinfobot) پیام دهید
2. User ID خود را کپی کنید (عدد)

**DATABASE_URL:**
- فرمت: `postgresql://username:password@host:port/database`
- مثال: `postgresql://postgres:mypassword@localhost:5432/balancebot`

**ENCRYPTION_KEY:**
- یک رشته 32 کاراکتری تصادفی (می‌توانید از این استفاده کنید: `change_this_key_in_production_32!!`)

### 4. تنظیم متن تعهدنامه

فایل `config.py` را باز کنید و متن تعهدنامه را در متغیر `COMMITMENT_TEXT` قرار دهید:

```python
COMMITMENT_TEXT = """
متن تعهدنامه شما اینجا قرار می‌گیرد...
"""
```

### 5. اجرای ربات

در ترمینال در پوشه پروژه:

```bash
python bot.py
```

یا:

```bash
python3 bot.py
```

اگر همه چیز درست باشد، پیام زیر را می‌بینید:

```
INFO - Bot is starting...
```

## تست ربات

1. در تلگرام به ربات خود پیام دهید: `/start`
2. باید پیام خوشامدگویی با دو دکمه نمایش داده شود

## عیب‌یابی

### خطای اتصال به دیتابیس:
- مطمئن شوید PostgreSQL در حال اجرا است
- `DATABASE_URL` را بررسی کنید
- نام دیتابیس و رمز عبور را بررسی کنید

### خطای BOT_TOKEN:
- توکن را از BotFather دوباره دریافت کنید
- مطمئن شوید توکن در `.env` درست وارد شده

### خطای ModuleNotFoundError:
- وابستگی‌ها را دوباره نصب کنید: `pip install -r requirements.txt`

## توقف ربات

برای توقف ربات، `Ctrl+C` را در ترمینال فشار دهید.

