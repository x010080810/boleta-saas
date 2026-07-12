import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(settings.DATABASE_URL_SYNC, echo=settings.DEBUG)
sync_session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    from app.models.company import Company, CompanyUser, UserCompany, Employee, EmployeeCompany
    from app.models.payroll import PayrollUpload, PaySlip, UnregisteredWorker
    from app.models.email_log import EmailLog
    from app.models.license import LicenseHistory
    from app.models.super_admin import SuperAdmin
    from app.models.quota import MonthlySendQuota
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        logging.warning("Database tables may already exist, continuing...")
