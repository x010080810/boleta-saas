TRANSLATIONS = {
    "es": {
        "upload_success": "Planilla subida correctamente",
        "upload_failed": "Error al subir planilla",
        "processing_started": "Procesamiento iniciado en segundo plano",
        "processing_completed": "Procesamiento completado",
        "processing_failed": "Procesamiento fallido",
        "boleta_sent": "Boleta enviada",
        "boleta_failed": "Error al enviar boleta",
        "boleta_not_sent": "No enviado por saldo insuficiente",
        "no_quota": "Sin saldo disponible en el plan mensual",
        "employee_not_found": "Empleado no registrado en el maestro",
        "boleta_sent_to_company": "Boleta enviada al correo remitente de la empresa",
        "license_inactive": "Licencia en estado '{estado}'. No puede subir planillas.",
        "company_not_found": "Empresa no encontrada",
        "upload_not_found": "Carga no encontrada",
        "boleta_not_found": "Boleta no encontrada",
        "file_not_found": "Archivo PDF no encontrado en disco",
        "invalid_format": "Formato de archivo inválido. Use .xls o .xlsx",
        "file_too_large": "Archivo excede el tamaño máximo de {max_size}MB",
        "already_processed": "La carga ya fue procesada o está en estado '{estado}'",
        "credentials_invalid": "Credenciales inválidas",
        "user_inactive": "Usuario inactivo",
        "ruc_exists": "El RUC ya está registrado",
        "email_exists": "El email ya está registrado",
        "resend_success": "Boleta re-enviada con éxito",
        "resend_failed": "Error al re-enviar boleta",
        "zip_download": "boletas_{ticket}.zip",
        "email_subject": "Boleta de Pago - {empresa} - {periodo}",
        "email_body": """
<html><body>
<p>Estimado(a) <strong>{nombre}</strong>,</p>
<p>Su boleta de pago correspondiente a <strong>{empresa}</strong> - periodo {periodo} ha sido generada.</p>
<p>Adjunto encontrara su boleta de pago en formato PDF.</p>
<p><strong>Contrasena de apertura:</strong> Su numero de documento</p>
<p>Ticket de referencia: {ticket}</p>
<br>
<p>Saludos cordiales,</p>
<p><strong>{empresa}</strong></p>
</body></html>""",
        "notification_subject": "Procesamiento de Planilla Completado - Ticket #{ticket} | {empresa}",
        "expiry_subject": "Su licencia del Sistema de Boletas vence en {dias} dias",
    },
    "en": {
        "upload_success": "Payroll uploaded successfully",
        "upload_failed": "Error uploading payroll",
        "processing_started": "Processing started in background",
        "processing_completed": "Processing completed",
        "processing_failed": "Processing failed",
        "boleta_sent": "Payslip sent",
        "boleta_failed": "Error sending payslip",
        "boleta_not_sent": "Not sent due to insufficient quota",
        "no_quota": "No quota available in monthly plan",
        "employee_not_found": "Employee not registered in master",
        "boleta_sent_to_company": "Payslip sent to company remitent email",
        "license_inactive": "License in state '{estado}'. Cannot upload payrolls.",
        "company_not_found": "Company not found",
        "upload_not_found": "Upload not found",
        "boleta_not_found": "Payslip not found",
        "file_not_found": "PDF file not found on disk",
        "invalid_format": "Invalid file format. Use .xls or .xlsx",
        "file_too_large": "File exceeds maximum size of {max_size}MB",
        "already_processed": "Upload already processed or in state '{estado}'",
        "credentials_invalid": "Invalid credentials",
        "user_inactive": "Inactive user",
        "ruc_exists": "RUC already registered",
        "email_exists": "Email already registered",
        "resend_success": "Payslip resent successfully",
        "resend_failed": "Error resending payslip",
        "zip_download": "payslips_{ticket}.zip",
        "email_subject": "Payslip - {empresa} - {periodo}",
        "email_body": """
<html><body>
<p>Dear <strong>{nombre}</strong>,</p>
<p>Your payslip for <strong>{empresa}</strong> - period {periodo} has been generated.</p>
<p>Please find attached your payslip in PDF format.</p>
<p><strong>Opening password:</strong> Your document number</p>
<p>Reference ticket: {ticket}</p>
<br>
<p>Best regards,</p>
<p><strong>{empresa}</strong></p>
</body></html>""",
        "notification_subject": "Payroll Processing Completed - Ticket #{ticket} | {empresa}",
        "expiry_subject": "Your payslip system license expires in {dias} days",
    },
}


def t(key: str, lang: str = "es", **kwargs) -> str:
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["es"])
    text = translations.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_lang_from_header(accept_language: str = "es") -> str:
    if accept_language:
        lang = accept_language.split(",")[0].split("-")[0].lower()
        if lang in TRANSLATIONS:
            return lang
    return "es"
