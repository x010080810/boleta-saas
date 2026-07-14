# Boleta SaaS — Resumen de Mantenimiento

## Stack actual

| Componente | Servicio | URL / Acceso |
|---|---|---|
| Frontend | Vercel | https://boleta-saas.vercel.app |
| Backend API | Railway | https://boleta-saas-production.up.railway.app |
| Base de Datos | Supabase PostgreSQL | `db.eryogftdkxuxyfrilstq.supabase.co:5432` |
| Storage (PDFs + backups) | Supabase S3 | Bucket `payslips` / `backups` |
| Redis (Celery broker) | Upstash | `sharp-lizard-160244.upstash.io:6379` |
| Email activo | Mailtrap sandbox | https://mailtrap.io |
| Código | GitHub | https://github.com/x010080810/boleta-saas |

---

## URLs funcionales

| URL | Descripción |
|---|---|
| https://boleta-saas.vercel.app | Frontend (usuarios finales) |
| https://boleta-saas-production.up.railway.app/api/health | Health check |
| https://boleta-saas-production.up.railway.app/docs | Swagger UI (FastAPI docs) |

---

## Credenciales de super admin

| Campo | Valor |
|---|---|
| Email | `jn835513@gmail.com` |
| Password | `tLTEIxODb!p!d^X1` |

Para regenerar, ejecutar `POST /api/setup` con header `X-Setup-Key: sNWOnUaWDrWSYSmlTj2Mn8SeJUDABZhstoEIA_B6v0Q`.

---

## Variables de entorno — Railway

Configuradas en https://railway.app → dashboard → Variables

| Variable | Valor |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:lI28KCz3mTYJ2bm5@db.eryogftdkxuxyfrilstq.supabase.co:5432/postgres` |
| `REDIS_URL` | `rediss://default:gQAAAAAAAnH0AAIgcDEyNDI5NTk4NWNjNDA0ZDdiYjI5MDBlMDk1NGI0OTNhOA@sharp-lizard-160244.upstash.io:6379` |
| `SECRET_KEY` | `sNWOnUaWDrWSYSmlTj2Mn8SeJUDABZhstoEIA_B6v0Q` |
| `FRONTEND_URL` | `https://boleta-saas.vercel.app` |
| `MAILTRAP_API_TOKEN` | `97868e26191c0f30a752675049347812` |
| `RESEND_API_KEY` | `re_4t7y3QyR_PR87vT8da2uquBdstW7Yq32u` |
| `SUPABASE_S3_ENDPOINT` | `https://eryogftdkxuxyfrilstq.supabase.co/storage/v1/s3` |
| `SUPABASE_S3_ACCESS_KEY` | (S3-specific key en Railway) |
| `SUPABASE_S3_SECRET_KEY` | (S3-specific key en Railway) |
| `SUPABASE_S3_REGION` | `sa-east-1` |
| `STORAGE_BUCKET` | `payslips` |
| `SUPABASE_S3_PUBLIC_URL` | `https://eryogftdkxuxyfrilstq.supabase.co/storage/v1/object/public/payslips` |

---

## Servicios externos

### Supabase
- URL: https://supabase.com → dashboard → proyecto `eryogftdkxuxyfrilstq`
- BD PostgreSQL + S3-compatible Storage
- 14 tablas: super_admins, companies, company_users, user_company_assignments, employees, employee_company_assignments, payroll_uploads, pay_slips, unregistered_workers, email_logs, license_history, system_settings, monthly_send_quotas, webhook_events
- Buckets: `payslips` (PDFs), `backups` (backups BD)

### Upstash Redis
- URL: https://console.upstash.com
- DB: `sharp-lizard-160244` (Free)
- Broker/backend de Celery (colas de tareas)

### Mailtrap (email activo — sandbox)
- URL: https://mailtrap.io
- API Token en Railway
- **Sandbox:** reescribe el `from` a `@demomailtrap.co`. Solo entrega a destinatarios autorizados.
- **Límite:** 1000 emails/mes (Free)
- **Propósito:** Solo para pruebas. No se puede usar con `from` real de la empresa.

