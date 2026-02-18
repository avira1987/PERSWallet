# Start the Account System Web Server
# Access at: http://191.101.113.163:8000

Write-Host "Starting Account System on http://191.101.113.163:8000 ..." -ForegroundColor Green

Set-Location "$PSScriptRoot\backend"

# Activate virtual environment
& "$PSScriptRoot\backend\venv\Scripts\Activate.ps1"

# Run Django server on all interfaces, port 8000
python manage.py runserver 0.0.0.0:8000
