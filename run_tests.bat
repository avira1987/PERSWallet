@echo off
chcp 65001 >nul
echo ========================================
echo اجرای تست‌های ربات پرس بات
echo ========================================
echo.

cd /d "%~dp0"

echo در حال بررسی نصب pytest...
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo pytest نصب نشده است. در حال نصب...
    pip install pytest pytest-asyncio
)

echo.
echo در حال اجرای تست موافقت‌نامه...
echo.
python -m pytest tests/test_agreement_flow.py -v -s

echo.
echo ========================================
echo تست‌ها به پایان رسید
echo ========================================
pause