### Resend (fallback inactivo)
- URL: https://resend.com
- API Key configurada en Railway
- **Inactivo:** requiere dominio verificado para enviar a destinatarios arbitrarios
- Será útil cuando se verifique dominio propio (ej. `boleta.oteroasociados.com.pe`)

### Vercel
- URL: https://vercel.com → dashboard → proyecto `boleta-saas`
- Frontend desplegado automáticamente desde `main` de GitHub
- Env var: `VITE_API_URL` = `https://boleta-saas-production.up.railway.app`

### GitHub
- URL: https://github.com/x010080810/boleta-saas
- Rama `main` con auto-deploy a Railway + Vercel
- Push protection bloquea secrets

---

## Email: estado actual y hoja de ruta

### Problema
Railway **bloquea SMTP** (puertos 25/465/587). La única forma de enviar correos es vía API HTTPS.
Mailtrap sandbox **reescribe el `from`**, por lo que el correo no llega desde la dirección real de la empresa.

### Requisito
El correo debe originarse desde la dirección real de la empresa (ej. `rrhh@empresa.com`), no desde un dominio genérico.

### Solución planificada: Gmail API (OAuth2)
- Usa HTTPS (puerto 443) → funciona en Railway
- Preserva el `from` real de la cuenta Gmail de cada empresa
- Cada empresa configura su propio Gmail OAuth2 token
- Sin límite de destinatarios (sujeto a cuotas de Gmail)

### Mientras tanto
- Mailtrap es el método activo para pruebas con `from` reescrito
- `Reply-To` se configura al email real de la empresa (para que las respuestas lleguen al destinatario correcto)
- Resend está configurado como respaldo cuando se active con dominio verificado
- SendGrid y SMTP directo fueron **removidos** (inactivos, sin API key)

---

## Orden de envío de email

1. **Mailtrap** (si `MAILTRAP_API_TOKEN` configurado) — **método activo actual**
2. **Resend** (si `RESEND_API_KEY` configurado) — inactivo (falta dominio verificado)
3. **Gmail API** (cuando se implemente OAuth2)
4. ~~SMTP directo~~ — bloqueado en Railway (removido)

El sistema prueba cada método en orden. Si uno falla, pasa al siguiente.

---

## Flujo del proceso (subir planilla → boleta enviada)

```
1. SUBIR EXCEL
   POST /uploads → valida archivo (.xls/.xlsx), guarda en /tmp,
   parsea con pandas, crea PayrollUpload (estado: pending), genera ticket

2. PREVISUALIZAR
   GET /uploads/{id}/preview → parsea Excel, cruza empleados vs. maestro,
   muestra tabla con detección de columnas

3. CONFIRMAR Y PROCESAR
   POST /uploads/{id}/process → cambia estado a "processing",
   dispara Celery task en segundo plano, retorna inmediato

4. CELERY TASK (background)
   a. Parsear Excel nuevamente
   b. Verificar cuota del mes (MonthlySendQuota)
   c. Por cada empleado:
      - Buscar en Employee (maestro)
      - Resolver email destino
      - Generar PDF: Jinja2 → HTML → WeasyPrint → PyMuPDF (AES-128,
        password = nro documento)
      - Subir PDF a Supabase S3
      - Crear PaySlip record
      - Si hay cuota: enviar email (Mailtrap vía HTTPS con PDF adjunto)
      - Si no hay cuota: marcar "no_enviado_sin_saldo"
   d. Actualizar contadores del upload
   e. Marcar upload como "completed"
   f. Enviar email de notificación a la empresa
   g. Commit en BD

5. VER REPORTE
   GET /uploads/{id}/report → resumen, observaciones, detalle envíos
   GET /uploads/{id}/boletas → lista de boletas con estado de envío
   GET /uploads/{id}/status → estado actual del proceso

6. DESCARGAR
   GET /boletas/{id}/download → PDF individual desde S3
   GET /uploads/{id}/download-all → ZIP con todos los PDFs desde S3

7. RE-ENVIAR
   POST /uploads/{id}/resend → re-envía boletas seleccionadas
   (mismo flujo de email)
```

