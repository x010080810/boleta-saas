from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.company import Company, CompanyUser, UserCompany, Employee, EmployeeCompany
from app.schemas.company import CompanyUpdate, EmployeeCreate, EmployeeBatchCreate, SmtpTestRequest
import smtplib
from email.mime.text import MIMEText

router = APIRouter()


@router.post("/test-smtp")
async def test_smtp_connection(req: SmtpTestRequest, current_user: dict = Depends(get_current_user)):
    try:
        msg = MIMEText(
            "Este es un correo de prueba desde Boleta SaaS.\n\n"
            "Si recibió este mensaje, la configuración SMTP es correcta."
        )
        msg["Subject"] = "Prueba SMTP - Boleta SaaS"
        msg["From"] = f"{req.from_name} <{req.from_email}>" if req.from_name else req.from_email
        msg["To"] = req.test_email

        server = smtplib.SMTP(req.smtp_host, req.smtp_port, timeout=15)
        server.starttls()
        server.login(req.smtp_user, req.smtp_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "message": "Conexión SMTP exitosa. Correo de prueba enviado."}
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=400, detail="Error de autenticación: usuario o contraseña incorrectos")
    except smtplib.SMTPConnectError:
        raise HTTPException(status_code=400, detail="No se pudo conectar al servidor SMTP. Verifique host y puerto")
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=400, detail=f"Error SMTP: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error de conexión: {str(e)}")


async def get_company_and_check_access(company_id: str, current_user: dict, db: AsyncSession):
    if current_user["type"] == "super_admin":
        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return company

    result = await db.execute(
        select(Company).join(UserCompany).where(
            Company.id == company_id,
            UserCompany.user_id == current_user["id"],
            UserCompany.is_active == True,
        )
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada o sin acceso")
    return company


@router.get("/")
async def list_companies(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user["type"] == "super_admin":
        result = await db.execute(select(Company).order_by(Company.name))
        companies = result.scalars().all()
    else:
        result = await db.execute(
            select(Company).join(UserCompany).where(
                UserCompany.user_id == current_user["id"],
                UserCompany.is_active == True,
            ).order_by(Company.name)
        )
        companies = result.scalars().all()

    return [{
        "id": c.id, "name": c.name, "ruc": c.ruc,
        "plan_envios_mes": c.plan_envios_mes,
        "licencia_estado": c.licencia_estado,
        "licencia_fin": str(c.licencia_fin) if c.licencia_fin else None,
        "is_active": c.is_active,
    } for c in companies]


@router.get("/{company_id}")
async def get_company(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(CompanyUser).join(UserCompany).where(UserCompany.company_id == company_id)
    )
    admins = [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in result.scalars().all()]

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
        "smtp_host": company.smtp_host,
        "smtp_port": company.smtp_port,
        "smtp_user": company.smtp_user,
        "smtp_from_email": company.smtp_from_email,
        "smtp_from_name": company.smtp_from_name,
        "email_subject_template": company.email_subject_template,
        "email_body_template": company.email_body_template,
        "lang": company.lang,
        "webhook_url": company.webhook_url,
        "is_active": company.is_active,
        "admins": admins,
    }


@router.put("/{company_id}")
async def update_company(
    company_id: str,
    req: CompanyUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.commit()
    return {"message": "Empresa actualizada correctamente"}


@router.get("/{company_id}/employees")
async def list_employees(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(Employee, EmployeeCompany)
        .join(EmployeeCompany, Employee.id == EmployeeCompany.employee_id)
        .where(EmployeeCompany.company_id == company_id, EmployeeCompany.is_active == True)
    )
    return [{
        "id": e.Employee.id,
        "tipo_documento": e.Employee.tipo_documento,
        "numero_documento": e.Employee.numero_documento,
        "nombre_completo": e.Employee.nombre_completo,
        "email": e.Employee.email,
        "cargo": e.EmployeeCompany.cargo,
        "fecha_ingreso": str(e.EmployeeCompany.fecha_ingreso) if e.EmployeeCompany.fecha_ingreso else None,
    } for e in result.all()]


@router.post("/{company_id}/employees")
async def create_employee(
    company_id: str,
    req: EmployeeCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(Employee).where(
            Employee.tipo_documento == req.tipo_documento,
            Employee.numero_documento == req.numero_documento,
        )
    )
    employee = result.scalar_one_or_none()

    if not employee:
        employee = Employee(
            tipo_documento=req.tipo_documento,
            numero_documento=req.numero_documento,
            nombre_completo=req.nombre_completo,
            email=req.email,
        )
        db.add(employee)
        await db.flush()

    existing = await db.execute(
        select(EmployeeCompany).where(
            EmployeeCompany.employee_id == employee.id,
            EmployeeCompany.company_id == company_id,
        )
    )
    if not existing.scalar_one_or_none():
        assignment = EmployeeCompany(
            employee_id=employee.id,
            company_id=company_id,
            cargo=req.cargo,
            fecha_ingreso=req.fecha_ingreso,
        )
        db.add(assignment)

    return {"message": "Empleado registrado correctamente", "id": employee.id}


@router.post("/{company_id}/employees/batch")
async def batch_create_employees(
    company_id: str,
    req: EmployeeBatchCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)
    results = []

    for emp in req.employees:
        result = await db.execute(
            select(Employee).where(
                Employee.tipo_documento == emp.tipo_documento,
                Employee.numero_documento == emp.numero_documento,
            )
        )
        employee = result.scalar_one_or_none()

        if not employee:
            employee = Employee(
                tipo_documento=emp.tipo_documento,
                numero_documento=emp.numero_documento,
                nombre_completo=emp.nombre_completo,
                email=emp.email,
            )
            db.add(employee)
            await db.flush()

        existing = await db.execute(
            select(EmployeeCompany).where(
                EmployeeCompany.employee_id == employee.id,
                EmployeeCompany.company_id == company_id,
            )
        )
        if not existing.scalar_one_or_none():
            assignment = EmployeeCompany(
                employee_id=employee.id,
                company_id=company_id,
                cargo=emp.cargo,
                fecha_ingreso=emp.fecha_ingreso,
            )
            db.add(assignment)

        results.append({"documento": emp.numero_documento, "nombre": emp.nombre_completo, "status": "ok"})

    return {"message": f"{len(results)} empleados procesados", "results": results}
