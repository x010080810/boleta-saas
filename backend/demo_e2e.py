"""
Demo E2E - Interactive demo del flujo completo de boletas de pago.
Uso: python demo_e2e.py

Requisitos: backend corriendo en http://localhost:8000
"""

import httpx
import json
import time
import sys
import os
import openpyxl
import tempfile
from datetime import datetime

API = "http://localhost:8000/api"

COLOR = {
    "ok": "\033[92m", "info": "\033[94m",
    "warn": "\033[93m", "err": "\033[91m",
    "bold": "\033[1m", "end": "\033[0m",
}


def p(title, status="info", detail=""):
    icon = {"ok": "\u2713", "info": "\u2192", "warn": "\u26a0", "err": "\u2717"}.get(status, " ")
    c = COLOR.get(status, COLOR["info"])
    msg = f"{c}{icon} {title}{COLOR['end']}"
    if detail:
        msg += f"\n  {detail}"
    print(msg)


def json_dump(data):
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def pay_url(company_id, path=""):
    return f"{API}/companies/{company_id}/payroll{path}"


def make_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "EMPLEADOS"
    headers = [
        "tipo_documento", "numero_documento", "apellidos_nombres", "email",
        "cargo", "fecha_ingreso", "dias_laborados", "asignacion_familiar",
        "ING_haber_basico", "ING_asignacion_familiar_monto", "ING_vacaciones",
        "ING_horas_extras", "ING_bono_productividad", "ING_gratificacion",
        "ING_cts", "ING_feriado", "ING_bono_trimestral", "ING_otros",
        "DESC_afp_obligatorio", "DESC_comision_afp", "DESC_prima_seguro",
        "DESC_onp", "DESC_renta_5ta", "DESC_otros",
        "APOR_essalud", "APOR_credito_eps", "APOR_vida_ley", "APOR_otros",
        "total_ingresos", "total_descuentos", "neto_pagar", "neto_pagar_usd",
    ]
    ws.append(headers)
    ws.append(["01", "002976650", "LARSSON IDA GABRIELLA MAGDALEN",
               "gabriella@email.com", "HEAD OF OPERATIONS", "2020-04-01", 30, "NO",
               23775.29, "", "", "", "", "", "", "", "", "",
               5419.21, "", "", "", "", "", "", "", "", "",
               23775.29, 5419.21, 18356.08, ""])
    ws.append(["01", "73666629", "QUISPE MAMANI JUAN CARLOS",
               "juan@email.com", "ANALISTA CONTABLE", "2021-03-15", 30, "NO",
               3500, "", "", "", "", "", "", "", "", "",
               520, "", "", "", "", "", "", "", "", "",
               3500, 520, 2980, ""])
    ws.append(["01", "12345678", "PEREZ GOMEZ MARIA ELENA",
               "maria@email.com", "GERENTE ADMINISTRATIVO", "2019-06-01", 30, "SI",
               8500, 102.5, "", "", "", "", "", "", "", "",
               1250, "", "", "", "", "", "", "", "", "",
               8602.5, 1250, 7352.5, ""])
    ws.append(["01", "87654321", "TORRES LOPEZ PEDRO ANTONIO",
               "pedro@email.com", "ASISTENTE RRHH", "2022-01-10", 30, "NO",
               2500, "", "", "", "", "", "", "", "", "",
               380, "", "", "", "", "", "", "", "", "",
               2500, 380, 2120, ""])
    ws.append(["01", "45678912", "CASTRO DIAZ ANA MARIA",
               "ana@email.com", "CONTADOR GENERAL", "2020-08-20", 30, "SI",
               6000, 102.5, "", "", "", "", "", "", "", "",
               900, "", "", "", "", "", "", "", "", "",
               6102.5, 900, 5202.5, ""])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    return tmp.name


