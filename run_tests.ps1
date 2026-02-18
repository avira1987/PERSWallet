# Run tests for user management section
Write-Host "Running user management tests..." -ForegroundColor Green
Write-Host ""

pytest tests/ -v

Read-Host "Press Enter to continue"
