#!/bin/bash
# اسکریپت نصب و راه‌اندازی روی سرور - در پوشه پروژه اجرا شود: /var/www/project1
set -e
echo "=== شروع نصب پیش‌نیازها و وابستگی‌ها ==="

# مسیر پروژه (پوشه حاوی backend و frontend)
PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

# نصب Python3 و pip در صورت نبود (مبتنی بر Debian/Ubuntu)
if ! command -v python3 &>/dev/null; then
    echo "نصب Python3..."
    sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv
fi
if ! command -v node &>/dev/null && ! command -v nodejs &>/dev/null; then
    echo "نصب Node.js برای ساخت فرانت..."
    sudo apt-get update -qq && sudo apt-get install -y -qq nodejs npm || true
fi

# Backend: venv و وابستگی‌ها
BACKEND="backend"
if [ ! -d "$BACKEND" ]; then
    echo "خطا: پوشه backend یافت نشد. در مسیر صحیح پروژه هستید؟ (مثلاً /var/www/project1)"
    exit 1
fi

cd "$BACKEND"
echo "=== ایجاد محیط مجازی Python ==="
python3 -m venv venv
source venv/bin/activate

echo "=== نصب وابستگی‌های Python ==="
pip install --upgrade pip -q
pip install -r requirements.txt

# فایل .env
if [ ! -f .env ]; then
    echo "هشدار: فایل .env وجود ندارد. از .env.production.example کپی کنید و مقادیر را تنظیم کنید."
    if [ -f .env.production.example ]; then
        cp .env.production.example .env
    elif [ -f .env.example ]; then
        cp .env.example .env
    fi
fi

echo "=== اجرای migrations ==="
python manage.py migrate --noinput

echo "=== جمع‌آوری فایل‌های استاتیک ==="
python manage.py collectstatic --noinput --clear 2>/dev/null || true

# اگر frontend/dist روی سرور نیست، سعی در ساخت فرانت (در صورت وجود node)
cd ..
if [ -d "frontend" ] && [ ! -d "frontend/dist" ]; then
    if command -v npm &>/dev/null || command -v node &>/dev/null; then
        echo "=== ساخت فرانت‌اند ==="
        cd frontend && npm ci --silent 2>/dev/null || npm install --silent
        npm run build
        cd ..
    else
        echo "هشدار: frontend/dist یافت نشد و Node نصب نیست. فرانت را locally بسازید و پوشه dist را کپی کنید."
    fi
fi

cd "$BACKEND"
echo "=== راه‌اندازی با Gunicorn (پورت 8000) ==="
echo "برای اجرای دائمی از systemd یا nohup استفاده کنید."
echo ""
echo "دسترسی به سایت: http://62.60.128.97:8000"
echo "ادمین: http://62.60.128.97:8000/admin/"
echo ""
# اجرای gunicorn در پیش‌زمینه تا خطاها نمایش داده شود
exec python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 2>&1
