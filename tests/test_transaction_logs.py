"""
تست برای سیستم لاگ‌گذاری کامل تراکنش‌ها
این تست بررسی می‌کند که:
1. تمام تراکنش‌ها (خرید، ارسال، فروش) با جزئیات کامل لاگ می‌شوند
2. user_id و username به درستی ثبت می‌شوند
3. شماره شبا برای فروش ثبت می‌شود
4. تاریخ و زمان دقیق ثبت می‌شود
5. تمام اطلاعات تراکنش (مبلغ، کارمزد، حساب مبدأ/مقصد) ثبت می‌شود
"""
import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import TransactionLog, Transaction
from handlers.buy import BuyHandler
from handlers.send import SendHandler
from handlers.sell import SellHandler
from utils.lock_manager import LockManager
from utils.encryption import encrypt_state, decrypt_state
import config


class TestTransactionLogs:
    """تست سیستم لاگ‌گذاری تراکنش‌ها"""
    
    @pytest.fixture
    def db_manager(self):
        """ایجاد یک نمونه از DatabaseManager"""
        return DatabaseManager()
    
    @pytest.fixture
    def lock_manager(self, db_manager):
        """ایجاد یک نمونه از LockManager"""
        return LockManager(db_manager)
    
    @pytest.fixture
    def test_user_and_account(self, db_manager):
        """ایجاد یک کاربر و حساب تستی"""
        user_id = "test_log_user_123"
        username = "test_log_user"
        account_number = "1111111111111111"
        password = "12345678"
        
        # ایجاد کاربر
        user = db_manager.get_or_create_user(user_id, username)
        
        # ایجاد حساب با موجودی 1000 PERS
        account = db_manager.create_account(user_id, account_number, password)
        db_manager.set_account_balance(account_number, 1000.0)
        
        return user_id, username, account_number, password
    
    @pytest.fixture
    def test_user2_and_account(self, db_manager):
        """ایجاد کاربر دوم و حساب برای تست ارسال"""
        user_id = "test_log_user_456"
        username = "test_log_user2"
        account_number = "2222222222222222"
        password = "12345678"
        
        # ایجاد کاربر
        user = db_manager.get_or_create_user(user_id, username)
        
        # ایجاد حساب
        account = db_manager.create_account(user_id, account_number, password)
        db_manager.set_account_balance(account_number, 500.0)
        
        return user_id, username, account_number, password
    
    def test_create_transaction_log_basic(self, db_manager, test_user_and_account):
        """تست: ایجاد لاگ تراکنش پایه"""
        user_id, username, account_number, password = test_user_and_account
        
        # ایجاد لاگ تراکنش
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='buy',
            from_account=None,
            to_account=account_number,
            amount=100.0,
            fee=0.0,
            sheba=None,
            status='success'
        )
        
        # بررسی لاگ
        assert log is not None, "لاگ باید ایجاد شده باشد"
        assert log.user_id == user_id, f"user_id باید {user_id} باشد"
        assert log.username == username, f"username باید {username} باشد"
        assert log.transaction_type == 'buy', "نوع تراکنش باید buy باشد"
        assert log.to_account == account_number, "حساب مقصد باید درست باشد"
        assert float(log.amount) == 100.0, "مبلغ باید 100 باشد"
        assert float(log.fee) == 0.0, "کارمزد باید 0 باشد"
        assert log.status == 'success', "وضعیت باید success باشد"
        assert log.created_at is not None, "تاریخ ایجاد باید تنظیم شده باشد"
        
        print(f"[TEST] ✅ لاگ تراکنش با ID {log.id} ایجاد شد")
        print(f"[TEST] ✅ User ID: {log.user_id}, Username: {log.username}")
        print(f"[TEST] ✅ تاریخ ایجاد: {log.created_at}")
    
    def test_create_transaction_log_with_username_from_db(self, db_manager, test_user_and_account):
        """تست: دریافت username از دیتابیس اگر ارائه نشده باشد"""
        user_id, username, account_number, password = test_user_and_account
        
        # ایجاد لاگ بدون username (باید از دیتابیس گرفته شود)
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=None,  # None - باید از دیتابیس گرفته شود
            transaction_type='buy',
            from_account=None,
            to_account=account_number,
            amount=50.0,
            fee=0.0
        )
        
        # بررسی که username از دیتابیس گرفته شده
        assert log.username == username, f"username باید از دیتابیس گرفته شده و {username} باشد"
        
        print(f"[TEST] ✅ username از دیتابیس گرفته شد: {log.username}")
    
    def test_transaction_log_buy(self, db_manager, test_user_and_account):
        """تست: لاگ تراکنش خرید"""
        user_id, username, account_number, password = test_user_and_account
        
        # ایجاد تراکنش
        transaction = db_manager.create_transaction(
            from_account=None,
            to_account=account_number,
            amount=200.0,
            fee=0.0,
            transaction_type='buy'
        )
        
        # ایجاد لاگ
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='buy',
            from_account=None,
            to_account=account_number,
            amount=200.0,
            fee=0.0,
            transaction_id=transaction.id
        )
        
        # بررسی لاگ خرید
        assert log.transaction_type == 'buy', "نوع تراکنش باید buy باشد"
        assert log.from_account is None, "حساب مبدأ باید None باشد"
        assert log.to_account == account_number, "حساب مقصد باید درست باشد"
        assert float(log.amount) == 200.0, "مبلغ باید 200 باشد"
        assert float(log.fee) == 0.0, "کارمزد خرید باید 0 باشد"
        assert log.sheba is None, "شبا برای خرید باید None باشد"
        assert log.transaction_id == transaction.id, "transaction_id باید درست باشد"
        
        print(f"[TEST] ✅ لاگ خرید ثبت شد:")
        print(f"[TEST]    - User: {log.user_id} (@{log.username})")
        print(f"[TEST]    - مبلغ: {log.amount} PERS")
        print(f"[TEST]    - حساب مقصد: {log.to_account}")
        print(f"[TEST]    - تاریخ: {log.created_at}")
    
    def test_transaction_log_send(self, db_manager, test_user_and_account, test_user2_and_account):
        """تست: لاگ تراکنش ارسال"""
        user_id1, username1, account_number1, password1 = test_user_and_account
        user_id2, username2, account_number2, password2 = test_user2_and_account
        
        amount = 150.0
        fee = min(amount * config.TRANSACTION_FEE_PERCENT, config.MAX_TRANSACTION_FEE)
        
        # ایجاد تراکنش
        transaction = db_manager.create_transaction(
            from_account=account_number1,
            to_account=account_number2,
            amount=amount,
            fee=fee,
            transaction_type='send'
        )
        
        # ایجاد لاگ
        log = db_manager.create_transaction_log(
            user_id=user_id1,
            username=username1,
            transaction_type='send',
            from_account=account_number1,
            to_account=account_number2,
            amount=amount,
            fee=fee,
            transaction_id=transaction.id
        )
        
        # بررسی لاگ ارسال
        assert log.transaction_type == 'send', "نوع تراکنش باید send باشد"
        assert log.from_account == account_number1, "حساب مبدأ باید درست باشد"
        assert log.to_account == account_number2, "حساب مقصد باید درست باشد"
        assert float(log.amount) == amount, f"مبلغ باید {amount} باشد"
        assert abs(float(log.fee) - fee) < 0.01, f"کارمزد باید {fee} باشد"
        assert log.sheba is None, "شبا برای ارسال باید None باشد"
        assert log.user_id == user_id1, "user_id باید کاربر فرستنده باشد"
        
        print(f"[TEST] ✅ لاگ ارسال ثبت شد:")
        print(f"[TEST]    - User: {log.user_id} (@{log.username})")
        print(f"[TEST]    - از حساب: {log.from_account}")
        print(f"[TEST]    - به حساب: {log.to_account}")
        print(f"[TEST]    - مبلغ: {log.amount} PERS")
        print(f"[TEST]    - کارمزد: {log.fee} PERS")
        print(f"[TEST]    - تاریخ: {log.created_at}")
    
    def test_transaction_log_sell_with_sheba(self, db_manager, test_user_and_account):
        """تست: لاگ تراکنش فروش با شماره شبا"""
        user_id, username, account_number, password = test_user_and_account
        
        amount = 300.0
        commission = amount * config.SELL_FEE_PERCENT
        sheba = "IR123456789012345678901234"
        
        # ایجاد تراکنش
        transaction = db_manager.create_transaction(
            from_account=account_number,
            to_account=None,
            amount=amount,
            fee=commission,
            transaction_type='sell'
        )
        
        # ایجاد لاگ
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='sell',
            from_account=account_number,
            to_account=None,
            amount=amount,
            fee=commission,
            sheba=sheba,
            transaction_id=transaction.id
        )
        
        # بررسی لاگ فروش
        assert log.transaction_type == 'sell', "نوع تراکنش باید sell باشد"
        assert log.from_account == account_number, "حساب مبدأ باید درست باشد"
        assert log.to_account is None, "حساب مقصد باید None باشد"
        assert float(log.amount) == amount, f"مبلغ باید {amount} باشد"
        assert abs(float(log.fee) - commission) < 0.01, f"کارمزد باید {commission} باشد"
        assert log.sheba == sheba, f"شبا باید {sheba} باشد"
        assert log.user_id == user_id, "user_id باید درست باشد"
        
        print(f"[TEST] ✅ لاگ فروش با شبا ثبت شد:")
        print(f"[TEST]    - User: {log.user_id} (@{log.username})")
        print(f"[TEST]    - از حساب: {log.from_account}")
        print(f"[TEST]    - مبلغ: {log.amount} PERS")
        print(f"[TEST]    - کارمزد: {log.fee} PERS")
        print(f"[TEST]    - شبا: {log.sheba}")
        print(f"[TEST]    - تاریخ: {log.created_at}")
    
    def test_transaction_log_timestamp(self, db_manager, test_user_and_account):
        """تست: بررسی ثبت تاریخ و زمان دقیق"""
        user_id, username, account_number, password = test_user_and_account
        
        before_time = datetime.utcnow()
        
        # ایجاد لاگ
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='buy',
            from_account=None,
            to_account=account_number,
            amount=100.0,
            fee=0.0
        )
        
        after_time = datetime.utcnow()
        
        # بررسی تاریخ و زمان
        assert log.created_at is not None, "تاریخ ایجاد باید تنظیم شده باشد"
        assert before_time <= log.created_at <= after_time, \
            "تاریخ ایجاد باید بین قبل و بعد از ایجاد لاگ باشد"
        
        # بررسی فرمت تاریخ (باید datetime باشد)
        assert isinstance(log.created_at, datetime), "created_at باید از نوع datetime باشد"
        
        # بررسی اینکه شامل تاریخ و زمان (تا دقیقه) است
        time_str = log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        assert len(time_str) > 0, "فرمت تاریخ باید معتبر باشد"
        
        print(f"[TEST] ✅ تاریخ و زمان ثبت شد: {log.created_at}")
        print(f"[TEST] ✅ فرمت کامل: {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def test_multiple_transaction_logs(self, db_manager, test_user_and_account):
        """تست: ایجاد چند لاگ تراکنش متوالی"""
        user_id, username, account_number, password = test_user_and_account
        
        logs = []
        
        # چند تراکنش مختلف
        transactions_data = [
            ('buy', None, account_number, 100.0, 0.0, None),
            ('buy', None, account_number, 50.0, 0.0, None),
            ('send', account_number, "9999999999999999", 75.0, 0.75, None),
        ]
        
        for trans_type, from_acc, to_acc, amount, fee, sheba in transactions_data:
            transaction = db_manager.create_transaction(
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                fee=fee,
                transaction_type=trans_type
            )
            
            log = db_manager.create_transaction_log(
                user_id=user_id,
                username=username,
                transaction_type=trans_type,
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                fee=fee,
                sheba=sheba,
                transaction_id=transaction.id
            )
            
            logs.append(log)
        
        # بررسی تعداد لاگ‌ها
        assert len(logs) == 3, "باید 3 لاگ ایجاد شده باشد"
        
        # بررسی لاگ‌ها
        assert logs[0].transaction_type == 'buy', "لاگ اول باید buy باشد"
        assert logs[1].transaction_type == 'buy', "لاگ دوم باید buy باشد"
        assert logs[2].transaction_type == 'send', "لاگ سوم باید send باشد"
        
        # بررسی که همه مربوط به همان کاربر هستند
        for log in logs:
            assert log.user_id == user_id, "همه لاگ‌ها باید مربوط به همان کاربر باشند"
            assert log.username == username, "همه لاگ‌ها باید همان username را داشته باشند"
        
        print(f"[TEST] ✅ {len(logs)} لاگ تراکنش ایجاد شد")
        for i, log in enumerate(logs, 1):
            print(f"[TEST]    {i}. {log.transaction_type}: {log.amount} PERS - {log.created_at}")
    
    def test_transaction_log_different_users(self, db_manager, test_user_and_account, test_user2_and_account):
        """تست: لاگ‌های تراکنش کاربران مختلف"""
        user_id1, username1, account_number1, password1 = test_user_and_account
        user_id2, username2, account_number2, password2 = test_user2_and_account
        
        # لاگ برای کاربر اول
        log1 = db_manager.create_transaction_log(
            user_id=user_id1,
            username=username1,
            transaction_type='buy',
            from_account=None,
            to_account=account_number1,
            amount=100.0,
            fee=0.0
        )
        
        # لاگ برای کاربر دوم
        log2 = db_manager.create_transaction_log(
            user_id=user_id2,
            username=username2,
            transaction_type='buy',
            from_account=None,
            to_account=account_number2,
            amount=200.0,
            fee=0.0
        )
        
        # بررسی تفاوت کاربران
        assert log1.user_id != log2.user_id, "user_id لاگ‌ها باید متفاوت باشند"
        assert log1.username != log2.username, "username لاگ‌ها باید متفاوت باشند"
        assert log1.to_account != log2.to_account, "حساب‌های مقصد باید متفاوت باشند"
        
        print(f"[TEST] ✅ لاگ کاربر 1: {log1.user_id} (@{log1.username})")
        print(f"[TEST] ✅ لاگ کاربر 2: {log2.user_id} (@{log2.username})")
    
    def test_transaction_log_failed_status(self, db_manager, test_user_and_account):
        """تست: لاگ تراکنش ناموفق"""
        user_id, username, account_number, password = test_user_and_account
        
        # ایجاد لاگ با وضعیت failed
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='send',
            from_account=account_number,
            to_account="9999999999999999",
            amount=1000.0,  # بیشتر از موجودی
            fee=10.0,
            status='failed'
        )
        
        # بررسی وضعیت
        assert log.status == 'failed', "وضعیت باید failed باشد"
        assert log.user_id == user_id, "user_id باید درست باشد"
        assert float(log.amount) == 1000.0, "مبلغ باید ثبت شده باشد"
        
        print(f"[TEST] ✅ لاگ تراکنش ناموفق ثبت شد: {log.status}")
    
    def test_transaction_log_all_fields(self, db_manager, test_user_and_account):
        """تست: بررسی تمام فیلدهای لاگ"""
        user_id, username, account_number, password = test_user_and_account
        
        transaction = db_manager.create_transaction(
            from_account=account_number,
            to_account=None,
            amount=500.0,
            fee=5.0,
            transaction_type='sell'
        )
        
        sheba = "IR987654321098765432109876"
        
        log = db_manager.create_transaction_log(
            user_id=user_id,
            username=username,
            transaction_type='sell',
            from_account=account_number,
            to_account=None,
            amount=500.0,
            fee=5.0,
            sheba=sheba,
            status='success',
            transaction_id=transaction.id
        )
        
        # بررسی تمام فیلدها
        assert log.id is not None, "id باید تنظیم شده باشد"
        assert log.user_id == user_id, "user_id باید درست باشد"
        assert log.username == username, "username باید درست باشد"
        assert log.transaction_type == 'sell', "transaction_type باید درست باشد"
        assert log.from_account == account_number, "from_account باید درست باشد"
        assert log.to_account is None, "to_account باید None باشد"
        assert float(log.amount) == 500.0, "amount باید درست باشد"
        assert float(log.fee) == 5.0, "fee باید درست باشد"
        assert log.sheba == sheba, "sheba باید درست باشد"
        assert log.status == 'success', "status باید درست باشد"
        assert log.transaction_id == transaction.id, "transaction_id باید درست باشد"
        assert log.created_at is not None, "created_at باید تنظیم شده باشد"
        
        print(f"[TEST] ✅ تمام فیلدهای لاگ بررسی شد:")
        print(f"[TEST]    - ID: {log.id}")
        print(f"[TEST]    - User ID: {log.user_id}")
        print(f"[TEST]    - Username: {log.username}")
        print(f"[TEST]    - Type: {log.transaction_type}")
        print(f"[TEST]    - From: {log.from_account}")
        print(f"[TEST]    - To: {log.to_account}")
        print(f"[TEST]    - Amount: {log.amount}")
        print(f"[TEST]    - Fee: {log.fee}")
        print(f"[TEST]    - Sheba: {log.sheba}")
        print(f"[TEST]    - Status: {log.status}")
        print(f"[TEST]    - Transaction ID: {log.transaction_id}")
        print(f"[TEST]    - Created At: {log.created_at}")


if __name__ == "__main__":
    # اجرای تست‌ها
    pytest.main([__file__, "-v", "-s"])
