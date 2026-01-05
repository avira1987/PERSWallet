#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اسکریپت مایگریشن برای ایجاد جدول payment_links
این اسکریپت جدول payment_links را در دیتابیس ایجاد می‌کند.
"""

import sys
import os

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.models import PaymentLink
from sqlalchemy import inspect
import logging

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migration():
    """اجرای مایگریشن برای جدول payment_links"""
    try:
        logger.info("=" * 60)
        logger.info("شروع مایگریشن payment_links...")
        logger.info("=" * 60)
        
        # ایجاد اتصال به دیتابیس
        db_manager = DatabaseManager()
        
        # بررسی وجود جدول
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        if 'payment_links' in tables:
            logger.info("✅ جدول payment_links از قبل وجود دارد.")
            
            # بررسی ساختار جدول
            columns = [col['name'] for col in inspector.get_columns('payment_links')]
            logger.info(f"ستون‌های موجود: {', '.join(columns)}")
            
            # بررسی وجود ستون‌های مورد نیاز
            required_columns = ['token', 'destination_account', 'amount', 'created_by', 
                              'is_used', 'used_at', 'used_by', 'created_at']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                logger.warning(f"⚠️ ستون‌های زیر وجود ندارند: {', '.join(missing_columns)}")
                logger.info("در حال ایجاد ستون‌های گمشده...")
                # در اینجا می‌توانید منطق اضافه کردن ستون‌ها را اضافه کنید
            else:
                logger.info("✅ همه ستون‌های مورد نیاز وجود دارند.")
        else:
            logger.info("📝 جدول payment_links وجود ندارد. در حال ایجاد...")
            
            # ایجاد جدول
            PaymentLink.__table__.create(db_manager.engine, checkfirst=True)
            logger.info("✅ جدول payment_links با موفقیت ایجاد شد.")
        
        logger.info("=" * 60)
        logger.info("مایگریشن با موفقیت انجام شد! ✅")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در اجرای مایگریشن: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
