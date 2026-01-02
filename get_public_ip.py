#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get public IP address for accessing the web panel from internet
"""

import socket
import urllib.request
import sys

def get_local_ip():
    """Get local IP address"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "نامشخص"

def get_public_ip():
    """Get public IP address"""
    try:
        # Try multiple services
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ifconfig.me/ip',
            'https://checkip.amazonaws.com'
        ]
        
        for service in services:
            try:
                with urllib.request.urlopen(service, timeout=5) as response:
                    ip = response.read().decode('utf-8').strip()
                    if ip:
                        return ip
            except Exception:
                continue
        
        return None
    except Exception:
        return None

if __name__ == '__main__':
    print("="*60)
    print("دریافت آدرس IP برای دسترسی به پنل وب")
    print("="*60)
    print()
    
    local_ip = get_local_ip()
    print(f"IP محلی (Local IP): {local_ip}")
    print(f"  دسترسی محلی: http://{local_ip}:5000")
    print()
    
    print("در حال دریافت IP عمومی...")
    public_ip = get_public_ip()
    
    if public_ip:
        print(f"IP عمومی (Public IP): {public_ip}")
        print(f"  دسترسی از اینترنت: http://{public_ip}:5000")
        print()
        print("⚠️  نکات مهم:")
        print("  1. مطمئن شوید پورت 5000 در فایروال ویندوز باز است")
        print("  2. اگر از روتر استفاده می‌کنید، Port Forwarding را تنظیم کنید")
        print("  3. برای امنیت بیشتر، از HTTPS استفاده کنید")
    else:
        print("❌ امکان دریافت IP عمومی وجود ندارد")
        print("  اتصال اینترنت را بررسی کنید")
    
    print()
    print("="*60)
