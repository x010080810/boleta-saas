import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PayrollUpload(Base):
    __tablename__ = "payroll_uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    tipo_planilla: Mapped[str] = mapped_column(String(30), nullable=False)
    periodo_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo_ano: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=True)

    total_registros: Mapped[int] = mapped_column(Integer, default=0)
    total_procesados: Mapped[int] = mapped_column(Integer, default=0)
    total_observaciones: Mapped[int] = mapped_column(Integer, default=0)
    total_enviados: Mapped[int] = mapped_column(Integer, default=0)
    total_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    total_sin_saldo: Mapped[int] = mapped_column(Integer, default=0)

    estado: Mapped[str] = mapped_column(String(20), default="pending")
    resumen_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    observaciones_json: Mapped[list] = mapped_column(JSON, nullable=True)
    detalle_envios_json: Mapped[list] = mapped_column(JSON, nullable=True)

    ticket_enviado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    procesado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="payroll_uploads")
    pay_slips = relationship("PaySlip", back_populates="payroll_upload")
    unregistered_workers = relationship("UnregisteredWorker", back_populates="payroll_upload")


class PaySlip(Base):
    __tablename__ = "pay_slips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    payroll_upload_id: Mapped[str] = mapped_column(String(36), ForeignKey("payroll_uploads.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=True)

    tipo_documento: Mapped[str] = mapped_column(String(2), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    email_destino: Mapped[str] = mapped_column(String(255), nullable=True)
    cargo: Mapped[str] = mapped_column(String(200), nullable=True)

    pdf_path: Mapped[str] = mapped_column(Text, nullable=True)
    pdf_password: Mapped[str] = mapped_column(Text, nullable=True)

    datos_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    ingresos_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    descuentos_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    aportaciones_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    total_ingresos: Mapped[float] = mapped_column(Float, default=0)
    total_descuentos: Mapped[float] = mapped_column(Float, default=0)
    neto_pagar: Mapped[float] = mapped_column(Float, default=0)
    neto_pagar_usd: Mapped[float] = mapped_column(Float, nullable=True)
    total_aportaciones: Mapped[float] = mapped_column(Float, default=0)

    es_observacion: Mapped[bool] = mapped_column(default=False)
    motivo_observacion: Mapped[str] = mapped_column(Text, nullable=True)

    estado_envio: Mapped[str] = mapped_column(String(20), default="no_enviado")
    batch_key: Mapped[str] = mapped_column(String(50), default="original")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    enviado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="pay_slips")
    payroll_upload = relationship("PayrollUpload", back_populates="pay_slips")
    employee = relationship("Employee", back_populates="pay_slips")
    email_logs = relationship("EmailLog", back_populates="pay_slip")


class UnregisteredWorker(Base):
    __tablename__ = "unregistered_workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payroll_upload_id: Mapped[str] = mapped_column(String(36), ForeignKey("payroll_uploads.id"), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(2), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    email_destino: Mapped[str] = mapped_column(String(255), nullable=True)
    datos_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    pdf_generado: Mapped[bool] = mapped_column(default=True)
    boleta_enviada: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    payroll_upload = relationship("PayrollUpload", back_populates="unregistered_workers")
