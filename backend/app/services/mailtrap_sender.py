import os
import base64
import httpx
from app.core.config import settings


MAILTRAP_API_URL = "https://send.api.mailtrap.io/api/send"


def _get_api_token() -> str:
    return os.environ.get("MAILTRAP_API_TOKEN") or getattr(settings, "MAILTRAP_API_TOKEN", "") or ""


def send_via_mailtrap(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str = "",
    from_name: str = "",
    pdf_bytes: bytes = b"",
    pdf_filename: str = "",
) -> dict:
    api_token = _get_api_token()
    if not api_token:
        return {"success": False, "error": "MAILTRAP_API_TOKEN no configurado"}

    from_email = from_email or os.environ.get("RESEND_FROM_EMAIL") or settings.RESEND_FROM_EMAIL or "jn835513@gmail.com"

    payload = {
        "from": {"email": from_email, "name": from_name or "Boleta SaaS"},
        "to": [{"email": to_email}],
        "subject": subject,
        "html": html_body,
    }

    if pdf_bytes:
        payload["attachments"] = [
            {
                "filename": pdf_filename or "boleta.pdf",
                "content": base64.b64encode(pdf_bytes).decode(),
                "type": "application/pdf",
                "disposition": "attachment",
            }
        ]

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                MAILTRAP_API_URL,
                headers={
                    "Api-Token": api_token,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code in (200, 201):
            return {"success": True, "error": None}
        else:
            return {"success": False, "error": f"Mailtrap error {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
