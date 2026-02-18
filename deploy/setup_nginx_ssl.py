"""
Setup nginx reverse proxy for persbot.ir -> gunicorn:8000 and get SSL cert.
Does NOT touch soodnama.ir config.
"""
import paramiko
import sys
import time

HOST, USER, PASSWORD = "62.60.128.97", "freelancer1", "amir2468"
DOMAIN = "persbot.ir"
WWW_DOMAIN = "www.persbot.ir"

NGINX_CONF = f"""server {{
    listen 80;
    server_name {DOMAIN} {WWW_DOMAIN};

    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        client_max_body_size 20M;
    }}

    location /static/ {{
        alias /var/www/project1/backend/staticfiles/;
    }}

    location /media/ {{
        alias /var/www/project1/backend/media/;
    }}
}}
"""


def run(client, cmd, timeout=30, use_sudo=False):
    if use_sudo:
        cmd = f"echo '{PASSWORD}' | sudo -S bash -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def safe_print(label, text):
    safe = "".join(c if ord(c) < 128 else "?" for c in text)
    print(f"[{label}] {safe.strip()}")


def main():
    print("Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

    # 1) Test sudo
    print("\n=== Testing sudo access ===")
    code, out, err = run(client, "whoami", use_sudo=True)
    if "root" in out:
        print("sudo OK (root)")
    else:
        safe_print("sudo out", out)
        safe_print("sudo err", err)
        print("sudo may not work. Trying anyway...")

    # 2) Write nginx config via SFTP to /tmp then sudo mv
    print("\n=== Writing nginx config for persbot.ir ===")
    sftp = client.open_sftp()
    with sftp.file("/tmp/persbot_nginx.conf", "w") as f:
        f.write(NGINX_CONF)
    sftp.close()
    code, out, err = run(client, "cp /tmp/persbot_nginx.conf /etc/nginx/sites-available/persbot", use_sudo=True)
    if code != 0:
        safe_print("copy err", err)
        print("Failed to write config!")
        client.close()
        return 1
    print("Config written to /etc/nginx/sites-available/persbot")

    # 3) Enable site (symlink)
    print("\n=== Enabling site ===")
    code, out, err = run(client, "ln -sf /etc/nginx/sites-available/persbot /etc/nginx/sites-enabled/persbot", use_sudo=True)
    if code != 0:
        safe_print("symlink err", err)

    # 4) Test nginx config
    print("\n=== Testing nginx config ===")
    code, out, err = run(client, "nginx -t 2>&1", use_sudo=True)
    combined = out + err
    safe_print("nginx -t", combined)
    if "successful" not in combined.lower():
        print("WARNING: nginx config test not clean. Checking if it's just the old soodnama cert issue...")

    # 5) Reload nginx
    print("\n=== Reloading nginx ===")
    code, out, err = run(client, "systemctl reload nginx 2>&1 || nginx -s reload 2>&1", use_sudo=True)
    safe_print("reload", out + err)
    time.sleep(2)

    # 6) Quick HTTP test from server
    print("\n=== Testing HTTP from server ===")
    code, out, err = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8000/ 2>&1", timeout=10)
    safe_print("Gunicorn direct (port 8000)", out)
    code, out, err = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' -H 'Host: {DOMAIN}' http://127.0.0.1/ 2>&1", timeout=10)
    safe_print("Nginx proxy (port 80)", out)

    # 7) Get SSL certificate with certbot
    print("\n=== Getting SSL certificate with certbot ===")
    certbot_cmd = f"certbot --nginx -d {DOMAIN} -d {WWW_DOMAIN} --non-interactive --agree-tos --email admin@{DOMAIN} --redirect 2>&1"
    code, out, err = run(client, certbot_cmd, use_sudo=True, timeout=120)
    combined = out + err
    safe_print("certbot", combined)

    if "congratulations" in combined.lower() or "successfully" in combined.lower():
        print("SSL certificate obtained!")
    elif "certificate not yet due for renewal" in combined.lower():
        print("SSL certificate already exists!")
    else:
        print("Certbot may have had issues. Trying without www...")
        certbot_cmd2 = f"certbot --nginx -d {DOMAIN} --non-interactive --agree-tos --email admin@{DOMAIN} --redirect 2>&1"
        code, out, err = run(client, certbot_cmd2, use_sudo=True, timeout=120)
        combined = out + err
        safe_print("certbot (no www)", combined)

    # 8) Reload nginx again after certbot
    print("\n=== Final nginx reload ===")
    code, out, err = run(client, "systemctl reload nginx 2>&1", use_sudo=True)
    safe_print("reload", out + err)

    # 9) Show final config
    print("\n=== Final persbot nginx config ===")
    code, out, err = run(client, "cat /etc/nginx/sites-enabled/persbot 2>&1")
    safe_print("config", out)

    # 10) Final test
    print("\n=== Final test from server ===")
    code, out, err = run(client, f"curl -sI http://{DOMAIN} 2>&1 | head -5", timeout=10)
    safe_print(f"http://{DOMAIN}", out)
    code, out, err = run(client, f"curl -skI https://{DOMAIN} 2>&1 | head -5", timeout=10)
    safe_print(f"https://{DOMAIN}", out)

    client.close()
    print("\n=== DONE ===")
    print(f"Website: https://{DOMAIN}")
    print(f"Admin:   https://{DOMAIN}/admin/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
