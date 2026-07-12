import os
import uuid
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import fitz  # PyMuPDF


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
    final_pdf = os.path.join(output_dir, f"boleta_{document_number}_{uuid.uuid4().hex[:8]}.pdf")

    doc = fitz.open(temp_pdf)
    doc.save(final_pdf, encryption=fitz.PDF_ENCRYPT_AES_128, user_pw=pdf_password, owner_pw=pdf_password)
    doc.close()

    os.remove(temp_pdf)

    return final_pdf, pdf_password
