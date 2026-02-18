# BalanceBot - Unified Launcher (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BalanceBot - Launching Bot and Web Panel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[INFO] Starting bot and web panel..." -ForegroundColor Green
Write-Host ""

# Run the unified launcher
python run_all.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Error running the application!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
