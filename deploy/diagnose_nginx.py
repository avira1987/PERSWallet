"""Diagnose nginx config on server to understand current setup."""
import paramiko

HOST, USER, PASSWORD = "62.60.128.97", "freelancer1", "amir2468"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

commands = [
    ("Nginx status", "sudo -n nginx -t 2>&1 || nginx -t 2>&1 || echo 'cannot test'"),
    ("Nginx sites-enabled", "ls -la /etc/nginx/sites-enabled/ 2>/dev/null || ls -la /etc/nginx/conf.d/ 2>/dev/null"),
    ("All nginx server_name", "grep -r 'server_name' /etc/nginx/sites-enabled/ 2>/dev/null; grep -r 'server_name' /etc/nginx/conf.d/ 2>/dev/null"),
    ("All nginx listen", "grep -r 'listen' /etc/nginx/sites-enabled/ 2>/dev/null; grep -r 'listen' /etc/nginx/conf.d/ 2>/dev/null"),
    ("All nginx proxy_pass", "grep -r 'proxy_pass' /etc/nginx/sites-enabled/ 2>/dev/null; grep -r 'proxy_pass' /etc/nginx/conf.d/ 2>/dev/null"),
    ("All nginx root", "grep -r 'root ' /etc/nginx/sites-enabled/ 2>/dev/null; grep -r 'root ' /etc/nginx/conf.d/ 2>/dev/null"),
    ("Default site config", "cat /etc/nginx/sites-enabled/default 2>/dev/null | head -80"),
    ("Other site configs", "for f in /etc/nginx/sites-enabled/*; do echo '=== '$f' ==='; cat $f 2>/dev/null; echo; done"),
    ("Gunicorn running?", "ps aux | grep gunicorn | grep -v grep"),
    ("Port 8000 listener", "ss -tlnp | grep 8000 || echo 'nothing on 8000'"),
    ("SSL certs for persbot.ir?", "ls -la /etc/letsencrypt/live/persbot.ir/ 2>/dev/null || echo 'no cert for persbot.ir'"),
    ("All SSL certs", "ls /etc/letsencrypt/live/ 2>/dev/null || echo 'no letsencrypt'"),
    ("Certbot installed?", "which certbot 2>/dev/null || echo 'no certbot'"),
    ("Can we sudo?", "sudo -n whoami 2>&1"),
]

for label, cmd in commands:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    safe = "".join(c if ord(c) < 128 else "?" for c in (out + err))
    print(f"\n--- {label} ---")
    print(safe.strip() if safe.strip() else "(empty)")

client.close()
