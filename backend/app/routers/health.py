import secrets
import string
from fastapi import APIRouter, Request, HTTPException, Header
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.super_admin import SuperAdmin
from app.models.system_settings import SystemSetting
from app.core.config import settings

NEW_ADMIN_EMAIL = "juan.nizama.r@gmail.com"
OLD_ADMIN_EMAIL = "admin@sistema.com"


def _generate_secure_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    db_ready = getattr(request.app.state, "db_ready", False)
    return {
        "status": "ok" if db_ready else "degraded",
        "database": "connected" if db_ready else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/setup")
async def setup(x_setup_key: str = Header(alias="X-Setup-Key")):
    if x_setup_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid setup key")
    async with async_session_factory() as db:
        old = await db.execute(
            select(SuperAdmin).where(SuperAdmin.email == OLD_ADMIN_EMAIL)
        )
        old_admin = old.scalar_one_or_none()
        if old_admin:
            old_admin.is_active = False

        existing = await db.execute(
            select(SuperAdmin).where(SuperAdmin.email == NEW_ADMIN_EMAIL)
        )
        new_admin = existing.scalar_one_or_none()

        raw_password = _generate_secure_password()
        if new_admin:
            new_admin.hashed_password = get_password_hash(raw_password)
            new_admin.is_active = True
        else:
            new_admin = SuperAdmin(
                email=NEW_ADMIN_EMAIL,
                hashed_password=get_password_hash(raw_password),
                full_name="Super Admin",
                is_active=True,
            )
            db.add(new_admin)

        default_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": "587",
            "smtp_user": "",
            "smtp_password": "",
            "smtp_from_email": "noreply@boletasaas.com",
            "smtp_from_name": "Boleta SaaS",
            "notification_email": NEW_ADMIN_EMAIL,
        }
        for key, value in default_settings.items():
            existing_setting = await db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            if not existing_setting.scalar_one_or_none():
                db.add(SystemSetting(key=key, value=value))

        await db.commit()

    return {
        "message": "Setup completado",
        "admin_email": NEW_ADMIN_EMAIL,
        "admin_password": raw_password,
    }
