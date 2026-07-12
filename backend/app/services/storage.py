import os
from typing import Optional
from app.core.config import settings


_pdf_dir: Optional[str] = None


def _get_output_dir() -> str:
    global _pdf_dir
    if _pdf_dir is None:
        _pdf_dir = settings.OUTPUT_DIR
        os.makedirs(_pdf_dir, exist_ok=True)
    return _pdf_dir


def save_pdf(file_bytes: bytes, filename: str) -> str:
    output_dir = _get_output_dir()
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath


def read_pdf(filepath: str) -> Optional[bytes]:
    if not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        return f.read()


def ensure_dirs() -> None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
