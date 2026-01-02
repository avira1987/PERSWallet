# تست‌های ربات

این پوشه شامل تست‌های واحد برای ربات پرس بات است.

## نصب وابستگی‌ها

```bash
pip install -r ../requirements.txt
```

## اجرای تست‌ها

برای اجرای همه تست‌ها:

```bash
pytest tests/ -v
```

برای اجرای تست خاص موافقت‌نامه:

```bash
pytest tests/test_agreement_flow.py -v -s
```

## تست موافقت‌نامه

فایل `test_agreement_flow.py` شامل تست‌های زیر است:

1. **test_agreement_not_accepted_initially**: بررسی اینکه در ابتدا موافقت‌نامه تایید نشده است
2. **test_accept_agreement_saves_to_database**: بررسی ذخیره شدن تایید در دیتابیس
3. **test_handle_accept_agreement_flow**: بررسی جریان کامل تایید موافقت‌نامه
4. **test_agreement_check_after_acceptance**: بررسی که پس از تایید، کاربر به مرحله بعدی می‌رود
5. **test_callback_after_agreement_acceptance**: بررسی کارکرد callback های دیگر پس از تایید
6. **test_agreement_persistence**: بررسی ماندگاری تایید در دیتابیس

## نکات مهم

- قبل از اجرای تست‌ها، مطمئن شوید که دیتابیس PostgreSQL در حال اجرا است
- متغیرهای محیطی در فایل `.env` باید تنظیم شده باشند
- تست‌ها از دیتابیس واقعی استفاده می‌کنند، پس مراقب باشید
