from fastapi import APIRouter, Request, HTTPException, Header
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.super_admin import SuperAdmin
from app.models.system_settings import SystemSetting
from app.core.config import settings

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
        existing = await db.execute(
            select(SuperAdmin).where(SuperAdmin.email == "admin@sistema.com")
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Super admin ya existe")

        super_admin = SuperAdmin(
            id="admin-001",
            email="admin@sistema.com",
            hashed_password=get_password_hash("123456"),
            full_name="Super Administrador",
        )
        db.add(super_admin)

        default_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": "587",
            "smtp_user": "",
            "smtp_password": "",
            "smtp_from_email": "noreply@boletasaas.com",
            "smtp_from_name": "Boleta SaaS",
            "notification_email": "admin@sistema.com",
        }
        for key, value in default_settings.items():
            existing_setting = await db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            if not existing_setting.scalar_one_or_none():
                db.add(SystemSetting(key=key, value=value))

        await db.commit()

    return {
        "message": "Seed completado exitosamente",
        "admin_email": "admin@sistema.com",
    }
