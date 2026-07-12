import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, Boolean, DateTime, Date, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ruc: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, index=True)
    logo_url: Mapped[str] = mapped_column(Text, nullable=True)

    plan_envios_mes: Mapped[int] = mapped_column(Integer, default=100)
    licencia_inicio: Mapped[date] = mapped_column(Date, nullable=True)
    licencia_fin: Mapped[date] = mapped_column(Date, nullable=True)
    licencia_grace_hasta: Mapped[date] = mapped_column(Date, nullable=True)
    licencia_estado: Mapped[str] = mapped_column(String(20), default="activa")
    licencia_renovacion_automatica: Mapped[bool] = mapped_column(Boolean, default=False)
    notificado_15_dias: Mapped[bool] = mapped_column(Boolean, default=False)

    smtp_host: Mapped[str] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str] = mapped_column(Text, nullable=True)
    smtp_from_email: Mapped[str] = mapped_column(String(255), nullable=True)
    smtp_from_name: Mapped[str] = mapped_column(String(200), nullable=True)

    email_subject_template: Mapped[str] = mapped_column(Text, nullable=True)
    email_body_template: Mapped[str] = mapped_column(Text, nullable=True)
    pdf_password_field: Mapped[str] = mapped_column(String(50), default="numero_documento")

    lang: Mapped[str] = mapped_column(String(5), default="es")
    webhook_url: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    users = relationship("UserCompany", back_populates="company")
    employees = relationship("EmployeeCompany", back_populates="company")
    payroll_uploads = relationship("PayrollUpload", back_populates="company")
    pay_slips = relationship("PaySlip", back_populates="company")
    email_logs = relationship("EmailLog", back_populates="company")
    quotas = relationship("MonthlySendQuota", back_populates="company")
    license_history = relationship("LicenseHistory", back_populates="company")


class CompanyUser(Base):
    __tablename__ = "company_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    companies = relationship("UserCompany", back_populates="user")


class UserCompany(Base):
    __tablename__ = "user_company_assignments"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("company_users.id"), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("CompanyUser", back_populates="companies")
    company = relationship("Company", back_populates="users")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo_documento: Mapped[str] = mapped_column(String(2), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    UniqueConstraint("tipo_documento", "numero_documento", name="uq_employee_document")

    companies = relationship("EmployeeCompany", back_populates="employee")
    pay_slips = relationship("PaySlip", back_populates="employee")


class EmployeeCompany(Base):
    __tablename__ = "employee_company_assignments"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), primary_key=True)
    cargo: Mapped[str] = mapped_column(String(200), nullable=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    employee = relationship("Employee", back_populates="companies")
    company = relationship("Company", back_populates="employees")
