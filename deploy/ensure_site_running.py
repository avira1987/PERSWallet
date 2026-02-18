"""
Ensure website is running on server: start Gunicorn persistently, open firewall.
Run from project root: python deploy/ensure_site_running.py
"""
import sys
import paramiko
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTE_PATH = "/var/www/project1"
HOST = "62.60.128.97"
USER = "freelancer1"
PASSWORD = "amir2468"
BACKEND = f"{REMOTE_PATH}/backend"
LOG_FILE = "/tmp/gunicorn_presWebsit.log"


def run_ssh(cmd, client, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def safe_print(text):
    print("".join(c if ord(c) < 128 else "?" for c in text), end="")


def main():
    print("Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

    # 1) Diagnose
    print("\n--- Gunicorn processes ---")
    code, out, _ = run_ssh("ps aux | grep -E 'gunicorn|grep' | grep -v grep", client)
    safe_print(out or "(none)\n")

    print("--- Port 8000 ---")
    code, out, _ = run_ssh("ss -tlnp 2>/dev/null | grep 8000 || netstat -tlnp 2>/dev/null | grep 8000 || true", client)
    safe_print(out or "(nothing listening on 8000)\n")

    print("--- Firewall (ufw) ---")
    code, out, _ = run_ssh("sudo -n ufw status 2>/dev/null || ufw status 2>/dev/null || true", client)
    safe_print(out or "(unknown)\n")

    # 2) Kill existing gunicorn for this project
    print("\nStopping any existing gunicorn for this project...")
    run_ssh(
        f"pkill -f 'gunicorn.*config.wsgi' 2>/dev/null; sleep 1; pgrep -f 'gunicorn.*config.wsgi' || true",
        client,
    )

    # 3) Open port 8000 (try with sudo; may fail without password)
    print("Opening port 8000 (firewall)...")
    code, out, err = run_ssh(
        "echo '%s' | sudo -S ufw allow 8000/tcp 2>/dev/null; echo '%s' | sudo -S ufw reload 2>/dev/null || true"
        % (PASSWORD, PASSWORD),
        client,
    )
    if "Rule added" in out or code == 0:
        print("Firewall updated.")
    else:
        print("Could not change firewall (may need manual: sudo ufw allow 8000; sudo ufw reload)")

    # 4) Start Gunicorn in a way that survives SSH disconnect (nohup + redirect + background)
    start_cmd = (
        f"cd {BACKEND} && source venv/bin/activate && "
        "nohup python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 "
        f"--daemon --pid /tmp/gunicorn_presWebsit.pid --access-logfile /tmp/gunicorn_access.log --error-logfile {LOG_FILE}"
    )
    print("Starting Gunicorn (daemon mode)...")
    code, out, err = run_ssh(start_cmd, client, timeout=60)
    if code != 0:
        safe_print(out)
        safe_print(err)
        print("Gunicorn start failed. Trying without --daemon...")
        start_cmd2 = (
            f"cd {BACKEND} && source venv/bin/activate && "
            f"nohup python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 >> {LOG_FILE} 2>&1 &"
        )
        run_ssh(start_cmd2, client)
        run_ssh("sleep 3", client)

    # 5) Verify
    print("\n--- Checking port 8000 again ---")
    code, out, _ = run_ssh("ss -tlnp 2>/dev/null | grep 8000 || true", client)
    safe_print(out or "(check failed)\n")

    print("--- Last lines of Gunicorn log ---")
    code, out, _ = run_ssh(f"tail -15 {LOG_FILE} 2>/dev/null || echo '(no log yet)'", client)
    safe_print(out)

    client.close()
    print("\n--- Done ---")
    print("Website: http://62.60.128.97:8000")
    print("Admin:   http://62.60.128.97:8000/admin/")
    if not out or "Listening" not in out:
        print("If still not accessible, on server run: sudo ufw allow 8000 && sudo ufw reload")
    return 0


if __name__ == "__main__":
    sys.exit(main())
