@echo off
chcp 65001 >nul
title BalanceBot - Launching Bot and Web Panel

echo ========================================
echo   BalanceBot - Launching Bot and Web Panel
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [INFO] Starting bot and web panel...
echo.

REM Run the unified launcher
python run_all.py

if errorlevel 1 (
    echo.
    echo [ERROR] Error running the application!
    pause
    exit /b 1
)

pause
