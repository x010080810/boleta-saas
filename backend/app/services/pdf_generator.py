import os
import uuid
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import fitz  # PyMuPDF
from app.services.storage import save_pdf


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "pdf")


def generate_payslip_pdf(
    employee_name: str,
    document_number: str,
    company_name: str,
    company_ruc: str,
    periodo: str,
    tipo_planilla: str,
    cargo: str,
    ingresos: dict,
    descuentos: dict,
    aportaciones: dict,
    total_ingresos: float,
    total_descuentos: float,
    neto_pagar: float,
    neto_pagar_usd: float = None,
    total_aportaciones: float = 0,
    ticket: str = "",
    dias_laborados: int = 30,
    output_dir: str = "output",
    s3_prefix: str = "",
) -> tuple:
    os.makedirs(output_dir, exist_ok=True)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("boleta.html")

    ingresos_items = []
    for k, v in ingresos.items():
        label = k.replace("ING_", "").replace("_", " ").title()
        ingresos_items.append({"label": label, "value": v})

    descuentos_items = []
    for k, v in descuentos.items():
        label = k.replace("DESC_", "").replace("_", " ").title()
        descuentos_items.append({"label": label, "value": v})

    aportaciones_items = []
    for k, v in aportaciones.items():
        label = k.replace("APOR_", "").replace("_", " ").title()
        aportaciones_items.append({"label": label, "value": v})

    html_content = template.render(
        employee_name=employee_name,
        document_number=document_number,
        company_name=company_name,
        company_ruc=company_ruc,
        periodo=periodo,
        tipo_planilla=tipo_planilla.upper(),
        cargo=cargo,
        dias_laborados=dias_laborados,
        ingresos=ingresos_items,
        descuentos=descuentos_items,
        aportaciones=aportaciones_items,
        total_ingresos=total_ingresos,
        total_descuentos=total_descuentos,
        total_aportaciones=total_aportaciones,
        neto_pagar=neto_pagar,
        neto_pagar_usd=neto_pagar_usd,
        ticket=ticket,
        fecha_emision=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )

    temp_pdf = os.path.join(output_dir, f"temp_{uuid.uuid4()}.pdf")
    HTML(string=html_content).write_pdf(temp_pdf)

    pdf_password = document_number
    final_name = f"boleta_{document_number}_{uuid.uuid4().hex[:8]}.pdf"

    doc = fitz.open(temp_pdf)
    s3_key = f"{s3_prefix}/{final_name}" if s3_prefix else final_name
    final_path = os.path.join(output_dir, final_name)
    doc.save(final_path, encryption=fitz.PDF_ENCRYPT_AES_128, user_pw=pdf_password, owner_pw=pdf_password)
    doc.close()

    with open(final_path, "rb") as f:
        pdf_bytes = f.read()
    save_pdf(pdf_bytes, s3_key)

    os.remove(temp_pdf)
    os.remove(final_path)

    return s3_key, pdf_password
