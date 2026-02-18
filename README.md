# PERSWallet Repository

این ریپوزیتوری شامل دو پروژه است:

---

## 1. BalanceBot - ربات تلگرام PERS

ربات تلگرام برای مدیریت کیف پول PERS با قابلیت‌های خرید، فروش، ارسال و دریافت.

🔗 **لینک ریپازیتوری:** [https://github.com/avira1987/PERSWallet](https://github.com/avira1987/PERSWallet)

### درباره BalanceBot

BalanceBot یک ربات تلگرام کامل و امن برای مدیریت کیف پول ارز دیجیتال PERS است. این ربات با استفاده از Python و کتابخانه python-telegram-bot توسعه یافته و از دیتابیس PostgreSQL برای ذخیره‌سازی اطلاعات استفاده می‌کند. ربات شامل یک پنل مدیریتی وب (Flask) برای نظارت و مدیریت کاربران و تراکنش‌ها می‌باشد.

**قابلیت‌های اصلی:**
- سیستم احراز هویت و مدیریت اکانت‌ها
- انجام تراکنش‌های خرید و فروش
- ارسال و دریافت PERS بین کاربران
- تولید QR Code برای پرداخت
- گزارش‌گیری PDF از تراکنش‌ها
- پنل مدیریتی وب برای ادمین
- سیستم رمزنگاری برای امنیت داده‌ها

**نصب و اجرای BalanceBot:**
```bash
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

📚 مستندات: `SETUP.md`, `RUN.md`, `WEB_README.md`, `QUICK_START_WEB.md`

---

## 2. presWebsit - سیستم اکانتی با قابلیت شارژ

A full-stack account management system with wallet charging, payment gateway integration, user transfers, affiliate program, and admin dashboard.

### Features

- **Company Landing Page** - Beautiful RTL website with company introduction and E-Namad badge
- **Authentication** - Registration, login with Argon2 password hashing and JWT tokens
- **Two-Factor Authentication** - TOTP-based 2FA compatible with Google Authenticator & Microsoft Authenticator
- **Wallet System** - Digital wallet with balance tracking and transaction history
- **Multi-Gateway Payments** - Shaparak payment via ZarinPal, IDPay, Pay.ir, NextPay
- **User Transfers** - Send balance between users by username or phone number
- **Pro Account Charging** - Dedicated page for sending charges to pro accounts
- **Affiliate Program** - Referral system with automatic commission
- **Admin Dashboard** - Manage users, transactions, and refund requests

### Project Structure

```
presWebsit/
├── backend/          # Django REST API
│   ├── config/       # Django settings, URLs
│   ├── accounts/     # User management, 2FA
│   ├── wallet/       # Wallet & transactions
│   ├── payments/     # Payment gateway integration
│   ├── transfers/    # User-to-user transfers
│   ├── affiliates/   # Affiliate/referral program
│   └── banking/      # Refund API
├── frontend/         # React + Vite app
└── deploy/           # Deployment scripts
```

### Setup presWebsit

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```
