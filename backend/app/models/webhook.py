import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    pay_slip_id: Mapped[str] = mapped_column(String(36), ForeignKey("pay_slips.id"), nullable=True)
    payroll_upload_id: Mapped[str] = mapped_column(String(36), ForeignKey("payroll_uploads.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    webhook_url: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    response_status: Mapped[int] = mapped_column(nullable=True)
    response_body: Mapped[str] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
