import subprocess
import sys
import os

def main():
    port = os.environ.get("PORT", "8080")
    processes = []

    p1 = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port,
    ])
    processes.append(p1)

    p2 = subprocess.Popen([
        sys.executable, "-m", "celery",
        "-A", "app.core.celery_app",
        "worker", "-l", "info",
    ])
    processes.append(p2)

    p3 = subprocess.Popen([
        sys.executable, "-m", "celery",
        "-A", "app.core.celery_app",
        "beat", "-l", "info",
    ])
    processes.append(p3)

    for p in processes:
        p.wait()

if __name__ == "__main__":
    main()
