import os
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import formataddr, formatdate
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def _load_credentials() -> Credentials | None:
    token_json = os.environ.get("GMAIL_TOKEN_JSON") or ""
    if not token_json:
        return None
    try:
        return Credentials.from_authorized_user_info(json.loads(token_json))
    except Exception:
        return None


def _refresh_if_needed(creds: Credentials) -> Credentials | None:
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            return creds
        except Exception:
            return None
    return creds


def send_via_gmail_api(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str,
    from_name: str = "",
    pdf_path: str = "",
) -> dict:
    creds = _load_credentials()
    if not creds:
        return {"success": False, "error": "GMAIL_TOKEN_JSON no configurado"}

    creds = _refresh_if_needed(creds)
    if not creds:
        return {"success": False, "error": "Token de Gmail expirado y no se pudo refrescar"}

    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = formataddr((from_name or from_email, from_email))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(timeval=None, localtime=True, usegmt=True)

        body_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(body_part)

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                part = MIMEBase("application", "pdf")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = os.path.basename(pdf_path).replace(" ", "_")
                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        service = build("gmail", "v1", credentials=creds)
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

        return {"success": True, "error": None}
    except HttpError as e:
        return {"success": False, "error": f"Gmail API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
