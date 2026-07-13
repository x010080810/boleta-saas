import os
import boto3
from typing import Optional
from app.core.config import settings


_s3_client: Optional[object] = None


def _get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.SUPABASE_S3_ENDPOINT,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
            region_name=settings.SUPABASE_S3_REGION,
        )
    return _s3_client


def _bucket_name() -> str:
    return settings.STORAGE_BUCKET


def save_pdf(file_bytes: bytes, key: str) -> str:
    s3 = _get_s3()
    s3.put_object(Bucket=_bucket_name(), Key=key, Body=file_bytes, ContentType="application/pdf")
    return key


def read_pdf(key: str) -> Optional[bytes]:
    if not key:
        return None
    s3 = _get_s3()
    try:
        resp = s3.get_object(Bucket=_bucket_name(), Key=key)
        return resp["Body"].read()
    except Exception:
        return None


def save_upload(file_bytes: bytes, key: str) -> str:
    s3 = _get_s3()
    s3.put_object(Bucket=_bucket_name(), Key=key, Body=file_bytes)
    return key


def delete_file(key: str) -> None:
    s3 = _get_s3()
    try:
        s3.delete_object(Bucket=_bucket_name(), Key=key)
    except Exception:
        pass


def get_public_url(key: str) -> str:
    base = settings.SUPABASE_S3_PUBLIC_URL
    if not base:
        return key
    return f"{base.rstrip('/')}/{key.lstrip('/')}"


def ensure_dirs() -> None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
