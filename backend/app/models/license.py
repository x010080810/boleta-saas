import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class LicenseHistory(Base):
    __tablename__ = "license_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    inicio_anterior: Mapped[date] = mapped_column(Date, nullable=True)
    fin_anterior: Mapped[date] = mapped_column(Date, nullable=True)
    plan_anterior: Mapped[int] = mapped_column(Integer, nullable=True)
    inicio_nuevo: Mapped[date] = mapped_column(Date, nullable=True)
    fin_nuevo: Mapped[date] = mapped_column(Date, nullable=True)
    plan_nuevo: Mapped[int] = mapped_column(Integer, nullable=True)
    notas: Mapped[str] = mapped_column(Text, nullable=True)
    creado_por: Mapped[str] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="license_history")
