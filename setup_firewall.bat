@echo off
chcp 65001 >nul
echo ============================================================
echo اجرای تنظیمات فایروال برای BalanceBot
echo ============================================================
echo.
echo این اسکریپت نیاز به دسترسی Administrator دارد.
echo.

:: بررسی دسترسی Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ خطا: این اسکریپت نیاز به دسترسی Administrator دارد!
    echo.
    echo لطفاً این فایل را با دسترسی Administrator اجرا کنید:
    echo   1. روی این فایل راست کلیک کنید
    echo   2. "Run as administrator" را انتخاب کنید
    echo.
    pause
    exit /b 1
)

echo ✓ دسترسی Administrator تایید شد
echo.
echo در حال اجرای اسکریپت PowerShell...
echo.

:: اجرای اسکریپت PowerShell
powershell.exe -ExecutionPolicy Bypass -File "%~dp0setup_firewall.ps1"

if %errorLevel% neq 0 (
    echo.
    echo ❌ خطا در اجرای اسکریپت
    pause
    exit /b 1
)

echo.
echo ============================================================
echo تنظیمات فایروال با موفقیت انجام شد!
echo ============================================================
pause