### Estados de un upload
- `pending` → recién subido, sin procesar. Se puede eliminar con `DELETE`.
- `processing` → Celery task ejecutándose (polling cada 3s desde frontend)
- `completed` → proceso terminado exitosamente
- `failed` → error durante el procesamiento

### Tickets "pending" abandonados
Si un usuario sube un Excel pero **nunca** hace clic en "Confirmar y Procesar", el ticket pending se elimina automáticamente al:
- Navegar a otra página (cleanup al desmontar componente)
- Subir otro Excel (se reemplaza)
- Hacer clic en "Procesar ahora" desde la página del reporte

---

## API — Endpoints relevantes

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/companies/{id}/payroll/uploads` | Subir Excel |
| GET | `/companies/{id}/payroll/uploads/{uid}/preview` | Previsualizar |
| POST | `/companies/{id}/payroll/uploads/{uid}/process` | Procesar (dispara Celery) |
| GET | `/companies/{id}/payroll/uploads/{uid}/status` | Estado del proceso |
| GET | `/companies/{id}/payroll/uploads/{uid}/report` | Reporte completo |
| GET | `/companies/{id}/payroll/uploads/{uid}/boletas` | Lista de boletas |
| DELETE | `/companies/{id}/payroll/uploads/{uid}` | Eliminar upload pending |
| GET | `/companies/{id}/payroll/boletas/{bid}/download` | Descargar PDF |
| GET | `/companies/{id}/payroll/uploads/{uid}/download-all` | Descargar ZIP |
| POST | `/companies/{id}/payroll/uploads/{uid}/resend` | Re-enviar boletas |
| POST | `/admin/companies` | Crear empresa (super admin) |

---

## Tareas programadas (Celery Beat)

Cada 24h se ejecutan:
- `check_expiring_licenses` — notifica licencias próximas a vencer (15 días)
- `update_license_states` — transición automática de estados de licencia
- `backup_database` — backup de BD a Supabase S3 (bucket `backups/`)

> **Nota:** `backup_database` requiere `pg_dump` en el contenedor. Si Railway no lo tiene instalado, falla silenciosamente.

---

## Mejoras recientes

- Correo de bienvenida y notificación al super admin al crear empresa desde admin
- Botón "Seleccionar archivo" / "Ningún archivo seleccionado" en español
- Redirección correcta a reporte con `companyId` en ruta
- Banner de upload pending con botón "Procesar ahora"
- Reversión automática de tickets pending abandonados
- Manejo de estado "pending" en reporte (ya no muestra pantalla vacía)
- Read PDF desde Supabase S3 (no desde filesystem local)
- Config `signature_version='s3v4'` en boto3

---

## Limitaciones conocidas

| Limitación | Detalle |
|---|---|
| Email sandbox | Mailtrap reescribe `from`. Solo para pruebas a `jn835513@gmail.com` |
| Sin Gmail API OAuth2 | El método que preservaría el `from` real de cada empresa aún no está implementado |
| Sin dominio custom | `oteroasociados.com.pe` sin DNS configurado. Serviría para Resend y frontend propio |
| Railway Free | Contenedor duerme tras inactividad. Developer ($5/mes) elimina sleep |
| Backups rotos | `pg_dump` no disponible en Railway Docker. Backups automáticos no funcionan |
| Scripts eliminados | `scripts/setup_gmail_oauth.py`, `check_mailtrap.py`, `check_railway.py` — obsoletos, removidos |

---

## Costos mensuales

| Servicio | Plan | Costo |
|---|---|---|
| Railway | Free | $0 |
| Supabase | Free | $0 |
| Upstash | Free | $0 |
| Mailtrap | Free (1000 emails/mes) | $0 |
| Vercel | Hobby | $0 |
| Resend | Free (inactivo) | $0 |
| **Total** | | **$0/mes** |
