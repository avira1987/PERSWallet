# راهنمای تست‌های بخش مدیریت کاربران

این فایل شامل تست‌های جامع برای بخش مدیریت کاربران است که مشکلات کند لود شدن و دکمه‌های غیرفعال را بررسی می‌کند.

## ساختار تست‌ها

### 1. تست‌های API (`test_user_management_api.py`)
- تست بارگذاری کاربران (performance)
- تست عملکرد دکمه‌ها (lock, unlock, delete, admin)
- تست فیلتر و جستجو
- تست جزئیات کاربر

### 2. تست‌های Frontend (`test_user_management_frontend.py`)
- تست وجود المان‌های HTML
- تست وجود JavaScript functions
- تست وجود Modal ها

### 3. تست‌های Integration (`test_user_management_integration.py`)
- تست جریان کامل مدیریت کاربر
- تست عملکرد همزمان
- تست عملکرد با تعداد زیاد کاربر

## نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

## اجرای تست‌ها

### اجرای همه تست‌ها:
```bash
pytest tests/
```

### اجرای تست‌های خاص:
```bash
# فقط تست‌های API
pytest tests/test_user_management_api.py

# فقط تست‌های performance
pytest tests/ -m performance

# فقط تست‌های integration
pytest tests/ -m integration
```

### اجرا با جزئیات بیشتر:
```bash
pytest tests/ -v
```

### اجرا با coverage:
```bash
pytest tests/ --cov=web --cov=database
```

## تست‌های Performance

تست‌های performance بررسی می‌کنند که:
- بارگذاری کاربران در کمتر از 1 ثانیه انجام شود
- بارگذاری همزمان چندین درخواست مشکلی ایجاد نکند
- با تعداد زیاد کاربر (100+) نیز عملکرد خوب باشد

## تست‌های دکمه‌ها

تست‌های دکمه‌ها بررسی می‌کنند که:
- دکمه قفل کردن کاربر کار می‌کند
- دکمه باز کردن قفل کاربر کار می‌کند
- دکمه حذف کاربر کار می‌کند
- دکمه تبدیل به ادمین کار می‌کند
- دکمه حذف دسترسی ادمین کار می‌کند

## مشکلات شناسایی شده

### 1. کند لود شدن
- تست‌ها بررسی می‌کنند که API در کمتر از 1 ثانیه پاسخ دهد
- تست‌های همزمان برای بررسی race conditions

### 2. دکمه‌های غیرفعال
- تست‌ها بررسی می‌کنند که همه endpoint های API به درستی کار می‌کنند
- تست‌ها بررسی می‌کنند که JavaScript functions موجود هستند

## عیب‌یابی

اگر تست‌ها fail شوند:

1. مطمئن شوید که همه وابستگی‌ها نصب شده‌اند
2. بررسی کنید که دیتابیس تست به درستی تنظیم شده است
3. لاگ‌های خطا را بررسی کنید

## افزودن تست جدید

برای افزودن تست جدید:

1. فایل تست مناسب را انتخاب کنید (API, Frontend, یا Integration)
2. یک متد جدید با نام `test_...` اضافه کنید
3. از fixture های موجود استفاده کنید (`test_db`, `logged_in_admin`, etc.)
4. تست را اجرا کنید و مطمئن شوید که pass می‌شود

## مثال تست

```python
def test_new_feature(self, logged_in_admin, test_db):
    """Test new feature"""
    response = logged_in_admin.get('/api/users')
    assert response.status_code == 200
    data = json.loads(response.data)
    # Your assertions here
```
