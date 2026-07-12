from pydantic_settings import BaseSettings
from typing import Optional
import warnings


class Settings(BaseSettings):
    APP_NAME: str = "Boleta SaaS"
    ENVIRONMENT: str = "development"

    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT != "production"

    DATABASE_URL: str = "postgresql+asyncpg://boleta_user:boleta_pass_2025@localhost:5432/boleta_saas"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "super-secret-key-change-in-production-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOAD_DIR: str = "/tmp/uploads"
    OUTPUT_DIR: str = "/tmp/output"
    BACKUP_DIR: str = "/tmp/backups"

    MAX_UPLOAD_SIZE_MB: int = 20
    MAX_EMAILS_PER_HOUR: int = 100

    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        if self.ENVIRONMENT == "production":
            return [self.FRONTEND_URL]
        return ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]

    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 5

    LOG_LEVEL: str = "INFO"

    SYSTEM_SMTP_HOST: str = "smtp.gmail.com"
    SYSTEM_SMTP_PORT: int = 587
    SYSTEM_SMTP_USER: str = ""
    SYSTEM_SMTP_PASSWORD: str = ""
    SYSTEM_SMTP_FROM_EMAIL: str = "noreply@boletasaas.com"
    SYSTEM_SMTP_FROM_NAME: str = "Boleta SaaS"

    # SendGrid (alternativa a SMTP para entornos que bloquean puertos SMTP)
    SENDGRID_API_KEY: str = ""

    # Supabase Storage (S3-compatible)
    SUPABASE_S3_ENDPOINT: str = ""
    SUPABASE_S3_ACCESS_KEY: str = ""
    SUPABASE_S3_SECRET_KEY: str = ""
    SUPABASE_S3_REGION: str = "sa-east-1"
    STORAGE_BUCKET: str = "payslips"
    SUPABASE_S3_PUBLIC_URL: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

if settings.SECRET_KEY == "super-secret-key-change-in-production-12345" and settings.ENVIRONMENT == "production":
    warnings.warn(
        "SECRET_KEY no ha sido cambiada del valor por defecto. "
        "Genera una segura con: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
