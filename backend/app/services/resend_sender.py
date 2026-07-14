import os
import base64
import httpx
from app.core.config import settings


RESEND_API_URL = "https://api.resend.com/emails"


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

    sender = from_email or os.environ.get("RESEND_FROM_EMAIL") or "onboarding@resend.dev"

    print(f"[RESEND] to={to_email!r} from={sender!r} reply_to={from_email!r}")

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    if from_email:
        payload["reply_to"] = from_email

    if pdf_bytes:
        content = base64.b64encode(pdf_bytes).decode()
        payload["attachments"] = [
            {
                "filename": pdf_filename or "boleta.pdf",
                "content": content,
            }
        ]

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "error": None, "id": data.get("id")}
        else:
            try:
                detail = resp.json().get("message") or resp.json().get("error") or resp.text
            except Exception:
                detail = resp.text
            print(f"[RESEND] FAILED: {detail}")
            return {"success": False, "error": f"Resend error {resp.status_code}: {detail}"}
    except Exception as e:
        print(f"[RESEND] EXCEPTION: {e}")
        return {"success": False, "error": str(e)}
