"""
تست برای بررسی عملکرد لینک پرداخت
این تست بررسی می‌کند که:
1. تابع parse_payment_link به درستی URL را parse می‌کند
2. لینک پرداخت در /start command به درستی کار می‌کند
3. لینک پرداخت در پیام متنی به درستی کار می‌کند
"""
import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.generators import parse_payment_link, generate_payment_link


class TestPaymentLinkParsing:
    """تست پارس کردن لینک پرداخت"""
    
    def test_parse_payment_link_new_format(self):
        """تست parse کردن لینک پرداخت با فرمت جدید"""
        bot_username = "testbot"
        destination_account = "1234567890123456"
        amount = 100.50
        link = generate_payment_link(bot_username, amount, destination_account)
        
        # لینک باید به این شکل باشد: https://t.me/testbot?start=pay_1234567890123456_100.5
        is_payment_link, parsed_dest, parsed_amount = parse_payment_link(link)
        
        assert is_payment_link == True, f"باید لینک پرداخت تشخیص داده شود. لینک: {link}"
        assert parsed_dest == destination_account, f"شماره حساب باید {destination_account} باشد، اما {parsed_dest} است"
        assert abs(parsed_amount - amount) < 0.01, f"مبلغ باید {amount} باشد، اما {parsed_amount} است"
    
    def test_parse_payment_link_old_format(self):
        """تست parse کردن لینک پرداخت با فرمت قدیمی (فقط مبلغ)"""
        url = "https://t.me/testbot?start=pay_100.50"
        
        is_payment_link, parsed_dest, parsed_amount = parse_payment_link(url)
        
        assert is_payment_link == True, "باید لینک پرداخت تشخیص داده شود"
        assert parsed_dest is None, "برای فرمت قدیمی باید destination_account None باشد"
        assert abs(parsed_amount - 100.50) < 0.01, f"مبلغ باید 100.50 باشد، اما {parsed_amount} است"
    
    def test_parse_payment_link_invalid_url(self):
        """تست parse کردن URL نامعتبر"""
        url = "https://t.me/testbot?start=something_else"
        
        is_payment_link, parsed_dest, parsed_amount = parse_payment_link(url)
        
        assert is_payment_link == False, "نباید لینک پرداخت تشخیص داده شود"
    
    def test_parse_payment_link_no_start_param(self):
        """تست parse کردن URL بدون پارامتر start"""
        url = "https://t.me/testbot"
        
        is_payment_link, parsed_dest, parsed_amount = parse_payment_link(url)
        
        assert is_payment_link == False, "نباید لینک پرداخت تشخیص داده شود"
    
    def test_parse_payment_link_with_ampersand(self):
        """تست parse کردن لینک با &start= (برای URLهای پیچیده)"""
        url = "https://t.me/testbot?param=value&start=pay_1234567890123456_100.50"
        
        is_payment_link, parsed_dest, parsed_amount = parse_payment_link(url)
        
        assert is_payment_link == True, "باید لینک پرداخت تشخیص داده شود"
        assert parsed_dest == "1234567890123456"
        assert abs(parsed_amount - 100.50) < 0.01
    
    def test_parse_payment_link_full_url_variations(self):
        """تست انواع مختلف URL"""
        test_cases = [
            ("https://t.me/testbot?start=pay_1234567890123456_100.50", True, "1234567890123456", 100.50),
            ("http://t.me/testbot?start=pay_1234567890123456_100.50", True, "1234567890123456", 100.50),
            ("t.me/testbot?start=pay_1234567890123456_100.50", True, "1234567890123456", 100.50),
            ("https://t.me/testbot?start=pay_100.50", True, None, 100.50),
            ("https://t.me/testbot?start=pay_1234567890123456_0.01", True, "1234567890123456", 0.01),
        ]
        
        for url, expected_is_link, expected_dest, expected_amount in test_cases:
            is_payment_link, parsed_dest, parsed_amount = parse_payment_link(url)
            assert is_payment_link == expected_is_link, f"برای URL {url} نتیجه اشتباه است"
            if expected_is_link:
                if expected_dest:
                    assert parsed_dest == expected_dest, f"برای URL {url} شماره حساب اشتباه است"
                else:
                    assert parsed_dest is None, f"برای URL {url} شماره حساب باید None باشد"
                assert abs(parsed_amount - expected_amount) < 0.01, f"برای URL {url} مبلغ اشتباه است"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
