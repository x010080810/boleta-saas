import os
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
    pdf_path: str = "",
) -> dict:
    api_key = _get_api_key()
    if not api_key:
        return {"success": False, "error": "RESEND_API_KEY no configurado"}

    resend.api_key = api_key

    from_email = from_email or os.environ.get("RESEND_FROM_EMAIL") or "onboarding@resend.dev"

    params = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            import base64
            content = base64.b64encode(f.read()).decode()
        params["attachments"] = [
            {
                "filename": os.path.basename(pdf_path).replace(" ", "_"),
                "content": content,
            }
        ]

    try:
        response = resend.Emails.send(params)
        return {"success": True, "error": None, "id": response.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}
