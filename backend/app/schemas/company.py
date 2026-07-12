from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date
from app.core.password_policy import validate_password


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    ruc: Optional[str] = None
    logo_url: Optional[str] = None
    plan_envios_mes: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    pdf_password_field: Optional[str] = None
    lang: Optional[str] = None
    webhook_url: Optional[str] = None


class LicenseUpdate(BaseModel):
    plan_envios_mes: int
    licencia_inicio: date
    licencia_fin: date
    dias_gracia: int = 60


class EmployeeCreate(BaseModel):
    tipo_documento: str
    numero_documento: str
    nombre_completo: str
    email: Optional[str] = None
    cargo: Optional[str] = None
    fecha_ingreso: Optional[date] = None


class EmployeeBatchCreate(BaseModel):
    employees: list[EmployeeCreate]


class SmtpTestRequest(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str
    from_name: str = ""
    test_email: str


class AdminCreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company_id: str
    role: str = "admin"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        valid, msg = validate_password(v)
        if not valid:
            raise ValueError(msg)
        return v


class AdminAssignUserRequest(BaseModel):
    user_id: str
    role: str = "admin"


class AdminUpdateAssignmentRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
