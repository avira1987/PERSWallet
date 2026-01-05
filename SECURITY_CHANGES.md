# تغییرات امنیتی اعمال شده

این فایل خلاصه‌ای از تغییرات امنیتی اعمال شده در پروژه را ارائه می‌دهد.

## تغییرات انجام شده

### 1. ✅ Authentication برای رابط وب
- اضافه شدن سیستم Flask-Login برای احراز هویت
- ایجاد صفحه login (`/login`)
- تمام routes محافظت شده با `@login_required` و `@admin_required`
- فقط کاربران admin می‌توانند به پنل وب دسترسی داشته باشند

### 2. ✅ حذف کلید رمزنگاری پیش‌فرض
- `ENCRYPTION_KEY` باید در `.env` تنظیم شود
- در صورت عدم تنظیم، برنامه با خطا متوقف می‌شود
- `WEB_SECRET_KEY` نیز اجباری شده است

### 3. ✅ بهبود Encryption
- بهبود الگوریتم derive کردن کلید
- استفاده از salt بهتر برای PBKDF2

### 4. ✅ Rate Limiting
- اضافه شدن Flask-Limiter
- محدودیت درخواست برای تمام API endpoints
- پیش‌فرض: 200 درخواست در روز، 50 درخواست در ساعت

### 5. ✅ CSRF Protection
- اضافه شدن Flask-WTF برای محافظت CSRF
- تمام فرم‌ها با CSRF token محافظت می‌شوند

### 6. ✅ حذف اطلاعات حساس از لاگ‌ها
- URL دیتابیس دیگر در لاگ‌ها نمایش داده نمی‌شود
- پیام‌های خطا برای کاربر عمومی‌تر شده‌اند
- جزئیات خطا فقط در لاگ سرور ثبت می‌شوند

### 7. ✅ بهبود Session Management
- استفاده از secret key از environment variables
- تنظیمات صحیح Flask-Login

### 8. ✅ بهبود Race Conditions
- استفاده از `with_for_update()` برای PostgreSQL
- بهبود atomicity در `update_account_balance`

### 9. ✅ بهبود Error Handling
- پیام‌های خطای عمومی برای کاربران
- ثبت جزئیات خطا فقط در لاگ سرور

## تنظیمات مورد نیاز

### 1. نصب پکیج‌های جدید

```bash
pip install -r requirements.txt
```

پکیج‌های جدید:
- `Flask-WTF==1.2.1`
- `Flask-Limiter==3.5.0`

### 2. تنظیم Environment Variables

در فایل `.env` باید مقادیر زیر را تنظیم کنید:

```env
# Encryption Key (اجباری)
ENCRYPTION_KEY=your_32_byte_key_here

# Web Secret Key (اجباری)
WEB_SECRET_KEY=your_secret_key_here
```

برای تولید کلیدهای امن:

```bash
# برای ENCRYPTION_KEY (32 بایت)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# برای WEB_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. تنظیم Admin User

برای دسترسی به پنل وب، باید یک کاربر را به عنوان admin تنظیم کنید:

1. از طریق ربات تلگرام، شناسه کاربری خود را دریافت کنید
2. در دیتابیس، کاربر خود را به admin تبدیل کنید (یا از طریق API)

### 4. راه‌اندازی مجدد

پس از اعمال تغییرات:

```bash
# راه‌اندازی ربات
python bot.py

# راه‌اندازی پنل وب
python web/app.py
```

## نکات مهم

1. **اولین بار راه‌اندازی**: پس از اعمال تغییرات، برای ورود به پنل وب باید از `/login` استفاده کنید
2. **Backup**: قبل از اعمال تغییرات، از دیتابیس backup بگیرید
3. **Testing**: تغییرات را در محیط test تست کنید قبل از deployment در production

## Migration Notes

- اگر از قبل `ENCRYPTION_KEY` داشتید، نیازی به تغییر نیست
- اگر `WEB_SECRET_KEY` نداشتید، باید آن را تنظیم کنید
- کاربران موجود در دیتابیس تغییری نمی‌کنند
- فقط باید یک کاربر را به admin تبدیل کنید

## سوالات متداول

**Q: اگر ENCRYPTION_KEY را تنظیم نکنم چه می‌شود؟**
A: برنامه با خطا متوقف می‌شود و پیام راهنما نمایش داده می‌شود.

**Q: چگونه می‌توانم یک کاربر را به admin تبدیل کنم؟**
A: می‌توانید از API استفاده کنید یا مستقیماً در دیتابیس ستون `is_admin` را به `true` تنظیم کنید.

**Q: آیا تغییرات backward compatible هستند؟**
A: بله، تمام تغییرات backward compatible هستند. فقط نیاز به تنظیم environment variables دارید.
