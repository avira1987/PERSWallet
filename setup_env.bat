@echo off
echo ========================================
echo    Balance Bot - Environment Setup
echo ========================================
echo.

if exist .env (
    echo [WARNING] .env file already exists!
    echo.
    set /p overwrite="Do you want to overwrite it? (y/n): "
    if /i not "%overwrite%"=="y" (
        echo Setup cancelled.
        pause
        exit /b 0
    )
)

if exist .env.example (
    echo [INFO] Copying .env.example to .env...
    copy .env.example .env >nul
    echo [SUCCESS] .env file created!
    echo.
    echo [IMPORTANT] Please edit .env file and add your BOT_TOKEN!
    echo.
    echo Steps:
    echo 1. Open .env file in a text editor
    echo 2. Replace "your_bot_token_here" with your actual bot token
    echo 3. Get your bot token from @BotFather on Telegram
    echo.
) else (
    echo [INFO] Creating .env file...
    (
        echo # Bot Configuration
        echo # Get your bot token from @BotFather on Telegram
        echo BOT_TOKEN=your_bot_token_here
        echo.
        echo # Admin User ID (optional)
        echo ADMIN_USER_ID=0
        echo.
        echo # Database Configuration
        echo DATABASE_URL=postgresql://user:password@localhost:5432/balancebot
        echo.
        echo # Encryption Key (optional but recommended)
        echo ENCRYPTION_KEY=
    ) > .env
    echo [SUCCESS] .env file created!
    echo.
    echo [IMPORTANT] Please edit .env file and add your BOT_TOKEN!
    echo.
)

echo Press any key to open .env file in notepad...
pause >nul
notepad .env

