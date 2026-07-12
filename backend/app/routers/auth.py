from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    get_current_user,
)
from app.models.super_admin import SuperAdmin
from app.models.company import Company, CompanyUser, UserCompany
from app.models.system_settings import SystemSetting
from app.schemas.auth import LoginRequest, RegisterCompanyRequest, TokenResponse
from app.core.rate_limit import limiter
from app.services.email_sender import send_welcome_email, send_new_company_notification
from app.core.config import settings
from datetime import date, timedelta

router = APIRouter()


async def _get_system_smtp(db: AsyncSession) -> dict:
    result = await db.execute(select(SystemSetting))
    db_settings = {r.key: r.value for r in result.scalars().all()}
    return {
        "host": db_settings.get("smtp_host") or settings.SYSTEM_SMTP_HOST,
        "port": int(db_settings.get("smtp_port") or settings.SYSTEM_SMTP_PORT),
        "user": db_settings.get("smtp_user") or settings.SYSTEM_SMTP_USER,
        "password": db_settings.get("smtp_password") or settings.SYSTEM_SMTP_PASSWORD,
        "from_email": db_settings.get("smtp_from_email") or settings.SYSTEM_SMTP_FROM_EMAIL,
        "from_name": db_settings.get("smtp_from_name") or settings.SYSTEM_SMTP_FROM_NAME,
        "notification_email": db_settings.get("notification_email") or "",
    }


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register_company(req: RegisterCompanyRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Company).where(Company.ruc == req.company_ruc))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El RUC ya está registrado")

    existing_user = await db.execute(select(CompanyUser).where(CompanyUser.email == req.admin_email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    today = date.today()
    company = Company(
        name=req.company_name,
        ruc=req.company_ruc,
        plan_envios_mes=50,
        licencia_inicio=today,
        licencia_fin=today + timedelta(days=30),
        licencia_grace_hasta=today + timedelta(days=90),
        licencia_estado="activa",
        is_active=True,
    )
    db.add(company)
    await db.flush()

    user = CompanyUser(
        email=req.admin_email,
        hashed_password=get_password_hash(req.admin_password),
        full_name=req.admin_full_name,
    )
    db.add(user)
    await db.flush()

    assignment = UserCompany(user_id=user.id, company_id=company.id, role="admin")
    db.add(assignment)
    await db.flush()

    smtp = await _get_system_smtp(db)
    result_welcome = send_welcome_email(
        system_smtp_host=smtp["host"],
        system_smtp_port=smtp["port"],
        system_smtp_user=smtp["user"],
        system_smtp_password=smtp["password"],
        system_from_email=smtp["from_email"],
        system_from_name=smtp["from_name"],
        to_email=req.admin_email,
        admin_name=req.admin_full_name,
        company_name=req.company_name,
        company_ruc=req.company_ruc,
        plan_envios=50,
        dias_vigencia=30,
        licencia_inicio=str(company.licencia_inicio),
        licencia_fin=str(company.licencia_fin),
    )
    if not result_welcome.get("success"):
        print(f"[EMAIL ERROR] Bienvenida a {req.admin_email}: {result_welcome.get('error')}")

    notification_to = smtp["notification_email"]
    if not notification_to:
        super_result = await db.execute(select(SuperAdmin).where(SuperAdmin.is_active == True))
        super_admin = super_result.scalar_one_or_none()
        if super_admin:
            notification_to = super_admin.email

    if notification_to:
        result_notification = send_new_company_notification(
            system_smtp_host=smtp["host"],
            system_smtp_port=smtp["port"],
            system_smtp_user=smtp["user"],
            system_smtp_password=smtp["password"],
            system_from_email=smtp["from_email"],
            system_from_name=smtp["from_name"],
            to_email=notification_to,
            company_name=req.company_name,
            company_ruc=req.company_ruc,
            admin_email=req.admin_email,
            admin_name=req.admin_full_name,
            plan_envios=50,
            licencia_inicio=str(company.licencia_inicio),
            licencia_fin=str(company.licencia_fin),
        )
        if not result_notification.get("success"):
            print(f"[EMAIL ERROR] Notificación a {notification_to}: {result_notification.get('error')}")

    access_token = create_access_token({"sub": user.id, "user_type": "company_user"})
    refresh_token = create_refresh_token({"sub": user.id, "user_type": "company_user"})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "email": user.email, "full_name": user.full_name, "type": "company_user"},
        companies=[{"id": company.id, "name": company.name, "ruc": company.ruc}],
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyUser).where(CompanyUser.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    access_token = create_access_token({"sub": user.id, "user_type": "company_user"})
    refresh_token = create_refresh_token({"sub": user.id, "user_type": "company_user"})

    result = await db.execute(
        select(Company).join(UserCompany).where(
            UserCompany.user_id == user.id,
            UserCompany.is_active == True,
        )
    )
    companies = [{"id": c.id, "name": c.name, "ruc": c.ruc} for c in result.scalars().all()]

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "email": user.email, "full_name": user.full_name, "type": "company_user"},
        companies=companies,
    )


@router.post("/super-login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def super_admin_login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SuperAdmin).where(SuperAdmin.email == req.email))
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(req.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not admin.is_active:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    access_token = create_access_token({"sub": admin.id, "user_type": "super_admin"})
    refresh_token = create_refresh_token({"sub": admin.id, "user_type": "super_admin"})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": admin.id, "email": admin.email, "full_name": admin.full_name, "type": "super_admin"},
    )


@router.post("/refresh")
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)):
    from app.core.security import decode_token, create_access_token, create_refresh_token
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    user_id = payload.get("sub")
    user_type = payload.get("user_type")

    new_access = create_access_token({"sub": user_id, "user_type": user_type})
    new_refresh = create_refresh_token({"sub": user_id, "user_type": user_type})

    return {"access_token": new_access, "refresh_token": new_refresh}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
