# راهنمای تنظیم فایروال برای BalanceBot

## روش‌های اجرای تنظیمات فایروال

### روش 1: استفاده از فایل Batch (پیشنهادی)
1. روی فایل `setup_firewall.bat` راست کلیک کنید
2. **"Run as administrator"** را انتخاب کنید
3. دستورالعمل‌های روی صفحه را دنبال کنید

### روش 2: اجرای مستقیم PowerShell
در PowerShell با دسترسی Administrator:

```powershell
cd C:\Users\Administrator\Desktop\balanceBot
.\setup_firewall.ps1
```

### روش 3: دستور مستقیم (بدون اسکریپت)
در PowerShell با دسترسی Administrator:

```powershell
New-NetFirewallRule -DisplayName "BalanceBot-WebPanel-Port-5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Enabled True
```

## بررسی تنظیمات

برای بررسی اینکه قانون فایروال ایجاد شده است:

```powershell
Get-NetFirewallRule -DisplayName "BalanceBot-WebPanel-Port-5000"
```

## حذف قانون فایروال (در صورت نیاز)

```powershell
Remove-NetFirewallRule -DisplayName "BalanceBot-WebPanel-Port-5000"
```

## نکات مهم

1. **دسترسی Administrator**: تمام روش‌ها نیاز به دسترسی Administrator دارند
2. **پورت 5000**: پورت 5000 برای دسترسی به پنل وب باز می‌شود
3. **امنیت**: اگر از اینترنت دسترسی دارید، حتماً از رمز عبور قوی استفاده کنید
4. **روتر**: اگر از روتر استفاده می‌کنید، باید Port Forwarding را هم تنظیم کنید

## دسترسی به پنل

بعد از باز کردن پورت در فایروال:
- **محلی**: http://localhost:5000
- **شبکه محلی**: http://[IP-محلی]:5000
- **اینترنت**: http://[IP-عمومی]:5000

برای دریافت IP عمومی:
```bash
python get_public_ip.py
```
