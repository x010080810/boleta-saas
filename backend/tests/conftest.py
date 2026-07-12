import pytest
import httpx
import time
import tempfile
import openpyxl
import os
from datetime import datetime


@pytest.fixture(scope="session")
def test_excel_file():
    """Create a test payroll Excel file matching the expected format."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "EMPLEADOS"

    headers = [
        "tipo_documento", "numero_documento", "apellidos_nombres", "email", "cargo",
        "fecha_ingreso", "dias_laborados", "asignacion_familiar",
        "ING_haber_basico", "ING_asignacion_familiar_monto", "ING_vacaciones",
        "ING_horas_extras", "ING_bono_productividad", "ING_gratificacion",
        "ING_cts", "ING_feriado", "ING_bono_trimestral", "ING_otros",
        "DESC_afp_obligatorio", "DESC_comision_afp", "DESC_prima_seguro",
        "DESC_onp", "DESC_renta_5ta", "DESC_otros",
        "APOR_essalud", "APOR_credito_eps", "APOR_vida_ley", "APOR_otros",
        "total_ingresos", "total_descuentos", "neto_pagar", "neto_pagar_usd",
    ]
    ws.append(headers)

    rows = [
        ["01", "002976650", "LARSSON IDA GABRIELLA MAGDALEN", "gabriella@email.com",
         "HEAD OF OPERATIONS", "2020-04-01", 30, "NO",
         23775.29, "", "", "", "", "", "", "", "", "",
         5419.21, "", "", "", "", "",
         "", "", "", "",
         23775.29, 5419.21, 18356.08, ""],
        ["01", "73666629", "QUISPE MAMANI JUAN CARLOS", "juan@email.com",
         "ANALISTA CONTABLE", "2021-03-15", 30, "NO",
         3500, "", "", "", "", "", "", "", "", "",
         520, "", "", "", "", "",
         "", "", "", "",
         3500, 520, 2980, ""],
        ["01", "12345678", "PEREZ GOMEZ MARIA ELENA", "maria@email.com",
         "GERENTE ADMINISTRATIVO", "2019-06-01", 30, "SI",
         8500, 102.5, "", "", "", "", "", "", "", "",
         1250, "", "", "", "", "",
         "", "", "", "",
         8602.5, 1250, 7352.5, ""],
        ["01", "87654321", "TORRES LOPEZ PEDRO ANTONIO", "pedro@email.com",
         "ASISTENTE RRHH", "2022-01-10", 30, "NO",
         2500, "", "", "", "", "", "", "", "", "",
         380, "", "", "", "", "",
         "", "", "", "",
         2500, 380, 2120, ""],
        ["01", "45678912", "CASTRO DIAZ ANA MARIA", "ana@email.com",
         "CONTADOR GENERAL", "2020-08-20", 30, "SI",
         6000, 102.5, "", "", "", "", "", "", "", "",
         900, "", "", "", "", "",
         "", "", "", "",
         6102.5, 900, 5202.5, ""],
    ]
    for row in rows:
        ws.append(row)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    yield tmp.name
    os.unlink(tmp.name)

API_BASE = "http://localhost:8000/api"

SUPER_EMAIL = "admin@sistema.com"
SUPER_PASS = "123456"

COMPANY_EMAIL = "admin@lavaleta.com"
COMPANY_PASS = "123456"


@pytest.fixture(scope="session")
def base_url():
    return API_BASE


@pytest.fixture(scope="session")
def super_token(base_url):
    r = httpx.post(
        f"{base_url}/auth/super-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASS},
    )
    assert r.status_code == 200, f"Super login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def company_token(base_url):
    r = httpx.post(
        f"{base_url}/auth/login",
        json={"email": COMPANY_EMAIL, "password": COMPANY_PASS},
    )
    assert r.status_code == 200, f"Company login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def test_company(base_url, super_token):
    timestamp = int(time.time())
    ruc = f"999{timestamp % 10**8:08d}"
    payload = {
        "company_name": f"Test Empresa {timestamp}",
        "company_ruc": ruc,
        "admin_email": f"admin_{timestamp}@test.com",
        "admin_password": "test123",
        "admin_full_name": f"Admin Test {timestamp}",
    }
    r = httpx.post(
        f"{base_url}/auth/register",
        json=payload,
    )
    assert r.status_code == 200, f"Register failed: {r.text}"
    data = r.json()
    company_id = data["companies"][0]["id"]
    yield {
        "company_id": company_id,
        "ruc": ruc,
        "token": data["access_token"],
        "email": payload["admin_email"],
        "password": payload["admin_password"],
        "name": payload["company_name"],
    }

    pass  # cleanup: empresa queda en BD para inspeccion manual


@pytest.fixture
def smtp_config():
    return {
        "smtp_host": "sandbox.smtp.mailtrap.io",
        "smtp_port": 587,
        "smtp_user": "5e9230575914d0",
        "smtp_password": "39f567281e3688",
        "smtp_from_email": "test@lavaleta.com",
        "smtp_from_name": "Test Empresa",
        "plan_envios_mes": 100,
        "lang": "es",
        "webhook_url": None,
    }


@pytest.fixture
def webhook_test_url():
    return "https://webhook.site/test-placeholder"


@pytest.fixture
def smtp_config_gmail():
    return {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "tu-correo@gmail.com",
        "smtp_password": "tu-contrasena-aplicacion",
        "smtp_from_email": "tu-correo@gmail.com",
        "smtp_from_name": "Mi Empresa",
        "plan_envios_mes": 100,
    }


@pytest.fixture
def test_employees(base_url, test_company):
    token = test_company["token"]
    company_id = test_company["company_id"]
    employees = [
        {"tipo_documento": "01", "numero_documento": "002976650",
         "nombre_completo": "LARSSON IDA GABRIELLA MAGDALEN",
         "email": "gabriella@email.com", "cargo": "HEAD OF OPERATIONS"},
        {"tipo_documento": "01", "numero_documento": "73666629",
         "nombre_completo": "QUISPE MAMANI JUAN CARLOS",
         "email": "juan@email.com", "cargo": "ANALISTA CONTABLE"},
        {"tipo_documento": "01", "numero_documento": "12345678",
         "nombre_completo": "PEREZ GOMEZ MARIA ELENA",
         "email": "maria@email.com", "cargo": "GERENTE ADMINISTRATIVO"},
        {"tipo_documento": "01", "numero_documento": "87654321",
         "nombre_completo": "TORRES LOPEZ PEDRO ANTONIO",
         "email": "pedro@email.com", "cargo": "ASISTENTE RRHH"},
        {"tipo_documento": "01", "numero_documento": "45678912",
         "nombre_completo": "CASTRO DIAZ ANA MARIA",
         "email": "ana@email.com", "cargo": "CONTADOR GENERAL"},
    ]
    for emp in employees:
        r = httpx.post(
            f"{base_url}/companies/{company_id}/employees",
            json=emp,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, f"Create employee failed: {r.text}"
    return employees
