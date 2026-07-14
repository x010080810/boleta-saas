import smtplib
import os
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import formataddr, formatdate
from html import escape
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "email")


def _connect_smtp(host: str, port: int, user: str, password: str, timeout: int = 30):
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=timeout)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)
        server.starttls()
    server.login(user, password)
    return server


def _get_resend_api_key() -> str:
    return os.environ.get("RESEND_API_KEY") or settings.RESEND_API_KEY or ""


def _get_sendgrid_api_key() -> str:
    return os.environ.get("SENDGRID_API_KEY") or settings.SENDGRID_API_KEY or ""


def _get_mailtrap_api_token() -> str:
    return os.environ.get("MAILTRAP_API_TOKEN") or getattr(settings, "MAILTRAP_API_TOKEN", "") or ""


def _has_gmail_token() -> bool:
    return bool(os.environ.get("GMAIL_TOKEN_JSON"))


def _send_via_gmail(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str,
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    try:
        from app.services.gmail_sender import send_via_gmail_api
        return send_via_gmail_api(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def _send_via_resend(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str = "",
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    try:
        from app.services.resend_sender import send_via_resend
        return send_via_resend(
            to_email=to_email, subject=subject, html_body=html_body,
            from_email=from_email, from_name=from_name,
            pdf_bytes=pdf_bytes, pdf_filename=pdf_filename,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def _send_via_mailtrap(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str = "",
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    try:
        from app.services.mailtrap_sender import send_via_mailtrap
        return send_via_mailtrap(
            to_email=to_email, subject=subject, html_body=html_body,
            from_email=from_email, from_name=from_name,
            pdf_bytes=pdf_bytes, pdf_filename=pdf_filename,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def _dispatch_email(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str,
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    methods = []
    if _get_resend_api_key():
        methods.append(("Resend", lambda: _send_via_resend(to_email, subject, html_body, from_email, from_name, pdf_bytes, pdf_filename)))
    if _has_gmail_token():
        methods.append(("Gmail API", lambda: _send_via_gmail(to_email, subject, html_body, from_email, from_name, pdf_bytes, pdf_filename)))
    api_key = _get_sendgrid_api_key()
    if api_key:
        methods.append(("SendGrid", lambda: _send_via_sendgrid(to_email, subject, html_body, from_email, from_name, pdf_bytes, pdf_filename)))
    if _get_mailtrap_api_token():
        methods.append(("Mailtrap", lambda: _send_via_mailtrap(to_email, subject, html_body, from_email, from_name, pdf_bytes, pdf_filename)))

    if not methods:
        return {"success": False, "error": "No hay metodo de envio configurado (Resend, Gmail API, SendGrid ni Mailtrap)"}

    errors = []
    for name, send_fn in methods:
        try:
            result = send_fn()
            if result.get("success"):
                return result
            errors.append(f"{name}: {result.get('error', 'error desconocido')}")
        except Exception as e:
            errors.append(f"{name}: {str(e)}")

    return {"success": False, "error": "; ".join(errors)}


def _send_via_sendgrid(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str,
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    api_key = _get_sendgrid_api_key()
    if not api_key:
        return {"success": False, "error": "SENDGRID_API_KEY no configurado"}

    try:
        from app.services.sendgrid_sender import send_via_sendgrid
        return send_via_sendgrid(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_headers(msg: MIMEMultipart, from_email: str, from_name: str, to_email: str) -> None:
    msg["Message-ID"] = f"<{uuid.uuid4().hex}@{from_email.split('@')[-1] or 'boletasapp.com'}>"
    msg["Date"] = formatdate(timeval=datetime.now(timezone.utc).timestamp(), localtime=False, usegmt=True)
    msg["X-Mailer"] = "BoletaSaaS/1.0"


def _strip_html(body_html: str) -> str:
    import re
    clean = re.sub(r"<[^>]+>", " ", body_html)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _attach_html_alternative(msg: MIMEMultipart, html_body: str) -> None:
    msg.attach(MIMEText(html_body, "html", "utf-8"))


def send_payslip_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
    from_name: str,
    to_email: str,
    subject_template: str,
    body_template: str,
    employee_name: str,
    company_name: str,
    periodo: str,
    ticket: str,
    pdf_path: str,
    pdf_password: str,
) -> dict:
    from app.services.storage import read_pdf as _read_pdf_s3
    pdf_bytes = _read_pdf_s3(pdf_path) if pdf_path else b""
    pdf_filename = pdf_path.split("/")[-1] if pdf_path else "boleta.pdf"

    if _get_resend_api_key() or _has_gmail_token() or _get_sendgrid_api_key() or _get_mailtrap_api_token():
        subject = (subject_template or "Boleta de Pago - {{empresa}}").replace("{{empresa}}", company_name).replace("{{empleado}}", employee_name)
        body = (body_template or """
<html><body>
<p>Estimado(a) <strong>{{empleado}}</strong>,</p>
<p>Adjunto su boleta de pago de <strong>{{empresa}}</strong> - periodo {{periodo}}.</p>
<p>Ticket: {{ticket}}</p>
</body></html>
""").replace("{{empleado}}", employee_name).replace("{{empresa}}", company_name).replace("{{periodo}}", periodo).replace("{{ticket}}", ticket)
        return _dispatch_email(
            to_email=to_email, subject=subject, html_body=body,
            from_email=from_email, from_name=from_name,
            pdf_bytes=pdf_bytes, pdf_filename=pdf_filename,
        )

    if not all([smtp_host, smtp_user, smtp_password, from_email, to_email]):
        return {"success": False, "error": "Configuración SMTP incompleta"}

    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = formataddr((from_name or company_name, from_email))
        msg["To"] = to_email
        msg["Reply-To"] = from_email

        _build_headers(msg, from_email, from_name, to_email)

        subject = (subject_template or "Boleta de Pago - {{empresa}} - {{periodo}}")
        subject = subject.replace("{{nombre}}", employee_name)
        subject = subject.replace("{{empresa}}", company_name)
        subject = subject.replace("{{periodo}}", periodo)
        subject = subject.replace("{{ticket}}", ticket)
        msg["Subject"] = subject

        body = (body_template or """
        <html><body>
        <p>Estimado(a) <strong>{{nombre}}</strong>,</p>
        <p>Su boleta de pago correspondiente a <strong>{{empresa}}</strong> - periodo {{periodo}} ha sido generada.</p>
        <p>Adjunto encontrara su boleta de pago en formato PDF.</p>
        <p>Ticket de referencia: {{ticket}}</p>
        <br>
        <p>Saludos cordiales,</p>
        <p><strong>{{empresa}}</strong></p>
        </body></html>
        """)
        body = body.replace("{{nombre}}", employee_name)
        body = body.replace("{{empresa}}", company_name)
        body = body.replace("{{periodo}}", periodo)
        body = body.replace("{{ticket}}", ticket)

        msg.attach(MIMEText(body, "html", "utf-8"))

        if pdf_bytes:
            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{pdf_filename}"',
            )
            msg.attach(part)

        server = _connect_smtp(smtp_host, smtp_port, smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _render_notification_body(ticket, tipo_planilla, periodo, empresa, usuario,
                               total_registros, total_procesados, total_observaciones,
                               total_enviados, total_fallidos, total_sin_saldo):
    return f"""
    <html><body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Procesamiento de Planilla Completado</h2>
        <p>Estimado(a) <strong>{usuario}</strong>,</p>
        <p>El procesamiento de su planilla ha sido completado exitosamente.</p>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Ticket</strong></td>
                <td style="padding: 8px;">{ticket}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Tipo</strong></td>
                <td style="padding: 8px;">{tipo_planilla}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Periodo</strong></td>
                <td style="padding: 8px;">{periodo}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Total registros</strong></td>
                <td style="padding: 8px;">{total_registros}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Procesados</strong></td>
                <td style="padding: 8px;">{total_procesados}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Observaciones</strong></td>
                <td style="padding: 8px; color: {'orange' if total_observaciones > 0 else 'green'};">{total_observaciones}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Envios exitosos</strong></td>
                <td style="padding: 8px; color: green;">{total_enviados}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Envios fallidos</strong></td>
                <td style="padding: 8px; color: {'red' if total_fallidos > 0 else 'green'};">{total_fallidos}</td></tr>
            <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Sin saldo</strong></td>
                <td style="padding: 8px; color: {'red' if total_sin_saldo > 0 else 'green'};">{total_sin_saldo}</td></tr>
        </table>

        <p>Puede consultar el reporte detallado ingresando al sistema con el ticket: <strong>{ticket}</strong></p>
        <br>
        <p>Saludos cordiales,<br><strong>Sistema de Boletas de Pago</strong></p>
    </div>
    </body></html>
    """


def send_notification(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
    from_name: str,
    to_email: str,
    ticket: str,
    tipo_planilla: str,
    periodo: str,
    empresa: str,
    usuario: str,
    total_registros: int,
    total_procesados: int,
    total_observaciones: int,
    total_enviados: int,
    total_fallidos: int,
    total_sin_saldo: int,
) -> dict:
    if _get_resend_api_key() or _has_gmail_token() or _get_sendgrid_api_key() or _get_mailtrap_api_token():
        body = _render_notification_body(ticket, tipo_planilla, periodo, empresa, usuario,
                                          total_registros, total_procesados, total_observaciones,
                                          total_enviados, total_fallidos, total_sin_saldo)
        return _dispatch_email(
            to_email=to_email,
            subject=f"Procesamiento de Planilla Completado - Ticket #{ticket} | {empresa}",
            html_body=body,
            from_email=from_email,
            from_name=from_name,
        )

    if not all([smtp_host, smtp_user, smtp_password, from_email, to_email]):
        return {"success": False, "error": "Configuración SMTP incompleta"}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((from_name or empresa, from_email))
        msg["To"] = to_email
        msg["Reply-To"] = from_email
        msg["Subject"] = f"Procesamiento de Planilla Completado - Ticket #{ticket} | {empresa}"

        _build_headers(msg, from_email, from_name, to_email)

        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Procesamiento de Planilla Completado</h2>
            <p>Estimado(a) <strong>{usuario}</strong>,</p>
            <p>El procesamiento de su planilla ha sido completado exitosamente.</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Ticket</strong></td>
                    <td style="padding: 8px;">{ticket}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Tipo</strong></td>
                    <td style="padding: 8px;">{tipo_planilla}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Periodo</strong></td>
                    <td style="padding: 8px;">{periodo}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Total registros</strong></td>
                    <td style="padding: 8px;">{total_registros}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Procesados</strong></td>
                    <td style="padding: 8px;">{total_procesados}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Observaciones</strong></td>
                    <td style="padding: 8px; color: {'orange' if total_observaciones > 0 else 'green'};">{total_observaciones}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Envios exitosos</strong></td>
                    <td style="padding: 8px; color: green;">{total_enviados}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Envios fallidos</strong></td>
                    <td style="padding: 8px; color: {'red' if total_fallidos > 0 else 'green'};">{total_fallidos}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Sin saldo</strong></td>
                    <td style="padding: 8px; color: {'red' if total_sin_saldo > 0 else 'green'};">{total_sin_saldo}</td></tr>
            </table>

            <p>Puede consultar el reporte detallado ingresando al sistema con el ticket: <strong>{ticket}</strong></p>
            <br>
            <p>Saludos cordiales,<br><strong>Sistema de Boletas de Pago</strong></p>
        </div>
        </body></html>
        """

        _attach_html_alternative(msg, body)

        server = _connect_smtp(smtp_host, smtp_port, smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}


def send_welcome_email(
    system_smtp_host: str,
    system_smtp_port: int,
    system_smtp_user: str,
    system_smtp_password: str,
    system_from_email: str,
    system_from_name: str,
    to_email: str,
    admin_name: str,
    company_name: str,
    company_ruc: str,
    plan_envios: int,
    dias_vigencia: int,
    licencia_inicio: str = "",
    licencia_fin: str = "",
) -> dict:
    if _get_resend_api_key() or _has_gmail_token() or _get_sendgrid_api_key() or _get_mailtrap_api_token():
        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Boleta SaaS</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">Sistema de Boletas de Pago</p>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
                <p>Estimado(a) <strong>{admin_name}</strong>,</p>
                <p>Su empresa <strong>{company_name}</strong> (RUC: {company_ruc}) ha sido registrada exitosamente en <strong>Boleta SaaS</strong>.</p>
                <div style="background: #f0fdf4; border: 1px solid #22c55e; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #166534; margin: 0 0 10px;">Plan de Prueba Gratuito</h3>
                    <table style="width: 100%;">
                        <tr><td style="padding: 4px 0;"><strong>Envios mensuales:</strong></td><td style="text-align: right;">{plan_envios} envios/mes</td></tr>
                        <tr><td style="padding: 4px 0;"><strong>Inicio:</strong></td><td style="text-align: right;">{licencia_inicio}</td></tr>
                        <tr><td style="padding: 4px 0;"><strong>Vence:</strong></td><td style="text-align: right;">{licencia_fin}</td></tr>
                        <tr><td style="padding: 4px 0;"><strong>Vigencia:</strong></td><td style="text-align: right;">{dias_vigencia} dias</td></tr>
                    </table>
                </div>
                <p>Puede ingresar al sistema con su correo electronico:</p>
                <p style="text-align: center; font-size: 16px; color: #3b82f6;"><strong>{to_email}</strong></p>
                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">Si usted no realizo este registro, ignore este mensaje.</p>
                <p style="color: #6b7280; font-size: 12px;">Saludos cordiales,<br><strong>Boleta SaaS</strong></p>
            </div>
        </div>
        </body></html>
        """
        return _dispatch_email(
            to_email=to_email,
            subject=f"Bienvenido a Boleta SaaS - {company_name}",
            html_body=body,
            from_email=system_from_email,
            from_name=system_from_name,
        )

    if not all([system_smtp_host, system_smtp_user, system_smtp_password, system_from_email, to_email]):
        return {"success": False, "error": "Configuración SMTP del sistema incompleta"}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((system_from_name, system_from_email))
        msg["To"] = to_email
        msg["Reply-To"] = system_from_email
        msg["Subject"] = f"Bienvenido a Boleta SaaS - {company_name}"

        _build_headers(msg, system_from_email, system_from_name, to_email)

        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Boleta SaaS</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">Sistema de Boletas de Pago</p>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
                <p>Estimado(a) <strong>{admin_name}</strong>,</p>
                <p>Su empresa <strong>{company_name}</strong> (RUC: {company_ruc}) ha sido registrada exitosamente en <strong>Boleta SaaS</strong>.</p>

                <div style="background: #f0fdf4; border: 1px solid #22c55e; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #166534; margin: 0 0 10px;">Plan de Prueba Gratuito</h3>
                    <table style="width: 100%;">
                        <tr><td style="padding: 4px 0;"><strong>Envios mensuales:</strong></td><td style="text-align: right;">{plan_envios} envios/mes</td></tr>
                        <tr><td style="padding: 4px 0;"><strong>Inicio:</strong></td><td style="text-align: right;">{licencia_inicio}</td></tr>
                        <tr><td style="padding: 4px 0;"><strong>Vence:</strong></td><td style="text-align: right;">{licencia_fin}</td></tr>
                        <tr><td style="padding: 4px 0;"><strong>Vigencia:</strong></td><td style="text-align: right;">{dias_vigencia} dias</td></tr>
                    </table>
                </div>

                <p>Puede ingresar al sistema con su correo electronico:</p>
                <p style="text-align: center; font-size: 16px; color: #3b82f6;"><strong>{to_email}</strong></p>

                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                    Si usted no realizo este registro, ignore este mensaje.
                </p>
                <p style="color: #6b7280; font-size: 12px;">Saludos cordiales,<br><strong>Boleta SaaS</strong></p>
            </div>
        </div>
        </body></html>
        """

        _attach_html_alternative(msg, body)

        server = _connect_smtp(system_smtp_host, system_smtp_port, system_smtp_user, system_smtp_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_new_company_notification(
    system_smtp_host: str,
    system_smtp_port: int,
    system_smtp_user: str,
    system_smtp_password: str,
    system_from_email: str,
    system_from_name: str,
    to_email: str,
    company_name: str,
    company_ruc: str,
    admin_email: str,
    admin_name: str,
    plan_envios: int = 0,
    licencia_inicio: str = "",
    licencia_fin: str = "",
) -> dict:
    if _get_resend_api_key() or _has_gmail_token() or _get_sendgrid_api_key() or _get_mailtrap_api_token():
        fecha = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 25px; border-radius: 10px 10px 0 0; text-align: center;">
                <h2 style="color: white; margin: 0;">Nueva Empresa Registrada</h2>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
                <p>Se ha registrado una nueva empresa en el sistema:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Empresa</strong></td><td style="padding: 8px;">{company_name}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>RUC</strong></td><td style="padding: 8px;">{company_ruc}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Admin</strong></td><td style="padding: 8px;">{admin_name} ({admin_email})</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Plan</strong></td><td style="padding: 8px;">{plan_envios} envios/mes</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Inicio licencia</strong></td><td style="padding: 8px;">{licencia_inicio}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Fin licencia</strong></td><td style="padding: 8px;">{licencia_fin}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Fecha registro</strong></td><td style="padding: 8px;">{fecha}</td></tr>
                </table>
            </div>
        </div>
        </body></html>
        """
        return _dispatch_email(
            to_email=to_email,
            subject=f"Nueva empresa registrada - {company_name}",
            html_body=body,
            from_email=system_from_email,
            from_name=system_from_name,
        )

    if not all([system_smtp_host, system_smtp_user, system_smtp_password, system_from_email, to_email]):
        return {"success": False, "error": "Configuración SMTP del sistema incompleta"}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((system_from_name, system_from_email))
        msg["To"] = to_email
        msg["Reply-To"] = system_from_email
        msg["Subject"] = f"Nueva empresa registrada - {company_name}"

        _build_headers(msg, system_from_email, system_from_name, to_email)

        fecha = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 25px; border-radius: 10px 10px 0 0; text-align: center;">
                <h2 style="color: white; margin: 0;">Nueva Empresa Registrada</h2>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
                <p>Se ha registrado una nueva empresa en el sistema:</p>

                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Empresa</strong></td>
                        <td style="padding: 8px;">{company_name}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>RUC</strong></td>
                        <td style="padding: 8px;">{company_ruc}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Admin</strong></td>
                        <td style="padding: 8px;">{admin_name}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Email admin</strong></td>
                        <td style="padding: 8px;">{admin_email}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Plan</strong></td>
                        <td style="padding: 8px;">{plan_envios} envios/mes</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Inicio licencia</strong></td>
                        <td style="padding: 8px;">{licencia_inicio}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Fin licencia</strong></td>
                        <td style="padding: 8px;">{licencia_fin}</td></tr>
                    <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Fecha registro</strong></td>
                        <td style="padding: 8px;">{fecha}</td></tr>
                </table>
            </div>
        </div>
        </body></html>
        """

        _attach_html_alternative(msg, body)

        server = _connect_smtp(system_smtp_host, system_smtp_port, system_smtp_user, system_smtp_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_license_expiry_warning(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
    from_name: str,
    to_email: str,
    empresa: str,
    ruc: str,
    plan: int,
    fin: str,
    dias: int,
    admin_name: str,
) -> dict:
    if _get_resend_api_key() or _has_gmail_token() or _get_sendgrid_api_key() or _get_mailtrap_api_token():
        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #856404; margin: 0;">Licencia proxima a vencer</h3>
            </div>
            <p>Estimado(a) <strong>{admin_name}</strong>,</p>
            <p>Su licencia de uso del Sistema de Boletas de Pago esta proxima a vencer.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Empresa</strong></td><td style="padding: 8px;">{empresa}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>RUC</strong></td><td style="padding: 8px;">{ruc}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Plan</strong></td><td style="padding: 8px;">{plan} envios/mes</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Vigente hasta</strong></td><td style="padding: 8px;">{fin}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Dias restantes</strong></td><td style="padding: 8px; color: red;"><strong>{dias} dias</strong></td></tr>
            </table>
            <p>Para renovar su licencia, contacte a su ejecutivo comercial.</p>
            <br><p>Saludos cordiales,<br><strong>Sistema de Boletas de Pago</strong></p>
        </div>
        </body></html>
        """
        return _dispatch_email(
            to_email=to_email,
            subject=f"Su licencia del Sistema de Boletas vence en {dias} dias",
            html_body=body,
            from_email=from_email,
            from_name=from_name,
        )

    if not all([smtp_host, smtp_user, smtp_password, from_email, to_email]):
        return {"success": False, "error": "Configuración SMTP incompleta"}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((from_name or "Sistema de Boletas", from_email))
        msg["To"] = to_email
        msg["Reply-To"] = from_email
        msg["Subject"] = f"Su licencia del Sistema de Boletas vence en {dias} dias"

        _build_headers(msg, from_email, from_name, to_email)

        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #856404; margin: 0;">Licencia proxima a vencer</h3>
            </div>
            <p>Estimado(a) <strong>{admin_name}</strong>,</p>
            <p>Su licencia de uso del Sistema de Boletas de Pago esta proxima a vencer.</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Empresa</strong></td>
                    <td style="padding: 8px;">{empresa}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>RUC</strong></td>
                    <td style="padding: 8px;">{ruc}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Plan</strong></td>
                    <td style="padding: 8px;">{plan} envios/mes</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Vigente hasta</strong></td>
                    <td style="padding: 8px;">{fin}</td></tr>
                <tr><td style="padding: 8px; background: #f8f9fa;"><strong>Dias restantes</strong></td>
                    <td style="padding: 8px; color: red;"><strong>{dias} dias</strong></td></tr>
            </table>

            <p>Para renovar su licencia, contacte a su ejecutivo comercial.</p>
            <br>
            <p>Saludos cordiales,<br><strong>Sistema de Boletas de Pago</strong></p>
        </div>
        </body></html>
        """

        _attach_html_alternative(msg, body)

        server = _connect_smtp(smtp_host, smtp_port, smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}
