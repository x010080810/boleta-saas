from fastapi import APIRouter, Request
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    db_ready = getattr(request.app.state, "db_ready", False)
    return {
        "status": "ok" if db_ready else "degraded",
        "database": "connected" if db_ready else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
