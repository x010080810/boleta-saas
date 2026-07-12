import asyncio
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

engine = create_async_engine(settings.DATABASE_URL, echo=True)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        existing = await db.execute(
            select(SuperAdmin).where(SuperAdmin.email == "admin@sistema.com")
        )
        if existing.scalar_one_or_none():
            print("Super admin ya existe. Omitiendo seed.")
            return

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

        print("Seed completado exitosamente!")
        print("\nCredenciales del Super Admin:")
        print("  Email: admin@sistema.com")
        print("  Password: 123456")
        print("\nUse el formulario de registro en /register para crear nuevas empresas.")


asyncio.run(seed())
