from pydantic import BaseModel, EmailStr
from typing import Optional


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


class SuperAdminLoginRequest(BaseModel):
    email: str
    password: str
