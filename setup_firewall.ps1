# Firewall Setup Script for BalanceBot Web Panel
# This script must be run with Administrator privileges

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================================"
Write-Host "Firewall Setup for BalanceBot Web Panel"
Write-Host "============================================================"
Write-Host ""

# Check for Administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Right-click on PowerShell"
    Write-Host "  2. Select 'Run as Administrator'"
    Write-Host "  3. Then run this script"
    Write-Host ""
    pause
    exit 1
}

Write-Host "OK: Administrator privileges confirmed" -ForegroundColor Green
Write-Host ""

$port = 5000
$ruleName = "BalanceBot-WebPanel-Port-$port"

# Check for existing rule
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "WARNING: Firewall rule '$ruleName' already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove and recreate it? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing existing rule..." -ForegroundColor Yellow
        Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        Write-Host "OK: Existing rule removed" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing rule. Exiting..." -ForegroundColor Yellow
        exit 0
    }
}

# Create Inbound rule
Write-Host "Creating firewall rule for port $port..." -ForegroundColor Cyan

try {
    # Inbound rule
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Name $ruleName `
        -Description "Allow inbound traffic for BalanceBot Web Panel on port $port" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $port `
        -Action Allow `
        -Enabled True `
        -Profile Any `
        -ErrorAction Stop
    
    Write-Host "OK: Inbound rule for port $port created" -ForegroundColor Green
    
    # Outbound rule (optional)
    $outboundRuleName = "$ruleName-Outbound"
    New-NetFirewallRule `
        -DisplayName $outboundRuleName `
        -Name $outboundRuleName `
        -Description "Allow outbound traffic for BalanceBot Web Panel on port $port" `
        -Direction Outbound `
        -Protocol TCP `
        -LocalPort $port `
        -Action Allow `
        -Enabled True `
        -Profile Any `
        -ErrorAction SilentlyContinue
    
    Write-Host "OK: Outbound rule for port $port created" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "OK: Firewall configuration completed successfully!" -ForegroundColor Green
    Write-Host "============================================================"
    Write-Host ""
    Write-Host "Port $port is now open in the firewall." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Access information:" -ForegroundColor Yellow
    Write-Host "  - Local access: http://localhost:$port"
    Write-Host "  - Network access: http://[Local-IP]:$port"
    Write-Host "  - Internet access: http://[Public-IP]:$port"
    Write-Host ""
    Write-Host "To get your public IP, run: python get_public_ip.py" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create firewall rule:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run the following command manually in PowerShell:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "New-NetFirewallRule -DisplayName '$ruleName' -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Display created rules
Write-Host "Created rules:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "$ruleName*" | Format-Table DisplayName, Direction, Enabled, Action -AutoSize

Write-Host ""
Write-Host "Press any key to close..."
pause
