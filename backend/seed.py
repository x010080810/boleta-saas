import asyncio
import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.super_admin import SuperAdmin
from app.models.system_settings import SystemSetting
from app.models.company import Company, CompanyUser, UserCompany, Employee, EmployeeCompany
from app.models.payroll import PayrollUpload, PaySlip, UnregisteredWorker
from app.models.quota import MonthlySendQuota
from app.models.email_log import EmailLog
from app.models.license import LicenseHistory
from app.core.config import settings
from datetime import datetime, timezone

NEW_ADMIN_EMAIL = "juan.nizama.r@gmail.com"
OLD_ADMIN_EMAIL = "admin@sistema.com"

engine = create_async_engine(settings.DATABASE_URL, echo=True)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        old = await db.execute(select(SuperAdmin).where(SuperAdmin.email == OLD_ADMIN_EMAIL))
        old_admin = old.scalar_one_or_none()
        if old_admin:
            old_admin.is_active = False
            print(f"Cuenta antigua ({OLD_ADMIN_EMAIL}) desactivada.")

        existing = await db.execute(select(SuperAdmin).where(SuperAdmin.email == NEW_ADMIN_EMAIL))
        new_admin = existing.scalar_one_or_none()

        raw_password = "".join(
            secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
            for _ in range(16)
        )
        if new_admin:
            new_admin.hashed_password = get_password_hash(raw_password)
            new_admin.is_active = True
            print(f"Super admin ({NEW_ADMIN_EMAIL}) actualizado.")
        else:
            new_admin = SuperAdmin(
                email=NEW_ADMIN_EMAIL,
                hashed_password=get_password_hash(raw_password),
                full_name="Super Admin",
                is_active=True,
            )
            db.add(new_admin)
            print(f"Super admin ({NEW_ADMIN_EMAIL}) creado.")

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

        print("\nSeed completado!")
        print(f"  Email: {NEW_ADMIN_EMAIL}")
        print(f"  Password: {raw_password}")


asyncio.run(seed())
