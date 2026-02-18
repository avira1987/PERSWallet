# راهنمای سریع اجرای ربات

## مراحل اجرا (خلاصه)

### 1️⃣ نصب وابستگی‌ها

```powershell
pip install -r requirements.txt
```

### 2️⃣ ایجاد فایل .env

فایل `.env.example` را کپی کنید و نام آن را به `.env` تغییر دهید، سپس مقادیر را پر کنید:

```env
BOT_TOKEN=توکن_ربات_از_BotFather
ADMIN_USER_ID=شماره_کاربری_شما
DATABASE_URL=postgresql://postgres:رمز_عبور@localhost:5432/balancebot
ENCRYPTION_KEY=یک_رشته_32_کاراکتری_تصادفی
```

**نحوه دریافت:**

- **BOT_TOKEN**: به [@BotFather](https://t.me/BotFather) پیام دهید و `/newbot` بزنید
- **ADMIN_USER_ID**: به [@userinfobot](https://t.me/userinfobot) پیام دهید
- **DATABASE_URL**: بعد از نصب PostgreSQL، دیتابیس `balancebot` را بسازید
- **ENCRYPTION_KEY**: یک رشته 32 کاراکتری مثل: `change_this_key_in_production_32!!`

### 3️⃣ راه‌اندازی PostgreSQL

اگر PostgreSQL نصب ندارید:
1. از [اینجا](https://www.postgresql.org/download/windows/) دانلود کنید
2. نصب کنید و رمز عبور `postgres` را یادداشت کنید
3. دیتابیس بسازید:

```sql
CREATE DATABASE balancebot;
```

### 4️⃣ اجرای ربات

```powershell
python bot.py
```

اگر همه چیز درست باشد، پیام `Bot is starting...` را می‌بینید.

### 5️⃣ تست

در تلگرام به ربات خود `/start` بزنید.

---

## عیب‌یابی سریع

| مشکل | راه حل |
|------|--------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` را دوباره اجرا کنید |
| خطای دیتابیس | PostgreSQL را اجرا کنید و `DATABASE_URL` را بررسی کنید |
| خطای BOT_TOKEN | توکن را از BotFather دوباره دریافت کنید |
| خطای ENCRYPTION_KEY | مطمئن شوید 32 کاراکتر است |

---

برای راهنمای کامل‌تر، فایل `SETUP.md` را مطالعه کنید.

