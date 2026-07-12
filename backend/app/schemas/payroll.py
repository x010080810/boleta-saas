from pydantic import BaseModel
from typing import Optional


class PayrollUploadResponse(BaseModel):
    id: str
    ticket_number: str
    tipo_planilla: str
    periodo_mes: int
    periodo_ano: int
    filename: str
    total_registros: int
    total_procesados: int
    total_observaciones: int
    total_enviados: int
    total_fallidos: int
    total_sin_saldo: int
    estado: str
    created_at: str


class PayrollPreview(BaseModel):
    ticket: str
    upload_id: str
    registros_detectados: int
    empleados: list


class ResendRequest(BaseModel):
    pay_slip_ids: Optional[list[str]] = None
    tipo: str = "selected"
