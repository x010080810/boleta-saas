from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.company import Company, Employee, EmployeeCompany
from app.models.payroll import PayrollUpload, PaySlip, UnregisteredWorker
from app.models.email_log import EmailLog
from app.models.quota import MonthlySendQuota
from app.schemas.payroll import ResendRequest
from app.services.excel_parser import parse_excel
from app.services.email_sender import send_payslip_email, send_notification
from app.services.pdf_generator import generate_payslip_pdf
from app.routers.companies import get_company_and_check_access
from app.tasks.payroll import process_payroll_upload
from app.core.rate_limit import limiter
from app.core.i18n import t, get_lang_from_header
from app.services.webhook import send_webhook
import os, json, uuid, io, zipfile
from datetime import datetime, timezone, date
from app.core.config import settings

router = APIRouter()


async def generate_ticket_number(company_id: str, anio: int, db: AsyncSession) -> str:
    result = await db.execute(
        select(PayrollUpload)
        .where(
            PayrollUpload.company_id == company_id,
            PayrollUpload.periodo_ano == anio,
        )
        .order_by(PayrollUpload.ticket_number.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()

    company = await db.execute(select(Company).where(Company.id == company_id))
    company = company.scalar_one_or_none()
    ruc = company.ruc if company else "00000000000"

    if last and last.ticket_number:
        parts = last.ticket_number.split("-")
        last_seq = int(parts[-1])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"BLP-{anio}-{ruc}-{new_seq:04d}"


@router.post("/upload")
@limiter.limit("5/minute")
async def upload_payroll(
    request: Request,
    company_id: str,
    file: UploadFile = File(...),
    tipo_planilla: str = Form(...),
    periodo_mes: int = Form(...),
    periodo_ano: int = Form(...),
    lang: str = "es",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)
    lang = company.lang or lang

    if company.licencia_estado not in ("activa", "por_vencer"):
        raise HTTPException(status_code=403, detail=t("license_inactive", lang, estado=company.licencia_estado))

    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail=t("invalid_format", lang))

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=t("file_too_large", lang, max_size=settings.MAX_UPLOAD_SIZE_MB))

    if len(content) < 8:
        raise HTTPException(status_code=400, detail=t("invalid_format", lang))
    magic = content[:8]
    is_xls = magic[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    is_xlsx = magic[:4] == b'\x50\x4b\x03\x04'
    if not is_xls and not is_xlsx:
        raise HTTPException(status_code=400, detail=t("invalid_format", lang))

    filepath = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(filepath, "wb") as f:
        f.write(content)
    content = None  # liberar memoria

    ticket = await generate_ticket_number(company_id, periodo_ano, db)

    upload = PayrollUpload(
        company_id=company_id,
        ticket_number=ticket,
        tipo_planilla=tipo_planilla,
        periodo_mes=periodo_mes,
        periodo_ano=periodo_ano,
        filename=file.filename,
        file_path=filepath,
        estado="pending",
    )
    db.add(upload)
    await db.flush()

    parsed = parse_excel(filepath)

    upload.total_registros = len(parsed["empleados"])
    await db.flush()

    return {
        "ticket": ticket,
        "upload_id": upload.id,
        "registros_detectados": len(parsed["empleados"]),
        "columnas_ing": parsed["columnas_ing"],
        "columnas_desc": parsed["columnas_desc"],
        "columnas_apor": parsed["columnas_apor"],
    }


@router.get("/uploads")
async def list_uploads(
    company_id: str,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    ticket: str = None,
    tipo_planilla: str = None,
    periodo_mes: int = None,
    periodo_ano: int = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    query = select(PayrollUpload).where(PayrollUpload.company_id == company_id)

    if ticket:
        query = query.where(PayrollUpload.ticket_number.ilike(f"%{ticket}%"))
    if tipo_planilla:
        query = query.where(PayrollUpload.tipo_planilla == tipo_planilla)
    if periodo_mes:
        query = query.where(PayrollUpload.periodo_mes == periodo_mes)
    if periodo_ano:
        query = query.where(PayrollUpload.periodo_ano == periodo_ano)
    if fecha_desde:
        query = query.where(PayrollUpload.created_at >= datetime.fromisoformat(fecha_desde))
    if fecha_hasta:
        query = query.where(PayrollUpload.created_at <= datetime.fromisoformat(fecha_hasta))

    query = query.order_by(PayrollUpload.created_at.desc())
    result = await db.execute(query)
    uploads = result.scalars().all()

    return [{
        "id": u.id,
        "ticket_number": u.ticket_number,
        "tipo_planilla": u.tipo_planilla,
        "periodo": f"{u.periodo_mes:02d}/{u.periodo_ano}",
        "filename": u.filename,
        "total_registros": u.total_registros,
        "total_procesados": u.total_procesados,
        "total_observaciones": u.total_observaciones,
        "total_enviados": u.total_enviados,
        "total_fallidos": u.total_fallidos,
        "total_sin_saldo": u.total_sin_saldo,
        "estado": u.estado,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in uploads]


@router.get("/uploads/{upload_id}/preview")
async def preview_upload(
    company_id: str,
    upload_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PayrollUpload).where(
            PayrollUpload.id == upload_id,
            PayrollUpload.company_id == company_id,
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")

    parsed = parse_excel(upload.file_path)
    empleados = parsed["empleados"]

    preview_data = []
    for emp in empleados:
        emp_result = await db.execute(
            select(Employee).where(
                Employee.tipo_documento == emp.get("tipo_documento", ""),
                Employee.numero_documento == emp.get("numero_documento", ""),
            )
        )
        registered = emp_result.scalar_one_or_none() is not None

        preview_data.append({
            "fila": emp.get("_fila", 0),
            "tipo_documento": emp.get("tipo_documento", ""),
            "numero_documento": emp.get("numero_documento", ""),
            "nombre_completo": emp.get("apellidos_nombres", ""),
            "email": emp.get("email", ""),
            "cargo": emp.get("cargo", ""),
            "total_ingresos": emp.get("total_ingresos", 0),
            "total_descuentos": emp.get("total_descuentos", 0),
            "neto_pagar": emp.get("neto_pagar", 0),
            "registrado_en_maestro": registered,
        })

    return {
        "ticket": upload.ticket_number,
        "tipo_planilla": upload.tipo_planilla,
        "periodo": f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
        "total_empleados": len(preview_data),
        "empleados": preview_data,
    }


@router.post("/uploads/{upload_id}/process")
async def process_upload(
    company_id: str,
    upload_id: str,
    lang: str = "es",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)
    lang = company.lang or lang

    result = await db.execute(
        select(PayrollUpload).where(
            PayrollUpload.id == upload_id,
            PayrollUpload.company_id == company_id,
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail=t("upload_not_found", lang))

    if upload.estado not in ("pending",):
        raise HTTPException(status_code=400, detail=t("already_processed", lang, estado=upload.estado))

    upload.estado = "processing"
    upload.procesado_en = datetime.now(timezone.utc)
    await db.commit()

    process_payroll_upload.delay(upload_id, company_id)

    return {
        "ticket": upload.ticket_number,
        "upload_id": upload.id,
        "estado": "processing",
        "message": "Procesamiento iniciado en segundo plano",
    }


@router.get("/uploads/{upload_id}/boletas")
async def list_boletas(
    company_id: str,
    upload_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PaySlip).where(
            PaySlip.company_id == company_id,
            PaySlip.payroll_upload_id == upload_id,
        ).order_by(PaySlip.created_at)
    )
    boletas = result.scalars().all()

    return [{
        "id": b.id,
        "tipo_documento": b.tipo_documento,
        "numero_documento": b.numero_documento,
        "nombre_completo": b.nombre_completo,
        "email_destino": b.email_destino,
        "total_ingresos": b.total_ingresos,
        "total_descuentos": b.total_descuentos,
        "neto_pagar": b.neto_pagar,
        "es_observacion": b.es_observacion,
        "motivo_observacion": b.motivo_observacion,
        "estado_envio": b.estado_envio,
        "error_message": b.error_message,
        "enviado_en": b.enviado_en.isoformat() if b.enviado_en else None,
        "batch_key": b.batch_key,
    } for b in boletas]


@router.get("/uploads/{upload_id}/status")
async def upload_status(
    company_id: str,
    upload_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PayrollUpload).where(
            PayrollUpload.id == upload_id,
            PayrollUpload.company_id == company_id,
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")

    return {
        "ticket": upload.ticket_number,
        "estado": upload.estado,
        "total_registros": upload.total_registros,
        "total_procesados": upload.total_procesados,
        "total_observaciones": upload.total_observaciones,
        "total_enviados": upload.total_enviados,
        "total_fallidos": upload.total_fallidos,
        "total_sin_saldo": upload.total_sin_saldo,
    }


@router.get("/uploads/{upload_id}/report")
async def upload_report(
    company_id: str,
    upload_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PayrollUpload).where(
            PayrollUpload.id == upload_id,
            PayrollUpload.company_id == company_id,
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")

    return {
        "ticket": upload.ticket_number,
        "tipo_planilla": upload.tipo_planilla,
        "periodo": f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
        "resumen": upload.resumen_json,
        "observaciones": upload.observaciones_json or [],
        "detalle_envios": upload.detalle_envios_json or [],
    }


@router.get("/boletas/{pay_slip_id}/download")
async def download_boleta(
    company_id: str,
    pay_slip_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import Response
    from app.services.storage import read_pdf
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PaySlip).where(
            PaySlip.id == pay_slip_id,
            PaySlip.company_id == company_id,
        )
    )
    boleta = result.scalar_one_or_none()
    if not boleta or not boleta.pdf_path:
        raise HTTPException(status_code=404, detail="Boleta no encontrada")

    pdf_bytes = read_pdf(boleta.pdf_path)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado en almacenamiento")

    filename = f"boleta_{boleta.numero_documento}_{boleta.nombre_completo[:30].replace(' ', '_')}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/uploads/{upload_id}/download-all")
async def download_all_boletas(
    company_id: str,
    upload_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import StreamingResponse
    await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PayrollUpload).where(
            PayrollUpload.id == upload_id,
            PayrollUpload.company_id == company_id,
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")

    result = await db.execute(
        select(PaySlip).where(
            PaySlip.company_id == company_id,
            PaySlip.payroll_upload_id == upload_id,
            PaySlip.pdf_path.isnot(None),
        )
    )
    boletas = result.scalars().all()

    buf = io.BytesIO()
    from app.services.storage import read_pdf as read_pdf_s3
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for b in boletas:
            pdf_data = read_pdf_s3(b.pdf_path) if b.pdf_path else None
            if pdf_data:
                arcname = f"boleta_{b.numero_documento}_{b.nombre_completo[:30].replace(' ', '_')}.pdf"
                zf.writestr(arcname, pdf_data)
    buf.seek(0)

    filename = f"boletas_{upload.ticket_number}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/uploads/{upload_id}/resend")
@limiter.limit("3/minute")
async def resend_boletas(
    request: Request,
    company_id: str,
    upload_id: str,
    req: ResendRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)

    query = select(PaySlip).where(
        PaySlip.company_id == company_id,
        PaySlip.payroll_upload_id == upload_id,
    )

    if req.tipo == "selected" and req.pay_slip_ids:
        query = query.where(PaySlip.id.in_(req.pay_slip_ids))

    result = await db.execute(query)
    boletas = result.scalars().all()

    ahora = date.today()
    quota_result = await db.execute(
        select(MonthlySendQuota).where(
            MonthlySendQuota.company_id == company_id,
            MonthlySendQuota.anio == ahora.year,
            MonthlySendQuota.mes == ahora.month,
        )
    )
    quota = quota_result.scalar_one_or_none()
    if not quota:
        quota = MonthlySendQuota(
            company_id=company_id,
            anio=ahora.year,
            mes=ahora.month,
            limite=company.plan_envios_mes,
            utilizados=0,
        )
        db.add(quota)
        await db.flush()

    disponibles = quota.limite - quota.utilizados
    enviados = 0

    for boleta in boletas:
        if disponibles <= 0:
            break

        to_email = boleta.email_destino
        if boleta.employee_id:
            emp_result = await db.execute(
                select(Employee).where(Employee.id == boleta.employee_id)
            )
            emp = emp_result.scalar_one_or_none()
            if emp and emp.email:
                to_email = emp.email

        email_result = send_payslip_email(
            smtp_host=company.smtp_host,
            smtp_port=company.smtp_port,
            smtp_user=company.smtp_user,
            smtp_password=company.smtp_password,
            from_email=company.smtp_from_email,
            from_name=company.smtp_from_name,
            to_email=to_email,
            subject_template=company.email_subject_template,
            body_template=company.email_body_template,
            employee_name=boleta.nombre_completo,
            company_name=company.name,
            periodo="",
            ticket="",
            pdf_path=boleta.pdf_path,
            pdf_password=boleta.pdf_password,
        )

        boleta.batch_key = f"resend_{ahora.month}_{ahora.day}"
        if email_result["success"]:
            boleta.estado_envio = "enviado"
            boleta.enviado_en = datetime.now(timezone.utc)
            boleta.error_message = None
            enviados += 1
            disponibles -= 1
            quota.utilizados += 1
            if company.webhook_url:
                send_webhook(
                    company_id=company_id,
                    event_type="payslip.resend.sent",
                    payload={
                        "event": "payslip.resend.sent",
                        "company_id": company_id,
                        "pay_slip_id": boleta.id,
                        "upload_id": upload_id,
                        "ticket": upload.ticket_number if 'upload' in dir() else None,
                        "employee_document": boleta.numero_documento,
                        "employee_name": boleta.nombre_completo,
                        "email": boleta.email_destino,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    webhook_url=company.webhook_url,
                )
        else:
            boleta.estado_envio = "fallido"
            boleta.error_message = email_result["error"]
            if company.webhook_url:
                send_webhook(
                    company_id=company_id,
                    event_type="payslip.resend.failed",
                    payload={
                        "event": "payslip.resend.failed",
                        "company_id": company_id,
                        "pay_slip_id": boleta.id,
                        "upload_id": upload_id,
                        "employee_document": boleta.numero_documento,
                        "employee_name": boleta.nombre_completo,
                        "email": boleta.email_destino,
                        "error": email_result["error"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    webhook_url=company.webhook_url,
                )

        email_log = EmailLog(
            company_id=company_id,
            pay_slip_id=boleta.id,
            payroll_upload_id=upload_id,
            batch_key=boleta.batch_key,
            destinatario_email=boleta.email_destino,
            estado=boleta.estado_envio,
            error_message=boleta.error_message,
        )
        db.add(email_log)

    await db.flush()
    return {"message": f"Re-enviadas {enviados} boletas", "enviados": enviados}


@router.post("/boletas/{pay_slip_id}/resend")
@limiter.limit("5/minute")
async def resend_individual_boleta(
    request: Request,
    company_id: str,
    pay_slip_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)

    result = await db.execute(
        select(PaySlip).where(
            PaySlip.id == pay_slip_id,
            PaySlip.company_id == company_id,
        )
    )
    boleta = result.scalar_one_or_none()
    if not boleta:
        raise HTTPException(status_code=404, detail="Boleta no encontrada")

    ahora = date.today()
    quota_result = await db.execute(
        select(MonthlySendQuota).where(
            MonthlySendQuota.company_id == company_id,
            MonthlySendQuota.anio == ahora.year,
            MonthlySendQuota.mes == ahora.month,
        )
    )
    quota = quota_result.scalar_one_or_none()
    if not quota:
        quota = MonthlySendQuota(
            company_id=company_id,
            anio=ahora.year,
            mes=ahora.month,
            limite=company.plan_envios_mes,
            utilizados=0,
        )
        db.add(quota)
        await db.flush()

    disponibles = quota.limite - quota.utilizados
    if disponibles <= 0:
        raise HTTPException(status_code=429, detail="Sin saldo disponible en el plan mensual")

    to_email = boleta.email_destino
    if boleta.employee_id:
        emp_result = await db.execute(
            select(Employee).where(Employee.id == boleta.employee_id)
        )
        emp = emp_result.scalar_one_or_none()
        if emp and emp.email:
            to_email = emp.email

    email_result = send_payslip_email(
        smtp_host=company.smtp_host,
        smtp_port=company.smtp_port,
        smtp_user=company.smtp_user,
        smtp_password=company.smtp_password,
        from_email=company.smtp_from_email,
        from_name=company.smtp_from_name,
        to_email=to_email,
        subject_template=company.email_subject_template,
        body_template=company.email_body_template,
        employee_name=boleta.nombre_completo,
        company_name=company.name,
        periodo="",
        ticket="",
        pdf_path=boleta.pdf_path,
        pdf_password=boleta.pdf_password,
    )

    boleta.batch_key = f"resend_{ahora.month}_{ahora.day}"
    if email_result["success"]:
        boleta.estado_envio = "enviado"
        boleta.enviado_en = datetime.now(timezone.utc)
        boleta.error_message = None
        quota.utilizados += 1
        if company.webhook_url:
            send_webhook(
                company_id=company_id,
                event_type="payslip.resend.sent",
                payload={
                    "event": "payslip.resend.sent",
                    "company_id": company_id,
                    "pay_slip_id": pay_slip_id,
                    "employee_document": boleta.numero_documento,
                    "employee_name": boleta.nombre_completo,
                    "email": boleta.email_destino,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                webhook_url=company.webhook_url,
            )
    else:
        boleta.estado_envio = "fallido"
        boleta.error_message = email_result["error"]
        if company.webhook_url:
            send_webhook(
                company_id=company_id,
                event_type="payslip.resend.failed",
                payload={
                    "event": "payslip.resend.failed",
                    "company_id": company_id,
                    "pay_slip_id": pay_slip_id,
                    "employee_document": boleta.numero_documento,
                    "employee_name": boleta.nombre_completo,
                    "email": boleta.email_destino,
                    "error": email_result["error"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                webhook_url=company.webhook_url,
            )

    email_log = EmailLog(
        company_id=company_id,
        pay_slip_id=boleta.id,
        payroll_upload_id=boleta.payroll_upload_id,
        batch_key=boleta.batch_key,
        destinatario_email=boleta.email_destino,
        estado=boleta.estado_envio,
        error_message=boleta.error_message,
    )
    db.add(email_log)
    await db.flush()

    return {
        "message": "Boleta re-enviada" if email_result["success"] else "Error al re-enviar",
        "pay_slip_id": pay_slip_id,
        "estado": boleta.estado_envio,
        "error": boleta.error_message,
    }


@router.get("/quota-status")
async def quota_status(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await get_company_and_check_access(company_id, current_user, db)
    ahora = date.today()

    result = await db.execute(
        select(MonthlySendQuota).where(
            MonthlySendQuota.company_id == company_id,
            MonthlySendQuota.anio == ahora.year,
            MonthlySendQuota.mes == ahora.month,
        )
    )
    quota = result.scalar_one_or_none()

    if not quota:
        return {
            "mes": ahora.month,
            "anio": ahora.year,
            "limite": company.plan_envios_mes,
            "utilizados": 0,
            "disponibles": company.plan_envios_mes,
        }

    return {
        "mes": quota.mes,
        "anio": quota.anio,
        "limite": quota.limite,
        "utilizados": quota.utilizados,
        "disponibles": quota.limite - quota.utilizados,
    }


def send_notification_email(company, upload, admin_name):
    from app.services.email_sender import send_notification
    try:
        send_notification(
            smtp_host=company.smtp_host,
            smtp_port=company.smtp_port,
            smtp_user=company.smtp_user,
            smtp_password=company.smtp_password,
            from_email=company.smtp_from_email,
            from_name=company.smtp_from_name,
            to_email=company.smtp_from_email,
            ticket=upload.ticket_number,
            tipo_planilla=upload.tipo_planilla,
            periodo=f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
            empresa=company.name,
            usuario=admin_name,
            total_registros=upload.total_registros,
            total_procesados=upload.total_procesados,
            total_observaciones=upload.total_observaciones,
            total_enviados=upload.total_enviados,
            total_fallidos=upload.total_fallidos,
            total_sin_saldo=upload.total_sin_saldo,
        )
    except Exception as e:
        print(f"Error sending notification email: {e}")
