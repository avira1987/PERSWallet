@echo off
chcp 65001 >nul
echo ========================================
echo   دپلوی خودکار - Deploy to Server
echo ========================================
echo.
cd /d "%~dp0"
echo در حال اتصال به سرور...
echo اگر رمز خواست: ssh\README_freelancer1.txt
echo.
powershell -ExecutionPolicy Bypass -File ".\deploy.ps1"
echo.
echo ========================================
echo تمام. هر کلیدی برای بستن...
pause >nul
