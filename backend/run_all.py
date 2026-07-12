import subprocess
import sys
import os
import time
import signal

processes = []

def signal_handler(signum, frame):
    for p in processes:
        p.terminate()
    sys.exit(0)

def main():
    port = os.environ.get("PORT", "8080")

    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(api)

    worker = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "app.core.celery_app", "worker", "-l", "info"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(worker)

    beat = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "app.core.celery_app", "beat", "-l", "info"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(beat)

    for p in processes:
        p.wait()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()
