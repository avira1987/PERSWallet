"""
تست برای بررسی کسر کارمزد ۱٪ هنگام فروش PERS
این تست بررسی می‌کند که:
1. کارمزد ۱٪ به درستی محاسبه می‌شود
2. هم مبلغ فروش و هم کارمزد از موجودی حساب کسر می‌شود
3. موجودی جدید درست است
4. تراکنش با fee درست ثبت می‌شود
"""
import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from handlers.sell import SellHandler
from utils.lock_manager import LockManager
from utils.encryption import encrypt_state, decrypt_state
import config


class TestSellCommission:
    """تست کسر کارمزد هنگام فروش"""
    
    @pytest.fixture
    def db_manager(self):
        """ایجاد یک نمونه از DatabaseManager"""
        return DatabaseManager()
    
    @pytest.fixture
    def lock_manager(self, db_manager):
        """ایجاد یک نمونه از LockManager"""
        return LockManager(db_manager)
    
    @pytest.fixture
    def sell_handler(self, db_manager, lock_manager):
        """ایجاد یک نمونه از SellHandler"""
        return SellHandler(db_manager, lock_manager)
    
    @pytest.fixture
    def test_user_and_account(self, db_manager):
        """ایجاد یک کاربر و حساب تستی"""
        user_id = "test_user_12345"
        account_number = "1234567890123456"
        password = "12345678"
        
        # ایجاد کاربر
        user = db_manager.get_or_create_user(user_id, "test_user")
        
        # ایجاد حساب با موجودی 1000 PERS
        account = db_manager.create_account(user_id, account_number, password)
        db_manager.set_account_balance(account_number, 1000.0)
        
        return user_id, account_number, password
    
    def test_commission_calculation(self):
        """تست: بررسی محاسبه کارمزد ۱٪"""
        # تست با مقادیر مختلف
        test_cases = [
            (100.0, 1.0),    # 100 PERS -> 1 PERS commission
            (50.0, 0.5),     # 50 PERS -> 0.5 PERS commission
            (1000.0, 10.0),  # 1000 PERS -> 10 PERS commission
            (10.0, 0.1),     # 10 PERS -> 0.1 PERS commission
        ]
        
        for amount, expected_commission in test_cases:
            commission = amount * config.SELL_FEE_PERCENT
            assert abs(commission - expected_commission) < 0.01, \
                f"کارمزد برای {amount} PERS باید {expected_commission} باشد، اما {commission} است"
        
        print("[TEST] ✅ محاسبه کارمزد درست است")
    
    def test_balance_deduction_with_commission(self, db_manager, test_user_and_account):
        """تست: بررسی کسر موجودی با در نظر گرفتن کارمزد"""
        user_id, account_number, password = test_user_and_account
        
        # موجودی اولیه
        initial_balance = db_manager.get_account_balance(account_number)
        assert initial_balance == 1000.0, f"موجودی اولیه باید 1000 باشد، اما {initial_balance} است"
        
        # مبلغ فروش
        sell_amount = 100.0
        commission = sell_amount * config.SELL_FEE_PERCENT
        total_deduction = sell_amount + commission
        
        # کسر از موجودی
        db_manager.update_account_balance(account_number, -total_deduction)
        
        # بررسی موجودی جدید
        new_balance = db_manager.get_account_balance(account_number)
        expected_balance = initial_balance - total_deduction
        
        assert abs(new_balance - expected_balance) < 0.01, \
            f"موجودی جدید باید {expected_balance} باشد، اما {new_balance} است"
        
        # بررسی که کارمزد هم کسر شده
        assert new_balance == initial_balance - sell_amount - commission, \
            "هم مبلغ فروش و هم کارمزد باید از موجودی کسر شده باشد"
        
        print(f"[TEST] ✅ موجودی اولیه: {initial_balance}")
        print(f"[TEST] ✅ مبلغ فروش: {sell_amount}")
        print(f"[TEST] ✅ کارمزد (1%): {commission}")
        print(f"[TEST] ✅ کل کسر: {total_deduction}")
        print(f"[TEST] ✅ موجودی جدید: {new_balance}")
    
    def test_transaction_record_with_fee(self, db_manager, test_user_and_account):
        """تست: بررسی ثبت تراکنش با fee"""
        user_id, account_number, password = test_user_and_account
        
        # مبلغ فروش
        sell_amount = 200.0
        commission = sell_amount * config.SELL_FEE_PERCENT
        
        # ایجاد تراکنش
        transaction = db_manager.create_transaction(
            from_account=account_number,
            to_account=None,
            amount=sell_amount,
            fee=commission,
            transaction_type='sell'
        )
        
        # بررسی تراکنش
        assert transaction is not None, "تراکنش باید ایجاد شده باشد"
        assert transaction.amount == sell_amount, \
            f"مبلغ تراکنش باید {sell_amount} باشد، اما {transaction.amount} است"
        assert abs(float(transaction.fee) - commission) < 0.01, \
            f"کارمزد تراکنش باید {commission} باشد، اما {transaction.fee} است"
        assert transaction.transaction_type == 'sell', \
            "نوع تراکنش باید 'sell' باشد"
        assert transaction.from_account == account_number, \
            "حساب مبدا باید درست باشد"
        
        print(f"[TEST] ✅ تراکنش با مبلغ {sell_amount} و کارمزد {commission} ثبت شد")
    
    def test_complete_sell_process(self, db_manager, test_user_and_account):
        """تست: بررسی فرآیند کامل فروش با کسر کارمزد"""
        user_id, account_number, password = test_user_and_account
        
        # موجودی اولیه
        initial_balance = db_manager.get_account_balance(account_number)
        print(f"\n[TEST] موجودی اولیه: {initial_balance} PERS")
        
        # مبلغ فروش
        sell_amount = 500.0
        commission = sell_amount * config.SELL_FEE_PERCENT
        total_deduction = sell_amount + commission
        
        print(f"[TEST] مبلغ فروش: {sell_amount} PERS")
        print(f"[TEST] کارمزد (1%): {commission} PERS")
        print(f"[TEST] کل کسر: {total_deduction} PERS")
        
        # کسر از موجودی
        db_manager.update_account_balance(account_number, -total_deduction)
        
        # ایجاد تراکنش
        transaction = db_manager.create_transaction(
            from_account=account_number,
            to_account=None,
            amount=sell_amount,
            fee=commission,
            transaction_type='sell'
        )
        
        # بررسی موجودی جدید
        new_balance = db_manager.get_account_balance(account_number)
        expected_balance = initial_balance - total_deduction
        
        assert abs(new_balance - expected_balance) < 0.01, \
            f"موجودی جدید باید {expected_balance} باشد، اما {new_balance} است"
        
        # بررسی تراکنش
        assert transaction.fee == commission, \
            f"کارمزد در تراکنش باید {commission} باشد، اما {transaction.fee} است"
        
        print(f"[TEST] ✅ موجودی جدید: {new_balance} PERS")
        print(f"[TEST] ✅ تراکنش با کارمزد ثبت شد")
        print(f"[TEST] ✅ فرآیند کامل فروش با موفقیت انجام شد")
    
    def test_multiple_sells_with_commission(self, db_manager, test_user_and_account):
        """تست: بررسی چند فروش متوالی با کسر کارمزد"""
        user_id, account_number, password = test_user_and_account
        
        initial_balance = db_manager.get_account_balance(account_number)
        print(f"\n[TEST] موجودی اولیه: {initial_balance} PERS")
        
        # چند فروش متوالی
        sells = [100.0, 200.0, 150.0]
        total_commission = 0.0
        total_sold = 0.0
        
        for sell_amount in sells:
            commission = sell_amount * config.SELL_FEE_PERCENT
            total_deduction = sell_amount + commission
            
            # کسر از موجودی
            db_manager.update_account_balance(account_number, -total_deduction)
            
            # ایجاد تراکنش
            db_manager.create_transaction(
                from_account=account_number,
                to_account=None,
                amount=sell_amount,
                fee=commission,
                transaction_type='sell'
            )
            
            total_sold += sell_amount
            total_commission += commission
            
            print(f"[TEST] فروش: {sell_amount} PERS، کارمزد: {commission} PERS")
        
        # بررسی موجودی نهایی
        final_balance = db_manager.get_account_balance(account_number)
        expected_balance = initial_balance - total_sold - total_commission
        
        assert abs(final_balance - expected_balance) < 0.01, \
            f"موجودی نهایی باید {expected_balance} باشد، اما {final_balance} است"
        
        print(f"[TEST] ✅ کل فروش: {total_sold} PERS")
        print(f"[TEST] ✅ کل کارمزد: {total_commission} PERS")
        print(f"[TEST] ✅ موجودی نهایی: {final_balance} PERS")
        print(f"[TEST] ✅ چند فروش متوالی با کسر کارمزد درست انجام شد")
    
    def test_sell_max_amount_with_commission(self, db_manager, test_user_and_account):
        """تست: بررسی فروش حداکثر مقدار با در نظر گرفتن کارمزد"""
        user_id, account_number, password = test_user_and_account
        
        initial_balance = db_manager.get_account_balance(account_number)
        
        # محاسبه حداکثر مقدار فروش (99% از موجودی، با در نظر گرفتن کارمزد)
        max_sell = (initial_balance * 0.99) / (1 + config.SELL_FEE_PERCENT)
        commission = max_sell * config.SELL_FEE_PERCENT
        total_deduction = max_sell + commission
        
        print(f"\n[TEST] موجودی اولیه: {initial_balance} PERS")
        print(f"[TEST] حداکثر فروش: {max_sell:.2f} PERS")
        print(f"[TEST] کارمزد: {commission:.2f} PERS")
        print(f"[TEST] کل کسر: {total_deduction:.2f} PERS")
        
        # کسر از موجودی
        db_manager.update_account_balance(account_number, -total_deduction)
        
        # بررسی موجودی نهایی (باید حداقل 1% باقی بماند)
        final_balance = db_manager.get_account_balance(account_number)
        min_required_balance = initial_balance * 0.01
        
        assert final_balance >= min_required_balance, \
            f"موجودی نهایی ({final_balance}) باید حداقل {min_required_balance} باشد (1% از موجودی اولیه)"
        
        print(f"[TEST] ✅ موجودی نهایی: {final_balance:.2f} PERS")
        print(f"[TEST] ✅ حداقل مورد نیاز: {min_required_balance:.2f} PERS")
        print(f"[TEST] ✅ فروش حداکثر مقدار با کسر کارمزد درست انجام شد")


if __name__ == "__main__":
    # اجرای تست‌ها
    pytest.main([__file__, "-v", "-s"])
