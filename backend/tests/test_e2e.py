"""
E2E Integration Tests
Run against a running backend: pytest tests/ -v --timeout=120
"""

import httpx
import io
import openpyxl
import pytest


def _url(base, company_id, path):
    return f"{base}/companies/{company_id}/payroll{path}"


class TestE2E:
    """Full end-to-end payroll processing flow."""

    def test_01_register_company(self, base_url, test_company):
        assert test_company["company_id"] is not None
        assert len(test_company["token"]) > 0

        r = httpx.get(
            f"{base_url}/companies/{test_company['company_id']}",
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == test_company["name"]
        assert data["ruc"] == test_company["ruc"]
        assert data["plan_envios_mes"] == 50

    def test_02_configure_smtp(self, base_url, test_company, smtp_config):
        r = httpx.put(
            f"{base_url}/companies/{test_company['company_id']}",
            json=smtp_config,
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200

        r = httpx.get(
            f"{base_url}/companies/{test_company['company_id']}",
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        data = r.json()
        assert data["smtp_host"] == smtp_config["smtp_host"]

    def test_03_register_employees(self, base_url, test_company, test_employees):
        r = httpx.get(
            f"{base_url}/companies/{test_company['company_id']}/employees",
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        employees = r.json()
        assert len(employees) == 5

    def test_04_download_template(self, base_url):
        r = httpx.get(f"{base_url}/templates/excel")
        assert r.status_code == 200
        assert r.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        assert "EMPLEADOS" in wb.sheetnames

    def test_05_upload_payroll(self, base_url, test_company, test_excel_file):
        cid = test_company["company_id"]
        with open(test_excel_file, "rb") as f:
            r = httpx.post(
                _url(base_url, cid, "/upload"),
                files={"file": ("test_planilla.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"tipo_planilla": "SUELDOS", "periodo_mes": "7", "periodo_ano": "2026"},
                headers={"Authorization": f"Bearer {test_company['token']}"},
            )
        assert r.status_code == 200, f"Upload failed: {r.text}"
        data = r.json()
        assert data["registros_detectados"] == 5
        assert data["ticket"].startswith("BLP-")
        test_company["upload_id"] = data["upload_id"]
        test_company["ticket"] = data["ticket"]

    def test_06_preview_upload(self, base_url, test_company):
        cid, uid = test_company["company_id"], test_company["upload_id"]
        r = httpx.get(
            _url(base_url, cid, f"/uploads/{uid}/preview"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_empleados"] == 5
        assert data["ticket"] == test_company["ticket"]

    def test_07_process_upload(self, base_url, test_company):
        cid, uid = test_company["company_id"], test_company["upload_id"]
        r = httpx.post(
            _url(base_url, cid, f"/uploads/{uid}/process"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200, f"Process failed: {r.text}"
        data = r.json()
        assert data["estado"] == "processing"

    def test_08_check_status_completed(self, base_url, test_company):
        import time
        cid, uid = test_company["company_id"], test_company["upload_id"]
        for _ in range(30):
            r = httpx.get(
                _url(base_url, cid, f"/uploads/{uid}/status"),
                headers={"Authorization": f"Bearer {test_company['token']}"},
            )
            assert r.status_code == 200
            data = r.json()
            if data["estado"] == "completed":
                assert data["total_procesados"] == 5
                assert data["total_enviados"] >= 1
                return
            time.sleep(2)
        pytest.fail("Upload did not complete within 60s")

    def test_09_list_boletas(self, base_url, test_company):
        cid, uid = test_company["company_id"], test_company["upload_id"]
        r = httpx.get(
            _url(base_url, cid, f"/uploads/{uid}/boletas"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        boletas = r.json()
        assert len(boletas) == 5
        test_company["boletas"] = boletas

    def test_10_download_pdf(self, base_url, test_company):
        cid = test_company["company_id"]
        boletas = test_company.get("boletas", [])
        assert len(boletas) > 0
        boleta = next((b for b in boletas if not b.get("es_observacion")), boletas[0])
        r = httpx.get(
            _url(base_url, cid, f"/boletas/{boleta['id']}/download"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert len(r.content) > 1000

    def test_11_get_report(self, base_url, test_company):
        cid, uid = test_company["company_id"], test_company["upload_id"]
        r = httpx.get(
            _url(base_url, cid, f"/uploads/{uid}/report"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ticket"] == test_company["ticket"]
        assert data["resumen"] is not None

    def test_12_resend_individual(self, base_url, test_company):
        cid = test_company["company_id"]
        boletas = test_company.get("boletas", [])
        assert len(boletas) > 0
        failed = [b for b in boletas if b["estado_envio"] == "fallido"]
        target = failed[0] if failed else boletas[0]
        r = httpx.post(
            _url(base_url, cid, f"/boletas/{target['id']}/resend"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200, f"Resend failed: {r.text}"

    def test_13_download_all_zip(self, base_url, test_company):
        cid, uid = test_company["company_id"], test_company["upload_id"]
        r = httpx.get(
            _url(base_url, cid, f"/uploads/{uid}/download-all"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"
        assert r.headers["content-disposition"].startswith("attachment; filename=boletas_")
        assert len(r.content) > 100

    def test_14_company_lang_config(self, base_url, test_company):
        r = httpx.put(
            f"{base_url}/companies/{test_company['company_id']}",
            json={"lang": "en"},
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200

        r = httpx.get(
            f"{base_url}/companies/{test_company['company_id']}",
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.json()["lang"] == "en"

        r = httpx.put(
            f"{base_url}/companies/{test_company['company_id']}",
            json={"lang": "es"},
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200

    def test_15_quota_status(self, base_url, test_company):
        cid = test_company["company_id"]
        r = httpx.get(
            _url(base_url, cid, "/quota-status"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["limite"] >= 10

    def test_16_list_uploads(self, base_url, test_company):
        cid = test_company["company_id"]
        r = httpx.get(
            _url(base_url, cid, "/uploads"),
            headers={"Authorization": f"Bearer {test_company['token']}"},
        )
        assert r.status_code == 200
        uploads = r.json()
        assert len(uploads) >= 1
        assert uploads[0]["ticket_number"] == test_company["ticket"]

    def test_17_i18n_translations(self, base_url):
        from app.core.i18n import t, TRANSLATIONS
        assert t("upload_success", "es") == "Planilla subida correctamente"
        assert t("upload_success", "en") == "Payroll uploaded successfully"
        assert t("license_inactive", "es", estado="vencida") == "Licencia en estado 'vencida'. No puede subir planillas."
        assert t("license_inactive", "en", estado="expired") == "License in state 'expired'. Cannot upload payrolls."
        assert "es" in TRANSLATIONS
        assert "en" in TRANSLATIONS

    def test_18_check_health(self, base_url):
        r = httpx.get(f"{base_url}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"


class TestAuth:
    """Authentication and authorization tests."""

    def test_login_invalid(self, base_url):
        r = httpx.post(
            f"{base_url}/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrong"},
        )
        assert r.status_code == 401

    def test_register_duplicate_ruc(self, base_url, test_company):
        r = httpx.post(
            f"{base_url}/auth/register",
            json={
                "company_name": "Otra Empresa",
                "company_ruc": test_company["ruc"],
                "admin_email": "another@test.com",
                "admin_password": "test123",
                "admin_full_name": "Another Admin",
            },
        )
        assert r.status_code == 400
        assert "RUC" in r.text

    def test_super_admin_list_companies(self, base_url, super_token):
        r = httpx.get(
            f"{base_url}/companies/",
            headers={"Authorization": f"Bearer {super_token}"},
        )
        assert r.status_code == 200
        companies = r.json()
        assert len(companies) >= 1


class TestRateLimiting:
    """Rate limiting tests."""

    def test_login_rate_limit(self, base_url):
        for i in range(12):
            r = httpx.post(
                f"{base_url}/auth/login",
                json={"email": "ratelimit@test.com", "password": "test"},
            )
            if i >= 10:
                assert r.status_code == 429, f"Expected 429 on attempt {i+1}"
                return
        pytest.fail("Rate limit was not triggered after 11 attempts")
