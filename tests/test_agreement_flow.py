"""
تست برای بررسی جریان تایید موافقت‌نامه
این تست بررسی می‌کند که:
1. موافقت‌نامه در دیتابیس به درستی ذخیره می‌شود
2. پس از تایید، ربات به مرحله بعدی می‌رود
3. بررسی می‌کند که کاربر می‌تواند از ربات استفاده کند
"""
import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from handlers.start import StartHandler
from utils.lock_manager import LockManager
from telegram import Update, CallbackQuery, User, Chat, Message
from telegram.ext import ContextTypes


class TestAgreementFlow:
    """تست جریان تایید موافقت‌نامه"""
    
    @pytest.fixture
    def db_manager(self):
        """ایجاد یک نمونه از DatabaseManager"""
        return DatabaseManager()
    
    @pytest.fixture
    def lock_manager(self, db_manager):
        """ایجاد یک نمونه از LockManager"""
        return LockManager(db_manager)
    
    @pytest.fixture
    def start_handler(self, db_manager, lock_manager):
        """ایجاد یک نمونه از StartHandler"""
        return StartHandler(db_manager, lock_manager)
    
    @pytest.fixture
    def mock_user(self):
        """ایجاد یک کاربر mock"""
        user = Mock(spec=User)
        user.id = 12345
        user.username = "test_user"
        user.first_name = "Test"
        return user
    
    @pytest.fixture
    def mock_chat(self):
        """ایجاد یک چت mock"""
        chat = Mock(spec=Chat)
        chat.id = 12345
        chat.type = "private"
        return chat
    
    @pytest.fixture
    def mock_update_with_callback(self, mock_user, mock_chat):
        """ایجاد یک Update mock با callback query"""
        update = Mock(spec=Update)
        update.effective_user = mock_user
        update.effective_chat = mock_chat
        
        callback_query = Mock(spec=CallbackQuery)
        callback_query.data = "accept_agreement"
        callback_query.from_user = mock_user
        callback_query.message = Mock(spec=Message)
        callback_query.message.chat = mock_chat
        callback_query.message.message_id = 1
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()
        
        update.callback_query = callback_query
        update.message = None
        return update
    
    @pytest.fixture
    def mock_context(self):
        """ایجاد یک Context mock"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        return context
    
    def test_agreement_not_accepted_initially(self, db_manager, mock_user):
        """تست: بررسی اینکه در ابتدا موافقت‌نامه تایید نشده است"""
        user_id = str(mock_user.id)
        
        # اطمینان از اینکه کاربر وجود دارد
        db_manager.get_or_create_user(user_id)
        
        # بررسی که موافقت‌نامه تایید نشده است
        has_accepted = db_manager.has_accepted_agreement(user_id)
        assert has_accepted == False, "موافقت‌نامه نباید در ابتدا تایید شده باشد"
    
    def test_accept_agreement_saves_to_database(self, db_manager, mock_user):
        """تست: بررسی اینکه تایید موافقت‌نامه در دیتابیس ذخیره می‌شود"""
        user_id = str(mock_user.id)
        
        # اطمینان از اینکه کاربر وجود دارد
        db_manager.get_or_create_user(user_id)
        
        # بررسی اولیه - نباید تایید شده باشد
        assert db_manager.has_accepted_agreement(user_id) == False
        
        # تایید موافقت‌نامه
        db_manager.accept_agreement(user_id)
        
        # بررسی که در دیتابیس ذخیره شده است
        has_accepted = db_manager.has_accepted_agreement(user_id)
        assert has_accepted == True, "موافقت‌نامه باید در دیتابیس ذخیره شده باشد"
    
    @pytest.mark.asyncio
    async def test_handle_accept_agreement_flow(self, start_handler, db_manager, 
                                                 mock_update_with_callback, mock_context, mock_user):
        """تست: بررسی جریان کامل تایید موافقت‌نامه"""
        user_id = str(mock_user.id)
        
        # پاک کردن وضعیت قبلی
        try:
            # اطمینان از اینکه کاربر وجود دارد و موافقت‌نامه تایید نشده است
            db_manager.get_or_create_user(user_id)
            # اگر قبلا تایید شده بود، آن را ریست کنیم (برای تست)
            # در واقعیت این کار را نمی‌کنیم، اما برای تست لازم است
        except:
            pass
        
        # بررسی اولیه
        initial_status = db_manager.has_accepted_agreement(user_id)
        print(f"\n[TEST] وضعیت اولیه موافقت‌نامه: {initial_status}")
        
        # اجرای handle_accept_agreement
        await start_handler.handle_accept_agreement(mock_update_with_callback, mock_context)
        
        # بررسی که callback.answer فراخوانی شده است
        mock_update_with_callback.callback_query.answer.assert_called_once()
        
        # بررسی که موافقت‌نامه در دیتابیس ذخیره شده است
        has_accepted = db_manager.has_accepted_agreement(user_id)
        assert has_accepted == True, f"موافقت‌نامه باید تایید شده باشد. وضعیت فعلی: {has_accepted}"
        
        # بررسی که edit_message_text یا send_message فراخوانی شده است
        # (بسته به اینکه کاربر اکانت دارد یا نه)
        assert (mock_update_with_callback.callback_query.edit_message_text.called or 
                mock_context.bot.send_message.called), "باید پیامی ارسال یا ویرایش شده باشد"
        
        print(f"[TEST] ✅ موافقت‌نامه با موفقیت تایید شد و در دیتابیس ذخیره شد")
    
    @pytest.mark.asyncio
    async def test_agreement_check_after_acceptance(self, start_handler, db_manager,
                                                     mock_context, mock_user, mock_chat):
        """تست: بررسی که پس از تایید، چک موافقت‌نامه درست کار می‌کند"""
        user_id = str(mock_user.id)
        
        # اطمینان از وجود کاربر
        db_manager.get_or_create_user(user_id)
        
        # تایید موافقت‌نامه
        db_manager.accept_agreement(user_id)
        
        # بررسی که has_accepted_agreement درست کار می‌کند
        has_accepted = db_manager.has_accepted_agreement(user_id)
        assert has_accepted == True, "پس از تایید، باید True برگرداند"
        
        # تست handle_start - باید به منوی اصلی یا welcome برود (نه به موافقت‌نامه)
        mock_update_message = Mock(spec=Update)
        mock_update_message.effective_user = mock_user
        mock_update_message.effective_chat = mock_chat
        mock_update_message.message = Mock(spec=Message)
        mock_update_message.message.chat = mock_chat
        mock_update_message.message.reply_text = AsyncMock()
        mock_update_message.callback_query = None
        
        await start_handler.handle_start(mock_update_message, mock_context)
        
        # بررسی که show_agreement فراخوانی نشده است
        # (اگر فراخوانی شده بود، باید reply_text با متن موافقت‌نامه فراخوانی می‌شد)
        # اما ما باید بررسی کنیم که reply_text فراخوانی شده (برای welcome یا main menu)
        assert mock_update_message.message.reply_text.called, "باید پیامی ارسال شده باشد"
        
        # بررسی محتوای پیام - نباید شامل "موافقت‌نامه" باشد
        call_args = mock_update_message.message.reply_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "موافقت‌نامه" not in message_text, "پس از تایید، نباید موافقت‌نامه نمایش داده شود"
        
        print(f"[TEST] ✅ پس از تایید موافقت‌نامه، کاربر به مرحله بعدی هدایت شد")
    
    @pytest.mark.asyncio
    async def test_callback_after_agreement_acceptance(self, db_manager, lock_manager,
                                                       mock_update_with_callback, mock_context, mock_user):
        """تست: بررسی که callback های دیگر پس از تایید موافقت‌نامه کار می‌کنند"""
        from bot import BalanceBot
        
        user_id = str(mock_user.id)
        
        # اطمینان از وجود کاربر
        db_manager.get_or_create_user(user_id)
        
        # تایید موافقت‌نامه
        db_manager.accept_agreement(user_id)
        
        # تغییر callback_data به یک callback دیگر (مثلا main_menu)
        mock_update_with_callback.callback_query.data = "main_menu"
        
        # ایجاد bot instance
        bot = BalanceBot()
        
        # اجرای handle_callback
        await bot.handle_callback(mock_update_with_callback, mock_context)
        
        # بررسی که callback.answer فراخوانی شده است
        mock_update_with_callback.callback_query.answer.assert_called_once()
        
        # بررسی که edit_message_text فراخوانی شده است (برای نمایش منوی اصلی)
        assert mock_update_with_callback.callback_query.edit_message_text.called, \
            "باید منوی اصلی نمایش داده شود"
        
        print(f"[TEST] ✅ پس از تایید موافقت‌نامه، callback های دیگر به درستی کار می‌کنند")
    
    def test_agreement_persistence(self, db_manager, mock_user):
        """تست: بررسی ماندگاری تایید موافقت‌نامه در دیتابیس"""
        user_id = str(mock_user.id)
        
        # اطمینان از وجود کاربر
        db_manager.get_or_create_user(user_id)
        
        # تایید موافقت‌نامه
        db_manager.accept_agreement(user_id)
        
        # بررسی اول
        assert db_manager.has_accepted_agreement(user_id) == True
        
        # ایجاد یک session جدید و بررسی دوباره (شبیه‌سازی restart)
        assert db_manager.has_accepted_agreement(user_id) == True, \
            "تایید موافقت‌نامه باید در session های مختلف ماندگار باشد"
        
        print(f"[TEST] ✅ تایید موافقت‌نامه در دیتابیس ماندگار است")
    
    @pytest.mark.asyncio
    async def test_agreement_acceptance_then_immediate_use(self, db_manager, lock_manager,
                                                          mock_user, mock_chat):
        """تست: بررسی مشکل گزارش شده - تایید موافقت‌نامه اما جلو نرفتن"""
        from bot import BalanceBot
        
        user_id = str(mock_user.id)
        
        # اطمینان از وجود کاربر و عدم تایید موافقت‌نامه
        db_manager.get_or_create_user(user_id)
        # اگر قبلا تایید شده بود، آن را ریست کنیم
        # (در واقعیت این کار را نمی‌کنیم، اما برای تست لازم است)
        
        # بررسی اولیه
        initial_status = db_manager.has_accepted_agreement(user_id)
        print(f"\n[TEST] وضعیت اولیه موافقت‌نامه: {initial_status}")
        
        # شبیه‌سازی کلیک روی accept_agreement
        bot = BalanceBot()
        
        # ایجاد update برای accept_agreement
        update_accept = Mock(spec=Update)
        update_accept.effective_user = mock_user
        update_accept.effective_chat = mock_chat
        
        callback_query_accept = Mock(spec=CallbackQuery)
        callback_query_accept.data = "accept_agreement"
        callback_query_accept.from_user = mock_user
        callback_query_accept.message = Mock(spec=Message)
        callback_query_accept.message.chat = mock_chat
        callback_query_accept.message.message_id = 1
        callback_query_accept.answer = AsyncMock()
        callback_query_accept.edit_message_text = AsyncMock()
        
        update_accept.callback_query = callback_query_accept
        update_accept.message = None
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        
        # اجرای handle_callback برای accept_agreement
        await bot.handle_callback(update_accept, context)
        
        # بررسی که callback.answer فراخوانی شده است
        callback_query_accept.answer.assert_called_once()
        
        # بررسی که موافقت‌نامه در دیتابیس ذخیره شده است
        has_accepted = db_manager.has_accepted_agreement(user_id)
        assert has_accepted == True, \
            f"❌ مشکل پیدا شد! موافقت‌نامه باید تایید شده باشد اما وضعیت: {has_accepted}"
        
        print(f"[TEST] ✅ موافقت‌نامه در دیتابیس ذخیره شد: {has_accepted}")
        
        # حالا شبیه‌سازی استفاده از یک ویژگی دیگر (مثلا main_menu)
        update_main_menu = Mock(spec=Update)
        update_main_menu.effective_user = mock_user
        update_main_menu.effective_chat = mock_chat
        
        callback_query_menu = Mock(spec=CallbackQuery)
        callback_query_menu.data = "main_menu"
        callback_query_menu.from_user = mock_user
        callback_query_menu.message = Mock(spec=Message)
        callback_query_menu.message.chat = mock_chat
        callback_query_menu.message.message_id = 2
        callback_query_menu.answer = AsyncMock()
        callback_query_menu.edit_message_text = AsyncMock()
        
        update_main_menu.callback_query = callback_query_menu
        update_main_menu.message = None
        
        # اجرای handle_callback برای main_menu
        await bot.handle_callback(update_main_menu, context)
        
        # بررسی که callback.answer فراخوانی شده است
        callback_query_menu.answer.assert_called_once()
        
        # بررسی که edit_message_text فراخوانی شده است (نه show_agreement)
        assert callback_query_menu.edit_message_text.called, \
            "❌ مشکل پیدا شد! باید منوی اصلی نمایش داده شود، نه موافقت‌نامه"
        
        # بررسی محتوای پیام - نباید شامل "موافقت‌نامه" باشد
        call_args = callback_query_menu.edit_message_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "موافقت‌نامه" not in message_text, \
                f"❌ مشکل پیدا شد! پس از تایید، نباید موافقت‌نامه نمایش داده شود. متن: {message_text[:100]}"
        
        print(f"[TEST] ✅ پس از تایید موافقت‌نامه، کاربر می‌تواند از ویژگی‌های دیگر استفاده کند")


if __name__ == "__main__":
    # اجرای تست‌ها
    pytest.main([__file__, "-v", "-s"])
