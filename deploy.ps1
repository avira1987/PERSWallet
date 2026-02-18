# Deploy script - Server: 62.60.128.97 | User: freelancer1 | Path: /var/www/project1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Server = "62.60.128.97"
$User = "freelancer1"
$RemotePath = "/var/www/project1"
$KeyPath = "$env:USERPROFILE\.ssh\id_freelancer1"

Write-Host "=== Deploy presWebsit ===" -ForegroundColor Cyan
Write-Host ""

# 1) Build frontend
Write-Host "[1/4] Building frontend (Vite)..." -ForegroundColor Yellow
Push-Location "$ProjectRoot\frontend"
if (-not (Test-Path "node_modules")) { npm install }
npm run build
if (-not (Test-Path "dist")) {
    Write-Host "Error: dist folder not created. Check build output above." -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "Frontend build OK." -ForegroundColor Green
Pop-Location
Write-Host ""

# 2) .env for production
$backendEnv = "$ProjectRoot\backend\.env"
$backendEnvProd = "$ProjectRoot\backend\.env.production.example"
if (-not (Test-Path $backendEnv) -and (Test-Path $backendEnvProd)) {
    Copy-Item $backendEnvProd $backendEnv
    Write-Host "[2/4] Created .env from .env.production.example. Edit backend\.env as needed." -ForegroundColor Yellow
} else {
    Write-Host "[2/4] .env exists or no production example." -ForegroundColor Gray
}
Write-Host ""

# 3) Upload to server
Write-Host "[3/4] Upload and install on server..." -ForegroundColor Yellow
$sshTarget = "${User}@${Server}"
$scpKey = ""
if (Test-Path $KeyPath) { $scpKey = "-i `"$KeyPath`"" }

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$tempZip = "$env:TEMP\presWebsit_deploy_$timestamp.zip"
$tempDir = "$env:TEMP\presWebsit_deploy_$timestamp"
if (Test-Path $tempZip) { Remove-Item $tempZip -Force -ErrorAction SilentlyContinue }
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Write-Host "Creating zip (excluding db, venv, node_modules)..."
Robocopy "$ProjectRoot\frontend" "$tempDir\frontend" /E /XD node_modules /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
Copy-Item -Path "$ProjectRoot\deploy" -Destination "$tempDir\deploy" -Recurse -Force
New-Item -ItemType Directory -Path "$tempDir\backend" -Force | Out-Null
Get-ChildItem "$ProjectRoot\backend" -Exclude "venv","__pycache__","db.sqlite3","staticfiles","*.pyc" | ForEach-Object { Copy-Item $_.FullName "$tempDir\backend\" -Recurse -Force }
$compressPaths = @("$tempDir\backend", "$tempDir\frontend", "$tempDir\deploy")
Compress-Archive -Path $compressPaths -DestinationPath $tempZip -Force
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Uploading (enter password if prompted)..."
$remoteZip = "presWebsit_deploy.zip"
$scpCmd = "scp $scpKey `"$tempZip`" ${sshTarget}:${RemotePath}/$remoteZip"
Write-Host "Command: $scpCmd" -ForegroundColor Gray
Invoke-Expression $scpCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Upload failed (exit $LASTEXITCODE). Try: ssh $sshTarget" -ForegroundColor Red
    Write-Host "Manual: upload zip to $RemotePath then on server run:" -ForegroundColor Yellow
    Write-Host "  cd $RemotePath; unzip -o presWebsit_deploy.zip; chmod +x deploy/setup_on_server.sh; ./deploy/setup_on_server.sh $RemotePath" -ForegroundColor White
    Remove-Item $tempZip -ErrorAction SilentlyContinue
    exit 1
}

$remoteCmd = "cd $RemotePath; unzip -o -q $remoteZip; chmod +x deploy/setup_on_server.sh; ./deploy/setup_on_server.sh $RemotePath"
$sshCmd = "ssh $scpKey $sshTarget `"$remoteCmd`""
Write-Host "Running setup on server..."
Invoke-Expression $sshCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "Server setup failed (exit $LASTEXITCODE). Run setup script manually on server." -ForegroundColor Red
}
Remove-Item $tempZip -ErrorAction SilentlyContinue
Write-Host ""

# 4) Access
Write-Host "[4/4] Access URLs:" -ForegroundColor Green
Write-Host "  Website:  http://${Server}:8000" -ForegroundColor White
Write-Host "  Admin:    http://${Server}:8000/admin/" -ForegroundColor White
Write-Host ""
Write-Host "If port 8000 blocked: on server run: sudo ufw allow 8000; sudo ufw reload" -ForegroundColor Gray
Write-Host "For production: use systemd or nohup for gunicorn." -ForegroundColor Gray
