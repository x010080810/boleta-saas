import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition,
    From, To, Subject, HtmlContent,
)
from app.core.config import settings


def send_via_sendgrid(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    pdf_path: Optional[str] = None,
    pdf_filename: Optional[str] = None,
) -> dict:
    api_key = os.environ.get("SENDGRID_API_KEY") or getattr(settings, "SENDGRID_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "SENDGRID_API_KEY no configurado"}

    from_email = from_email or os.environ.get("SYSTEM_SMTP_FROM_EMAIL") or "noreply@boletasaas.com"
    from_name = from_name or "Boleta SaaS"

    message = Mail(
        from_email=From(from_email, from_name),
        to_emails=To(to_email),
        subject=Subject(subject),
        html_content=HtmlContent(html_body),
    )

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            import base64
            encoded = base64.b64encode(f.read()).decode()
        attachment = Attachment(
            file_content=FileContent(encoded),
            file_name=FileName(pdf_filename or os.path.basename(pdf_path)),
            file_type=FileType("application/pdf"),
            disposition=Disposition("attachment"),
        )
        message.add_attachment(attachment)

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return {"success": True, "error": None, "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}
