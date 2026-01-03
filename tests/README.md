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

برای اجرای تست کارمزد فروش:

```bash
pytest tests/test_sell_commission.py -v -s
```

برای اجرای تست لاگ تراکنش‌ها:

```bash
pytest tests/test_transaction_logs.py -v -s
```

## تست موافقت‌نامه

فایل `test_agreement_flow.py` شامل تست‌های زیر است:

1. **test_agreement_not_accepted_initially**: بررسی اینکه در ابتدا موافقت‌نامه تایید نشده است
2. **test_accept_agreement_saves_to_database**: بررسی ذخیره شدن تایید در دیتابیس
3. **test_handle_accept_agreement_flow**: بررسی جریان کامل تایید موافقت‌نامه
4. **test_agreement_check_after_acceptance**: بررسی که پس از تایید، کاربر به مرحله بعدی می‌رود
5. **test_callback_after_agreement_acceptance**: بررسی کارکرد callback های دیگر پس از تایید
6. **test_agreement_persistence**: بررسی ماندگاری تایید در دیتابیس

## تست کارمزد فروش

فایل `test_sell_commission.py` شامل تست‌های زیر است:

1. **test_commission_calculation**: بررسی محاسبه کارمزد ۱٪
2. **test_balance_deduction_with_commission**: بررسی کسر موجودی با در نظر گرفتن کارمزد
3. **test_transaction_record_with_fee**: بررسی ثبت تراکنش با fee
4. **test_complete_sell_process**: بررسی فرآیند کامل فروش با کسر کارمزد
5. **test_multiple_sells_with_commission**: بررسی چند فروش متوالی با کسر کارمزد
6. **test_sell_max_amount_with_commission**: بررسی فروش حداکثر مقدار با در نظر گرفتن کارمزد

## تست لاگ تراکنش‌ها

فایل `test_transaction_logs.py` شامل تست‌های زیر است:

1. **test_create_transaction_log_basic**: بررسی ایجاد لاگ تراکنش پایه
2. **test_create_transaction_log_with_username_from_db**: بررسی دریافت username از دیتابیس
3. **test_transaction_log_buy**: بررسی لاگ تراکنش خرید با user_id و username
4. **test_transaction_log_send**: بررسی لاگ تراکنش ارسال با اطلاعات کامل حساب مقصد و مبلغ
5. **test_transaction_log_sell_with_sheba**: بررسی لاگ تراکنش فروش با شماره شبا
6. **test_transaction_log_timestamp**: بررسی ثبت تاریخ و زمان دقیق (تا دقیقه)
7. **test_multiple_transaction_logs**: بررسی ایجاد چند لاگ تراکنش متوالی
8. **test_transaction_log_different_users**: بررسی لاگ‌های تراکنش کاربران مختلف
9. **test_transaction_log_failed_status**: بررسی لاگ تراکنش ناموفق
10. **test_transaction_log_all_fields**: بررسی تمام فیلدهای لاگ (user_id, username, مبلغ، کارمزد، شبا، تاریخ و زمان)

این تست‌ها بررسی می‌کنند که تمام تراکنش‌ها (خرید، ارسال، فروش) با جزئیات کامل در جدول `transaction_logs` ثبت می‌شوند.

## نکات مهم

- قبل از اجرای تست‌ها، مطمئن شوید که دیتابیس PostgreSQL در حال اجرا است
- متغیرهای محیطی در فایل `.env` باید تنظیم شده باشند
- تست‌ها از دیتابیس واقعی استفاده می‌کنند، پس مراقب باشید