def main():
    print(f"{COLOR['bold']}{'='*60}{COLOR['end']}")
    print(f"{COLOR['bold']}  DEMO E2E - SISTEMA DE BOLETAS DE PAGO{COLOR['end']}")
    print(f"{COLOR['bold']}{'='*60}{COLOR['end']}")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API:    {API}")
    print()

    r = httpx.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    p("1. Sistema saludable", "ok", json_dump(r.json()))

    r = httpx.post(f"{API}/auth/super-login", json={
        "email": "admin@sistema.com", "password": "123456",
    }, timeout=10)
    assert r.status_code == 200
    super_token = r.json()["access_token"]
    p("2. Super Admin autenticado", "ok")

    timestamp = int(time.time())
    ruc = f"999{timestamp % 10**8:08d}"
    company_data = {
        "company_name": f"Demo S.A.C. {timestamp}",
        "company_ruc": ruc,
        "admin_email": f"demo_admin_{timestamp}@demo.com",
        "admin_password": "demo123456",
        "admin_full_name": f"Admin Demo {timestamp}",
    }
    r = httpx.post(f"{API}/auth/register", json=company_data, timeout=10)
    assert r.status_code == 200, f"Register failed: {r.text}"
    reg = r.json()
    company_id = reg["companies"][0]["id"]
    token = reg["access_token"]
    p("3. Empresa registrada", "ok", json_dump({
        "id": company_id, "ruc": ruc, "admin": company_data["admin_email"],
    }))

    r = httpx.put(f"{API}/admin/companies/{company_id}/license", json={
        "plan_envios_mes": 100,
        "licencia_inicio": "2026-01-01",
        "licencia_fin": "2027-12-31",
        "dias_gracia": 60,
    }, headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
    assert r.status_code == 200
    p("4. Plan y licencia activados", "ok")

    r = httpx.put(f"{API}/companies/{company_id}", json={
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "tu-correo@gmail.com",
        "smtp_password": "xxxx xxxx xxxx xxxx",
        "smtp_from_email": "tu-correo@gmail.com",
        "smtp_from_name": "Demo S.A.C.",
        "lang": "es",
    }, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert r.status_code == 200
    p("5. SMTP configurado (Gmail - reemplazar credenciales)", "ok")

    empleados = [
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
    for emp in empleados:
        r = httpx.post(f"{API}/companies/{company_id}/employees", json=emp,
                       headers={"Authorization": f"Bearer {token}"}, timeout=10)
        assert r.status_code == 200, f"Create employee failed: {r.text}"
    p("6. 5 empleados registrados en maestro", "ok")

    excel_path = make_excel()
    p("7. Planilla Excel generada en memoria", "ok")

    with open(excel_path, "rb") as f:
        r = httpx.post(
            pay_url(company_id, "/upload"),
            files={"file": ("planilla.xlsx", f,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"tipo_planilla": "SUELDOS", "periodo_mes": "7", "periodo_ano": "2026"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
    os.unlink(excel_path)
    assert r.status_code == 200, f"Upload failed: {r.text}"
    upload = r.json()
    ticket = upload["ticket"]
    upload_id = upload["upload_id"]
    p("8. Planilla subida", "ok", json_dump({
        "ticket": ticket, "registros": upload["registros_detectados"],
        "ing": upload["columnas_ing"], "desc": upload["columnas_desc"],
        "apor": upload["columnas_apor"],
    }))

    r = httpx.get(
        pay_url(company_id, f"/uploads/{upload_id}/preview"),
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
    assert r.status_code == 200
    preview = r.json()
    p("9. Vista previa", "ok", json_dump([
        {"nombre": e["nombre_completo"], "neto": e["neto_pagar"],
         "registrado": e["registrado_en_maestro"]}
        for e in preview["empleados"]
    ]))

    r = httpx.post(
        pay_url(company_id, f"/uploads/{upload_id}/process"),
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
    assert r.status_code == 200
    p("10. Procesamiento iniciado en background", "ok")

    for i in range(30):
        r = httpx.get(
            pay_url(company_id, f"/uploads/{upload_id}/status"),
            headers={"Authorization": f"Bearer {token}"}, timeout=10,
        )
        data = r.json()
        sys.stdout.write(f"\r    Estado: {data['estado'].upper()} ({i+1}/30s)")
        sys.stdout.flush()
        if data["estado"] == "completed":
            print()
            p("11. Procesamiento completado", "ok", json_dump({
                "registros": data["total_registros"],
                "procesados": data["total_procesados"],
                "enviados": data["total_enviados"],
                "fallidos": data["total_fallidos"],
                "sin_saldo": data["total_sin_saldo"],
                "observaciones": data["total_observaciones"],
            }))
            break
        if data["estado"] == "failed":
            print()
            p("Procesamiento fallido", "err")
            return
        time.sleep(2)
    else:
        p("Timeout esperando procesamiento", "err")
        return

    r = httpx.get(
        pay_url(company_id, f"/uploads/{upload_id}/boletas"),
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
    assert r.status_code == 200
    boletas = r.json()
    p(f"12. {len(boletas)} boletas generadas", "ok", json_dump([
        {"nombre": b["nombre_completo"], "email": b["email_destino"],
         "neto": b["neto_pagar"], "estado": b["estado_envio"],
         "observacion": b["es_observacion"], "motivo": b["motivo_observacion"]}
        for b in boletas
    ]))

    boleta_pdf = next((b for b in boletas if not b.get("es_observacion")), boletas[0])
    r = httpx.get(
        pay_url(company_id, f"/boletas/{boleta_pdf['id']}/download"),
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    filename = f"demo_boleta_{boleta_pdf['numero_documento']}.pdf"
    with open(filename, "wb") as f:
        f.write(r.content)
    p(f"13. PDF descargado: {filename} ({len(r.content)/1024:.1f} KB)", "ok")

    r = httpx.get(
        pay_url(company_id, f"/uploads/{upload_id}/report"),
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
    assert r.status_code == 200
    report = r.json()
    p("14. Reporte detallado", "ok", json_dump({
        "resumen": report["resumen"],
        "observaciones": report.get("observaciones", []),
    }))

    r = httpx.get(
        pay_url(company_id, "/quota-status"),
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
    assert r.status_code == 200
    p("15. Cuota mensual", "ok", json_dump(r.json()))

    for i in range(12):
        r = httpx.post(f"{API}/auth/login",
                       json={"email": "test@rate.com", "password": "test"}, timeout=10)
        if r.status_code == 429:
            p("16. Rate limit funcional (429 tras 10 intentos/min)", "ok")
            break
    else:
        p("16. Rate limit no activado (esperar 1 min entre demos)", "warn")

    print()
    print(f"{COLOR['bold']}{'='*60}{COLOR['end']}")
    print(f"{COLOR['bold']}  DEMO COMPLETADA EXITOSAMENTE{COLOR['end']}")
    print(f"{COLOR['bold']}{'='*60}{COLOR['end']}")
    print()
    print(f"  Empresa:         {company_data['company_name']}")
    print(f"  RUC:             {ruc}")
    print(f"  Ticket:          {ticket}")
    print(f"  Upload ID:       {upload_id}")
    print(f"  PDF:             {filename}")
    print()
    print(f"  Acceso empresa:  {company_data['admin_email']} / {company_data['admin_password']}")
    print(f"  Acceso super:    admin@sistema.com / 123456")


if __name__ == "__main__":
    main()
    with open("demo_vars.json", "w") as f:
        json.dump({"company_email": "admin@sistema.com", "company_password": "123456", "api_base": API}, f)
