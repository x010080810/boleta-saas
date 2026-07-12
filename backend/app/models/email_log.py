import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    pay_slip_id: Mapped[str] = mapped_column(String(36), ForeignKey("pay_slips.id"), nullable=False)
    payroll_upload_id: Mapped[str] = mapped_column(String(36), ForeignKey("payroll_uploads.id"), nullable=True)
    batch_key: Mapped[str] = mapped_column(String(50), default="original")
    destinatario_email: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    enviado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="email_logs")
    pay_slip = relationship("PaySlip", back_populates="email_logs")
