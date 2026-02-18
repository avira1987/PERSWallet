# دپلوی سریع - راهنمای کامل

## روش ۱: دابل‌کلیک (ساده‌ترین)
فایل **`DEPLOY_NOW.bat`** را دابل‌کلیک کنید.

- اگر رمز عبور خواست: مقدار داخل `ssh\README_freelancer1.txt` را وارد کنید.
- بعد از اتمام، سایت در آدرس زیر در دسترس است:
  - **http://62.60.128.97:8000**
  - **http://62.60.128.97:8000/29962979.txt** (فایل تایید انماد)

---

## روش ۲: از PowerShell خارج از Cursor
1. کلید **Win + R** را بزنید
2. تایپ کنید: `powershell` و Enter
3. دستورات زیر را اجرا کنید:

```powershell
cd C:\Users\Administrator\Desktop\presWebsit
.\deploy.ps1
```

---

## روش ۳: دپلوی دستی (اگر اسکریپت خطا داد)

### مرحله ۱: ساخت zip
اسکریپت همین کار را می‌کند، اما اگر فقط می‌خواهید فایل‌ها را ببینید:
- پوشه `frontend` (بدون node_modules) + `backend` (بدون venv) + `deploy`

### مرحله ۲: آپلود با WinSCP
1. WinSCP را باز کنید
2. اتصال جدید:
   - میزبان: `62.60.128.97`
   - کاربر: `freelancer1`
   - رمز: از `ssh\README_freelancer1.txt`
3. فایل zip را به `/var/www/project1/` آپلود کنید
4. با SSH وصل شوید و اجرا کنید:

```bash
cd /var/www/project1
unzip -o presWebsit_deploy.zip
chmod +x deploy/setup_on_server.sh
./deploy/setup_on_server.sh /var/www/project1
```

---

## تغییرات انماد (اعمال شده)
- `29962979.txt` در ریشه سایت
- متاتگ `<meta name="enamad" content="29962979">`
- عنوان صفحه: سیستم حساب کاربری 29962979
