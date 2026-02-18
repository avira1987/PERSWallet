"""
Deploy via SSH with password (README_freelancer1).
Creates zip, uploads to server, runs setup_on_server.sh.
"""
import os
import sys
import zipfile
import paramiko
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTE_PATH = "/var/www/project1"
HOST = "62.60.128.97"
USER = "freelancer1"
PASSWORD = "amir2468"  # from README_freelancer1.txt
ZIP_NAME = "presWebsit_deploy.zip"

SKIP_DIRS = {"venv", "__pycache__", "node_modules", "staticfiles"}
SKIP_FILES = {"db.sqlite3"}
SKIP_SUFFIXES = (".pyc",)


def add_dir_to_zip(zf, src_dir, arc_prefix):
    src = Path(src_dir)
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILES or f.endswith(SKIP_SUFFIXES):
                continue
            path = Path(root) / f
            arc = arc_prefix / rel / f
            zf.write(path, arc)


def main():
    zip_path = PROJECT_ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    print("Creating zip...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        add_dir_to_zip(zf, PROJECT_ROOT / "backend", Path("backend"))
        add_dir_to_zip(zf, PROJECT_ROOT / "frontend", Path("frontend"))
        add_dir_to_zip(zf, PROJECT_ROOT / "deploy", Path("deploy"))
    print(f"Zip created: {zip_path} ({zip_path.stat().st_size // 1024} KB)")

    print("Connecting to server (password auth)...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

    print("Uploading zip via SFTP...")
    sftp = client.open_sftp()
    try:
        sftp.put(str(zip_path), f"{REMOTE_PATH}/{ZIP_NAME}")
    finally:
        sftp.close()
    print("Upload done.")

    # Stop old Gunicorn, then fix CRLF and run setup in background
    commands = f"""
pkill -f 'gunicorn.*config.wsgi' 2>/dev/null; sleep 2
cd {REMOTE_PATH} && unzip -o -q {ZIP_NAME} && sed -i 's/\\r$//' deploy/setup_on_server.sh && chmod +x deploy/setup_on_server.sh && (nohup bash deploy/setup_on_server.sh {REMOTE_PATH} > /tmp/deploy.log 2>&1 &) && sleep 90 && echo '--- Last 60 lines of deploy log ---' && tail -60 /tmp/deploy.log
"""
    print("Running setup on server (background, waiting 90s for install)...")
    stdin, stdout, stderr = client.exec_command(commands, get_pty=True, timeout=200)
    for line in iter(stdout.readline, ""):
        safe = "".join(c if ord(c) < 128 else "?" for c in line)
        print(safe, end="")
    err = stderr.read().decode()
    if err:
        print("STDERR:", err, file=sys.stderr)
    code = stdout.channel.recv_exit_status()
    client.close()

    zip_path.unlink(missing_ok=True)
    if code != 0:
        print(f"Remote command exited with {code}", file=sys.stderr)
        sys.exit(1)
    print("\nDone. Access: http://62.60.128.97:8000 and http://62.60.128.97:8000/admin/")


if __name__ == "__main__":
    main()
