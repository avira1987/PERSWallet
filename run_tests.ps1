# اجرای تست‌های ربات پرس بات
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "اجرای تست‌های ربات پرس بات" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# تغییر به دایرکتوری اسکریپت
Set-Location $PSScriptRoot

# بررسی نصب pytest
Write-Host "در حال بررسی نصب pytest..." -ForegroundColor Yellow
try {
    python -m pytest --version | Out-Null
    Write-Host "pytest نصب شده است." -ForegroundColor Green
} catch {
    Write-Host "pytest نصب نشده است. در حال نصب..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio
}

Write-Host ""
Write-Host "در حال اجرای تست موافقت‌نامه..." -ForegroundColor Yellow
Write-Host ""

# اجرای تست‌ها
python -m pytest tests/test_agreement_flow.py -v -s

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "تست‌ها به پایان رسید" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "برای بستن، کلیدی را فشار دهید..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
