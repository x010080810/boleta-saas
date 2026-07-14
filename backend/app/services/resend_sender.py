import os
import base64
import resend
from app.core.config import settings


def _get_api_key() -> str:
    return os.environ.get("RESEND_API_KEY") or settings.RESEND_API_KEY or ""


def send_via_resend(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str = "",
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    api_key = _get_api_key()
    if not api_key:
        return {"success": False, "error": "RESEND_API_KEY no configurado"}

    resend.api_key = api_key

    sender_email = os.environ.get("RESEND_FROM_EMAIL") or "onboarding@resend.dev"

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "reply_to": from_email or sender_email,
    }

    if pdf_bytes:
        content = base64.b64encode(pdf_bytes).decode()
        params["attachments"] = [
            {
                "filename": pdf_filename or "boleta.pdf",
                "content": content,
            }
        ]

    try:
        response = resend.Emails.send(params)
        return {"success": True, "error": None, "id": response.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}
