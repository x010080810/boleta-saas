from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash
from app.models.company import Company, CompanyUser, UserCompany
from app.models.super_admin import SuperAdmin
from app.models.payroll import PayrollUpload, PaySlip
from app.models.quota import MonthlySendQuota
from app.models.license import LicenseHistory
from app.models.email_log import EmailLog
from app.models.system_settings import SystemSetting
from app.schemas.company import LicenseUpdate, AdminCreateUserRequest, AdminAssignUserRequest, AdminUpdateAssignmentRequest, AdminCreateCompanyRequest, AdminCreateCompanyResponse
from app.core.password_policy import validate_password, generate_secure_password
from app.core.config import settings
from app.services.email_sender import send_welcome_email, send_new_company_notification
from datetime import date, datetime, timezone, timedelta

router = APIRouter()


async def verify_super_admin(current_user: dict):
    if current_user["type"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super administradores")


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


@router.get("/companies")
async def admin_list_companies(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(select(Company).order_by(Company.name))
    companies = result.scalars().all()

    data = []
    for c in companies:
        uploads_result = await db.execute(
            select(func.count(PayrollUpload.id)).where(PayrollUpload.company_id == c.id)
        )
        total_uploads = uploads_result.scalar()

        quota_result = await db.execute(
            select(MonthlySendQuota).where(
                MonthlySendQuota.company_id == c.id,
                MonthlySendQuota.anio == date.today().year,
                MonthlySendQuota.mes == date.today().month,
            )
        )
        quota = quota_result.scalar_one_or_none()

        data.append({
            "id": c.id,
            "name": c.name,
            "ruc": c.ruc,
            "plan_envios_mes": c.plan_envios_mes,
            "licencia_inicio": str(c.licencia_inicio) if c.licencia_inicio else None,
            "licencia_fin": str(c.licencia_fin) if c.licencia_fin else None,
            "licencia_grace_hasta": str(c.licencia_grace_hasta) if c.licencia_grace_hasta else None,
            "licencia_estado": c.licencia_estado,
            "is_active": c.is_active,
            "total_uploads": total_uploads,
            "quota_utilizada": quota.utilizados if quota else 0,
            "quota_limite": quota.limite if quota else c.plan_envios_mes,
        })

    return data


@router.post("/companies")
async def admin_create_company(
    req: AdminCreateCompanyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    existing_ruc = await db.execute(select(Company).where(Company.ruc == req.company_ruc))
    if existing_ruc.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El RUC ya está registrado")

    existing_user = await db.execute(select(CompanyUser).where(CompanyUser.email == req.admin_email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    company = Company(
        name=req.company_name,
        ruc=req.company_ruc,
        plan_envios_mes=req.plan_envios_mes,
        licencia_inicio=req.licencia_inicio,
        licencia_fin=req.licencia_fin,
        licencia_grace_hasta=req.licencia_fin + timedelta(days=req.dias_gracia),
        licencia_estado="activa",
        is_active=True,
    )
    db.add(company)
    await db.flush()

    raw_password = req.admin_password or generate_secure_password()
    if not raw_password:
        raw_password = generate_secure_password()

    user = CompanyUser(
        email=req.admin_email,
        hashed_password=get_password_hash(raw_password),
        full_name=req.admin_full_name,
    )
    db.add(user)
    await db.flush()

    assignment = UserCompany(user_id=user.id, company_id=company.id, role="admin")
    db.add(assignment)
    await db.flush()

    await db.commit()

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
        plan_envios=req.plan_envios_mes,
        dias_vigencia=30,
        licencia_inicio=str(req.licencia_inicio),
        licencia_fin=str(req.licencia_fin),
    )
    if not result_welcome.get("success"):
        print(f"[EMAIL ERROR] Bienvenida a {req.admin_email}: {result_welcome.get('error')}")

    notification_to = smtp["notification_email"] or ""
    super_result = await db.execute(select(SuperAdmin).where(SuperAdmin.is_active == True))
    super_admin = super_result.scalars().first()
    if super_admin:
        if not notification_to:
            notification_to = super_admin.email
        elif notification_to != super_admin.email:
            print(f"[ADMIN] notification_email en settings ({notification_to}) difiere del super admin ({super_admin.email}), usando super admin")
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
            plan_envios=req.plan_envios_mes,
            licencia_inicio=str(req.licencia_inicio),
            licencia_fin=str(req.licencia_fin),
        )
        if not result_notification.get("success"):
            print(f"[EMAIL ERROR] Notificacion a {notification_to}: {result_notification.get('error')}")

    return AdminCreateCompanyResponse(
        company_id=company.id,
        company_name=company.name,
        admin_email=user.email,
        admin_password=raw_password,
    )


@router.get("/companies/{company_id}")
async def admin_get_company(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    result = await db.execute(
        select(CompanyUser, UserCompany)
        .join(UserCompany, UserCompany.user_id == CompanyUser.id)
        .where(UserCompany.company_id == company_id)
    )
    users = [
        {
            "id": row.CompanyUser.id,
            "email": row.CompanyUser.email,
            "full_name": row.CompanyUser.full_name,
            "role": row.UserCompany.role,
            "is_active": row.UserCompany.is_active,
        }
        for row in result.all()
    ]

    return {
        "id": company.id,
        "name": company.name,
        "ruc": company.ruc,
        "logo_url": company.logo_url,
        "plan_envios_mes": company.plan_envios_mes,
        "licencia_inicio": str(company.licencia_inicio) if company.licencia_inicio else None,
        "licencia_fin": str(company.licencia_fin) if company.licencia_fin else None,
        "licencia_grace_hasta": str(company.licencia_grace_hasta) if company.licencia_grace_hasta else None,
        "licencia_estado": company.licencia_estado,
        "notificado_15_dias": company.notificado_15_dias,
        "is_active": company.is_active,
        "users": users,
    }


@router.get("/users")
async def admin_list_users(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(select(CompanyUser).order_by(CompanyUser.full_name))
    users = result.scalars().all()

    data = []
    for u in users:
        companies_result = await db.execute(
            select(UserCompany).where(UserCompany.user_id == u.id)
        )
        assignments = companies_result.scalars().all()
        data.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "companies": [
                {
                    "company_id": a.company_id,
                    "role": a.role,
                    "is_active": a.is_active,
                }
                for a in assignments
            ],
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return data


@router.post("/users")
async def admin_create_user(
    req: AdminCreateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    existing = await db.execute(select(CompanyUser).where(CompanyUser.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    company = await db.execute(select(Company).where(Company.id == req.company_id))
    if not company.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    user = CompanyUser(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
    )
    db.add(user)
    await db.flush()

    assignment = UserCompany(
        user_id=user.id,
        company_id=req.company_id,
        role=req.role,
    )
    db.add(assignment)
    await db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "company_id": req.company_id,
        "role": req.role,
    }


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(select(CompanyUser).where(CompanyUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    companies_result = await db.execute(
        select(UserCompany, Company.name, Company.ruc)
        .join(Company, Company.id == UserCompany.company_id)
        .where(UserCompany.user_id == user_id)
    )
    assignments = [
        {
            "company_id": row.UserCompany.company_id,
            "company_name": row.name,
            "company_ruc": row.ruc,
            "role": row.UserCompany.role,
            "is_active": row.UserCompany.is_active,
        }
        for row in companies_result.all()
    ]

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "companies": assignments,
    }


@router.get("/companies/{company_id}/users")
async def admin_company_users(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    company = await db.execute(select(Company).where(Company.id == company_id))
    if not company.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    result = await db.execute(
        select(CompanyUser, UserCompany)
        .join(UserCompany, UserCompany.user_id == CompanyUser.id)
        .where(UserCompany.company_id == company_id)
        .order_by(CompanyUser.full_name)
    )
    return [
        {
            "id": row.UserCompany.user_id,
            "email": row.CompanyUser.email,
            "full_name": row.CompanyUser.full_name,
            "role": row.UserCompany.role,
            "is_active": row.UserCompany.is_active,
        }
        for row in result.all()
    ]


@router.post("/companies/{company_id}/users")
async def admin_assign_user(
    company_id: str,
    req: AdminAssignUserRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    company = await db.execute(select(Company).where(Company.id == company_id))
    if not company.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    user = await db.execute(select(CompanyUser).where(CompanyUser.id == req.user_id))
    if not user.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    existing = await db.execute(
        select(UserCompany).where(
            UserCompany.user_id == req.user_id,
            UserCompany.company_id == company_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El usuario ya está asignado a esta empresa")

    assignment = UserCompany(
        user_id=req.user_id,
        company_id=company_id,
        role=req.role,
    )
    db.add(assignment)
    await db.commit()

    return {"message": "Usuario asignado correctamente"}


@router.put("/companies/{company_id}/users/{user_id}")
async def admin_update_assignment(
    company_id: str,
    user_id: str,
    req: AdminUpdateAssignmentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(
        select(UserCompany).where(
            UserCompany.user_id == user_id,
            UserCompany.company_id == company_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    if req.role is not None:
        assignment.role = req.role
    if req.is_active is not None:
        assignment.is_active = req.is_active
    await db.commit()

    return {"message": "Asignación actualizada correctamente"}


@router.delete("/companies/{company_id}/users/{user_id}")
async def admin_remove_assignment(
    company_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(
        select(UserCompany).where(
            UserCompany.user_id == user_id,
            UserCompany.company_id == company_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    await db.delete(assignment)
    await db.commit()

    return {"message": "Usuario removido de la empresa correctamente"}


@router.put("/companies/{company_id}/license")
async def admin_update_license(
    company_id: str,
    req: LicenseUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    from datetime import timedelta

    history = LicenseHistory(
        company_id=company_id,
        tipo="renovacion" if company.licencia_inicio else "contratacion",
        inicio_anterior=company.licencia_inicio,
        fin_anterior=company.licencia_fin,
        plan_anterior=company.plan_envios_mes,
        inicio_nuevo=req.licencia_inicio,
        fin_nuevo=req.licencia_fin,
        plan_nuevo=req.plan_envios_mes,
        creado_por=current_user["id"],
    )
    db.add(history)

    company.plan_envios_mes = req.plan_envios_mes
    company.licencia_inicio = req.licencia_inicio
    company.licencia_fin = req.licencia_fin
    company.licencia_grace_hasta = req.licencia_fin + timedelta(days=req.dias_gracia)
    company.licencia_estado = "activa"
    company.is_active = True
    company.notificado_15_dias = False

    await db.flush()
    return {"message": "Licencia actualizada correctamente"}


@router.get("/license/expiring")
async def admin_expiring_licenses(
    dias: int = 15,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)
    from datetime import timedelta
    target = date.today() + timedelta(days=dias)

    result = await db.execute(
        select(Company).where(
            Company.licencia_fin == target,
            Company.is_active == True,
        )
    )
    companies = result.scalars().all()

    return [{
        "id": c.id,
        "name": c.name,
        "ruc": c.ruc,
        "licencia_fin": str(c.licencia_fin),
        "plan_envios_mes": c.plan_envios_mes,
        "contacto": c.smtp_from_email,
    } for c in companies]


@router.get("/license/grace-period")
async def admin_grace_period(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(
        select(Company).where(Company.licencia_estado == "grace_period")
    )
    companies = result.scalars().all()

    data = []
    for c in companies:
        dias_restantes = (c.licencia_grace_hasta - date.today()).days if c.licencia_grace_hasta else 0
        data.append({
            "id": c.id,
            "name": c.name,
            "ruc": c.ruc,
            "grace_hasta": str(c.licencia_grace_hasta),
            "dias_restantes": max(0, dias_restantes),
            "contacto": c.smtp_from_email,
        })

    return data


@router.get("/stats")
async def admin_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    total = await db.execute(select(func.count(Company.id)))
    activas = await db.execute(
        select(func.count(Company.id)).where(
            Company.licencia_estado == "activa",
            Company.is_active == True,
        )
    )
    por_vencer = await db.execute(
        select(func.count(Company.id)).where(Company.notificado_15_dias == True)
    )
    grace = await db.execute(
        select(func.count(Company.id)).where(Company.licencia_estado == "grace_period")
    )
    bajas = await db.execute(
        select(func.count(Company.id)).where(
            Company.licencia_estado == "baja",
            Company.is_active == False,
        )
    )

    uploads_mes = await db.execute(
        select(func.count(PayrollUpload.id)).where(
            func.extract("year", PayrollUpload.created_at) == date.today().year,
            func.extract("month", PayrollUpload.created_at) == date.today().month,
        )
    )

    return {
        "total_empresas": total.scalar(),
        "activas": activas.scalar(),
        "por_vencer": por_vencer.scalar(),
        "grace_period": grace.scalar(),
        "bajas": bajas.scalar(),
        "uploads_del_mes": uploads_mes.scalar(),
    }


@router.get("/dashboard")
async def admin_dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)
    today = date.today()

    total = await db.execute(select(func.count(Company.id)))
    activas = await db.execute(
        select(func.count(Company.id)).where(Company.licencia_estado == "activa", Company.is_active == True)
    )
    por_vencer = await db.execute(
        select(func.count(Company.id)).where(Company.notificado_15_dias == True)
    )
    grace = await db.execute(
        select(func.count(Company.id)).where(Company.licencia_estado == "grace_period")
    )
    bajas = await db.execute(
        select(func.count(Company.id)).where(Company.licencia_estado == "baja", Company.is_active == False)
    )

    uploads_mes = await db.execute(
        select(func.count(PayrollUpload.id)).where(
            func.extract("year", PayrollUpload.created_at) == today.year,
            func.extract("month", PayrollUpload.created_at) == today.month,
        )
    )

    monthly_sends = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        sent = await db.execute(
            select(func.count(PaySlip.id)).where(
                PaySlip.estado_envio == "enviado",
                func.extract("year", PaySlip.enviado_en) == y,
                func.extract("month", PaySlip.enviado_en) == m,
            )
        )
        failed = await db.execute(
            select(func.count(PaySlip.id)).where(
                PaySlip.estado_envio == "fallido",
                func.extract("year", PaySlip.enviado_en) == y,
                func.extract("month", PaySlip.enviado_en) == m,
            )
        )
        monthly_sends.append({
            "mes": f"{y}-{m:02d}",
            "enviados": sent.scalar() or 0,
            "fallidos": failed.scalar() or 0,
        })

    daily_uploads = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        count = await db.execute(
            select(func.count(PayrollUpload.id)).where(
                func.date(PayrollUpload.created_at) == day,
            )
        )
        daily_uploads.append({
            "fecha": day.isoformat(),
            "subidas": count.scalar() or 0,
        })

    top_companies_result = await db.execute(
        select(
            Company.id, Company.name, Company.ruc,
            func.count(PayrollUpload.id).label("total_uploads"),
            func.coalesce(func.sum(PayrollUpload.total_enviados), 0).label("total_enviados"),
        )
        .join(PayrollUpload, PayrollUpload.company_id == Company.id, isouter=True)
        .group_by(Company.id, Company.name, Company.ruc)
        .order_by(text("total_enviados DESC"))
        .limit(10)
    )
    top_companies = [
        {"id": row.id, "name": row.name, "ruc": row.ruc,
         "total_uploads": row.total_uploads, "total_enviados": row.total_enviados or 0}
        for row in top_companies_result.all()
    ]

    return {
        "total_empresas": total.scalar(),
        "activas": activas.scalar(),
        "por_vencer": por_vencer.scalar(),
        "grace_period": grace.scalar(),
        "bajas": bajas.scalar(),
        "uploads_del_mes": uploads_mes.scalar(),
        "monthly_sends": monthly_sends,
        "daily_uploads": daily_uploads,
        "top_companies": top_companies,
    }


@router.get("/companies/{company_id}/license-history")
async def admin_license_history(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(
        select(LicenseHistory)
        .where(LicenseHistory.company_id == company_id)
        .order_by(LicenseHistory.created_at.desc())
    )
    history = result.scalars().all()

    return [{
        "id": h.id,
        "tipo": h.tipo,
        "inicio_anterior": str(h.inicio_anterior) if h.inicio_anterior else None,
        "fin_anterior": str(h.fin_anterior) if h.fin_anterior else None,
        "plan_anterior": h.plan_anterior,
        "inicio_nuevo": str(h.inicio_nuevo) if h.inicio_nuevo else None,
        "fin_nuevo": str(h.fin_nuevo) if h.fin_nuevo else None,
        "plan_nuevo": h.plan_nuevo,
        "notas": h.notas,
        "creado_en": h.created_at.isoformat() if h.created_at else None,
    } for h in history]


@router.get("/system-settings")
async def admin_get_system_settings(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    result = await db.execute(select(SystemSetting))
    rows = {r.key: r.value for r in result.scalars().all()}

    defaults = {
        "smtp_host": settings.SYSTEM_SMTP_HOST,
        "smtp_port": str(settings.SYSTEM_SMTP_PORT),
        "smtp_user": settings.SYSTEM_SMTP_USER,
        "smtp_password": settings.SYSTEM_SMTP_PASSWORD,
        "smtp_from_email": settings.SYSTEM_SMTP_FROM_EMAIL,
        "smtp_from_name": settings.SYSTEM_SMTP_FROM_NAME,
        "notification_email": "",
    }

    for k in defaults:
        if k not in rows:
            rows[k] = defaults[k]

    return rows


@router.put("/system-settings")
async def admin_update_system_settings(
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_super_admin(current_user)

    allowed_keys = {
        "smtp_host", "smtp_port", "smtp_user", "smtp_password",
        "smtp_from_email", "smtp_from_name", "notification_email",
    }

    for key, value in body.items():
        if key not in allowed_keys:
            continue
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = str(value)
        else:
            db.add(SystemSetting(key=key, value=str(value)))

    await db.commit()
    return {"message": "Configuración actualizada correctamente"}
