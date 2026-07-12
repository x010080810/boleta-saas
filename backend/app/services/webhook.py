import httpx
import json
from datetime import datetime, timezone
from app.core.database import sync_session_factory
from app.models.webhook import WebhookEvent
from app.core.config import settings


def send_webhook(company_id: str, event_type: str, payload: dict, webhook_url: str) -> dict:
    event_id = None
    try:
        db = sync_session_factory()
        event = WebhookEvent(
            company_id=company_id,
            event_type=event_type,
            webhook_url=webhook_url,
            payload=payload,
        )
        db.add(event)
        db.flush()
        event_id = event.id
        db.commit()
    except Exception:
        if db:
            db.close()
        return {"success": False, "error": "Failed to create webhook event"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "BoletaSaaS-Webhook/1.0"},
            )
        try:
            db = sync_session_factory()
            event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
            if event:
                event.response_status = resp.status_code
                event.response_body = resp.text[:2000]
                event.success = 200 <= resp.status_code < 300
                event.executed_at = datetime.now(timezone.utc)
                db.commit()
            db.close()
        except Exception:
            if db:
                db.close()

        if 200 <= resp.status_code < 300:
            return {"success": True, "status_code": resp.status_code}
        return {"success": False, "error": f"HTTP {resp.status_code}", "status_code": resp.status_code}

    except Exception as e:
        try:
            db = sync_session_factory()
            event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
            if event:
                event.success = False
                event.error_message = str(e)
                event.executed_at = datetime.now(timezone.utc)
                db.commit()
            db.close()
        except Exception:
            if db:
                db.close()
        return {"success": False, "error": str(e)}
