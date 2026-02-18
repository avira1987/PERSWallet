"""Unzip uploaded deploy zip on server, migrate, collectstatic, restart Gunicorn."""
import paramiko
import sys

REMOTE_PATH = "/var/www/project1"
HOST, USER, PASSWORD = "62.60.128.97", "freelancer1", "amir2468"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

cmd = (
    f"cd {REMOTE_PATH} && unzip -o -q presWebsit_deploy.zip 2>/dev/null; "
    "sed -i 's/\\r$//' deploy/setup_on_server.sh 2>/dev/null; "
    f"cd {REMOTE_PATH}/backend && source venv/bin/activate && "
    "pip install -q -r requirements.txt && "
    "python manage.py migrate --noinput && "
    "python manage.py collectstatic --noinput --clear 2>/dev/null; "
    "pkill -f 'gunicorn.*config.wsgi' 2>/dev/null; sleep 2; "
    "nohup python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 "
    "--daemon --pid /tmp/gunicorn_presWebsit.pid --error-logfile /tmp/gunicorn_presWebsit.log 2>/dev/null; "
    "echo DONE"
)
stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
code = stdout.channel.recv_exit_status()
client.close()
print(out)
if err:
    print("STDERR:", err)
print("Exit code:", code)
sys.exit(0 if code == 0 else 1)
