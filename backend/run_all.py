import subprocess
import sys
import os
import signal
import time

def main():
    port = os.environ.get("PORT", "8080")

    worker = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "app.core.celery_app", "worker", "-l", "info"],
    )

    beat = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "app.core.celery_app", "beat", "-l", "info"],
    )

    def cleanup(signum, frame):
        worker.terminate()
        beat.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    os.execvpe(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
        os.environ,
    )

if __name__ == "__main__":
    main()
