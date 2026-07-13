from datetime import datetime, timezone, date
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.celery_app import celery_app
from app.core.database import sync_session_factory
from app.models.company import Company, Employee, EmployeeCompany
from app.models.payroll import PayrollUpload, PaySlip, UnregisteredWorker
from app.models.email_log import EmailLog
from app.models.quota import MonthlySendQuota
from app.services.excel_parser import parse_excel
from app.services.pdf_generator import generate_payslip_pdf
from app.services.email_sender import send_payslip_email
from app.services.webhook import send_webhook
from app.core.config import settings


@celery_app.task(bind=True, max_retries=1, default_retry_delay=60)
def process_payroll_upload(self, upload_id: str, company_id: str):
    db = sync_session_factory()
    try:
        upload = db.execute(
            select(PayrollUpload).where(
                PayrollUpload.id == upload_id,
                PayrollUpload.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not upload or upload.estado != "processing":
            db.close()
            return

        company = db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
        if not company:
            db.close()
            return

        parsed = parse_excel(upload.file_path)
        empleados = parsed["empleados"]

        observaciones = []
        detalle_envios = []
        procesados = 0
        observados = 0

        ahora = date.today()
        mes_actual = ahora.month
        anio_actual = ahora.year

        quota = db.execute(
            select(MonthlySendQuota).where(
                MonthlySendQuota.company_id == company_id,
                MonthlySendQuota.anio == anio_actual,
                MonthlySendQuota.mes == mes_actual,
            )
        ).scalar_one_or_none()

        if not quota:
            quota = MonthlySendQuota(
                company_id=company_id,
                anio=anio_actual,
                mes=mes_actual,
                limite=company.plan_envios_mes,
                utilizados=0,
            )
            db.add(quota)
            db.flush()

        disponibles = quota.limite - quota.utilizados
        enviados_count = 0
        fallidos_count = 0
        sin_saldo_count = 0

        for emp in empleados:
            doc_type = emp.get("tipo_documento", "01")
            doc_num = str(emp.get("numero_documento", "")).strip()

            employee = db.execute(
                select(Employee)
                .options(selectinload(Employee.companies))
                .where(
                    Employee.tipo_documento == doc_type,
                    Employee.numero_documento == doc_num,
                )
            ).scalar_one_or_none()

            email_destino = emp.get("email", "")
            es_observacion = False
            motivo_obs = None

            if employee:
                email_excel = emp.get("email", "")
                if not email_excel and employee.email:
                    email_destino = employee.email
                cargo = emp.get("cargo", "")
                for comp in employee.companies or []:
                    if comp.company_id == company_id and comp.cargo:
                        cargo = comp.cargo
            else:
                es_observacion = True
                motivo_obs = "Empleado no registrado en el maestro"
                email_destino = emp.get("email", "") or company.smtp_from_email or ""
                if not email_destino:
                    email_destino = company.smtp_from_email or ""
                accion = "Boleta enviada al correo del archivo Excel" if emp.get("email") else "Boleta enviada al correo remitente de la empresa"
                observados += 1
                unreg = UnregisteredWorker(
                    payroll_upload_id=upload.id,
                    tipo_documento=doc_type,
                    numero_documento=doc_num,
                    nombre_completo=emp.get("apellidos_nombres", ""),
                    email_destino=email_destino,
                    datos_json=emp,
                )
                db.add(unreg)
                observaciones.append({
                    "fila": emp.get("_fila", 0),
                    "documento": doc_num,
                    "nombre": emp.get("apellidos_nombres", ""),
                    "motivo": motivo_obs,
                    "accion": accion,
                })

            ingresos = {k: v for k, v in emp.items() if k.startswith("ING_")}
            descuentos = {k: v for k, v in emp.items() if k.startswith("DESC_")}
            aportaciones = {k: v for k, v in emp.items() if k.startswith("APOR_")}

            pdf_path, pdf_password = generate_payslip_pdf(
                employee_name=emp.get("apellidos_nombres", ""),
                document_number=doc_num,
                company_name=company.name,
                company_ruc=company.ruc,
                periodo=f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
                tipo_planilla=upload.tipo_planilla,
                cargo=emp.get("cargo", ""),
                ingresos=ingresos,
                descuentos=descuentos,
                aportaciones=aportaciones,
                total_ingresos=emp.get("total_ingresos", 0),
                total_descuentos=emp.get("total_descuentos", 0),
                total_aportaciones=sum(v for v in aportaciones.values() if isinstance(v, (int, float))),
                neto_pagar=emp.get("neto_pagar", 0),
                neto_pagar_usd=emp.get("neto_pagar_usd"),
                ticket=upload.ticket_number,
                dias_laborados=emp.get("dias_laborados", 30),
                output_dir=settings.OUTPUT_DIR,
                s3_prefix=f"payslips/{company_id}/{upload_id}",
            )

            pay_slip = PaySlip(
                company_id=company_id,
                payroll_upload_id=upload.id,
                employee_id=employee.id if employee else None,
                tipo_documento=doc_type,
                numero_documento=doc_num,
                nombre_completo=emp.get("apellidos_nombres", ""),
                email_destino=email_destino,
                cargo=emp.get("cargo", ""),
                pdf_path=pdf_path,
                pdf_password=pdf_password,
                datos_json=emp,
                ingresos_json=ingresos,
                descuentos_json=descuentos,
                aportaciones_json=aportaciones,
                total_ingresos=float(emp.get("total_ingresos", 0) or 0),
                total_descuentos=float(emp.get("total_descuentos", 0) or 0),
                total_aportaciones=float(sum(v for v in aportaciones.values() if isinstance(v, (int, float)))),
                neto_pagar=float(emp.get("neto_pagar", 0) or 0),
                neto_pagar_usd=float(emp.get("neto_pagar_usd", 0)) if emp.get("neto_pagar_usd") else None,
                es_observacion=es_observacion,
                motivo_observacion=motivo_obs,
            )
            db.add(pay_slip)
            db.flush()

            if disponibles > 0:
                pay_slip.estado_envio = "enviado"
                enviados_count += 1
                disponibles -= 1
                quota.utilizados += 1

                email_result = send_payslip_email(
                    smtp_host=company.smtp_host,
                    smtp_port=company.smtp_port,
                    smtp_user=company.smtp_user,
                    smtp_password=company.smtp_password,
                    from_email=company.smtp_from_email,
                    from_name=company.smtp_from_name,
                    to_email=email_destino,
                    subject_template=company.email_subject_template,
                    body_template=company.email_body_template,
                    employee_name=emp.get("apellidos_nombres", ""),
                    company_name=company.name,
                    periodo=f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
                    ticket=upload.ticket_number,
                    pdf_path=pdf_path,
                    pdf_password=pdf_password,
                )

                if email_result["success"]:
                    pay_slip.estado_envio = "enviado"
                    pay_slip.enviado_en = datetime.now(timezone.utc)
                    pay_slip.error_message = None
                    email_log = EmailLog(
                        company_id=company_id,
                        pay_slip_id=pay_slip.id,
                        payroll_upload_id=upload.id,
                        destinatario_email=email_destino,
                        estado="sent",
                    )
                    db.add(email_log)
                    if company.webhook_url:
                        try:
                            send_webhook(
                                company_id=company_id,
                                event_type="payslip.sent",
                                payload={
                                    "event": "payslip.sent",
                                    "company_id": company_id,
                                    "pay_slip_id": pay_slip.id,
                                    "upload_id": upload.id,
                                    "ticket": upload.ticket_number,
                                    "employee_document": doc_num,
                                    "employee_name": emp.get("apellidos_nombres", ""),
                                    "email": email_destino,
                                    "periodo": f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                                webhook_url=company.webhook_url,
                            )
                        except Exception:
                            pass
                else:
                    pay_slip.estado_envio = "fallido"
                    pay_slip.error_message = email_result["error"]
                    fallidos_count += 1
                    email_log = EmailLog(
                        company_id=company_id,
                        pay_slip_id=pay_slip.id,
                        payroll_upload_id=upload.id,
                        destinatario_email=email_destino,
                        estado="failed",
                        error_message=email_result["error"],
                    )
                    db.add(email_log)
                    if company.webhook_url:
                        try:
                            send_webhook(
                                company_id=company_id,
                                event_type="payslip.failed",
                                payload={
                                    "event": "payslip.failed",
                                    "company_id": company_id,
                                    "pay_slip_id": pay_slip.id,
                                    "upload_id": upload.id,
                                    "ticket": upload.ticket_number,
                                    "employee_document": doc_num,
                                    "employee_name": emp.get("apellidos_nombres", ""),
                                    "email": email_destino,
                                    "error": email_result["error"],
                                    "periodo": f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                                webhook_url=company.webhook_url,
                            )
                        except Exception:
                            pass
            else:
                pay_slip.estado_envio = "no_enviado_sin_saldo"
                sin_saldo_count += 1
                email_log = EmailLog(
                    company_id=company_id,
                    pay_slip_id=pay_slip.id,
                    payroll_upload_id=upload.id,
                    destinatario_email=email_destino,
                    estado="no_enviado_sin_saldo",
                    error_message="Sin saldo disponible en el plan mensual",
                )
                db.add(email_log)
                observaciones.append({
                    "fila": emp.get("_fila", 0),
                    "documento": doc_num,
                    "nombre": emp.get("apellidos_nombres", ""),
                    "motivo": "Sin saldo disponible en el plan mensual",
                    "accion": "PDF generado pero no enviado",
                })

            detalle_envios.append({
                "fila": emp.get("_fila", 0),
                "documento": doc_num,
                "nombre": emp.get("apellidos_nombres", ""),
                "email_destino": email_destino + (" (por observación)" if es_observacion else ""),
                "estado": pay_slip.estado_envio,
                "error": pay_slip.error_message,
            })

            procesados += 1

        # Auto-registrar trabajadores no encontrados en el maestro
        unreg_result = db.execute(
            select(UnregisteredWorker).where(
                UnregisteredWorker.payroll_upload_id == upload.id
            )
        )
        for uw in unreg_result.scalars().all():
            existing = db.execute(
                select(Employee).where(
                    Employee.tipo_documento == uw.tipo_documento,
                    Employee.numero_documento == uw.numero_documento,
                )
            ).scalar_one_or_none()
            if existing:
                continue

            nombre = uw.nombre_completo
            email = None
            cargo = None
            if uw.datos_json:
                nombre = uw.datos_json.get("apellidos_nombres") or uw.nombre_completo
                email = uw.datos_json.get("email") or None
                cargo = uw.datos_json.get("cargo") or None

            new_emp = Employee(
                tipo_documento=uw.tipo_documento,
                numero_documento=uw.numero_documento,
                nombre_completo=nombre,
                email=email,
            )
            db.add(new_emp)
            db.flush()

            db.add(EmployeeCompany(
                employee_id=new_emp.id,
                company_id=company_id,
                cargo=cargo,
            ))

            for ps in db.execute(
                select(PaySlip).where(
                    PaySlip.payroll_upload_id == upload.id,
                    PaySlip.tipo_documento == uw.tipo_documento,
                    PaySlip.numero_documento == uw.numero_documento,
                )
            ).scalars().all():
                ps.employee_id = new_emp.id

        upload.total_procesados = procesados
        upload.total_observaciones = observados
        upload.total_enviados = enviados_count
        upload.total_fallidos = fallidos_count
        upload.total_sin_saldo = sin_saldo_count
        upload.estado = "completed"
        upload.ticket_enviado_en = datetime.now(timezone.utc)
        upload.resumen_json = {
            "ticket": upload.ticket_number,
            "tipo_planilla": upload.tipo_planilla,
            "periodo": f"{upload.periodo_mes:02d}/{upload.periodo_ano}",
            "total_registros": upload.total_registros,
            "total_procesados": procesados,
            "total_observaciones": observados,
            "total_enviados": enviados_count,
            "total_fallidos": fallidos_count,
            "total_sin_saldo": sin_saldo_count,
        }
        upload.observaciones_json = observaciones
        upload.detalle_envios_json = detalle_envios
        db.flush()

        if company.smtp_from_email:
            try:
                from app.services.email_sender import send_notification
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
                    usuario="Sistema",
                    total_registros=upload.total_registros,
                    total_procesados=upload.total_procesados,
                    total_observaciones=upload.total_observaciones,
                    total_enviados=upload.total_enviados,
                    total_fallidos=upload.total_fallidos,
                    total_sin_saldo=upload.total_sin_saldo,
                )
            except Exception as e:
                print(f"Error sending notification email: {e}")

        db.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            upload = db.execute(
                select(PayrollUpload).where(PayrollUpload.id == upload_id)
            ).scalar_one_or_none()
            if upload:
                upload.estado = "failed"
                upload.total_procesados = locals().get("procesados", 0)
                upload.total_observaciones = locals().get("observados", 0)
                upload.total_enviados = locals().get("enviados_count", 0)
                upload.total_fallidos = locals().get("fallidos_count", 0)
                upload.total_sin_saldo = locals().get("sin_saldo_count", 0)
                upload.resumen_json = {
                    "ticket": upload.ticket_number,
                    "tipo_planilla": upload.tipo_planilla,
                    "periodo": f"{upload.periodo_mes:02d}/{upload.periodo_ano}" if upload.periodo_mes else "",
                    "total_registros": upload.total_registros or 0,
                    "total_procesados": upload.total_procesados or 0,
                    "total_observaciones": upload.total_observaciones or 0,
                    "total_enviados": upload.total_enviados or 0,
                    "total_fallidos": upload.total_fallidos or 0,
                    "total_sin_saldo": upload.total_sin_saldo or 0,
                }
                upload.observaciones_json = locals().get("observaciones", []) or []
                upload.detalle_envios_json = locals().get("detalle_envios", []) or []
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()
