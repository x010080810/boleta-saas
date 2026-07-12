from pydantic import BaseModel, field_validator
from typing import Optional
from app.core.password_policy import validate_password


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    companies: list = []


class RegisterCompanyRequest(BaseModel):
    company_name: str
    company_ruc: str
    admin_email: str
    admin_password: str
    admin_full_name: str

    @field_validator("admin_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        valid, msg = validate_password(v)
        if not valid:
            raise ValueError(msg)
        return v


class SuperAdminLoginRequest(BaseModel):
    email: str
    password: str
