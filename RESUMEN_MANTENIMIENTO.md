# Boleta SaaS — Resumen de Mantenimiento

## Stack actual

| Componente | Servicio | URL / Acceso |
|---|---|---|
| Frontend | Vercel | https://boleta-saas.vercel.app |
| Backend API | Railway | https://boleta-saas-production.up.railway.app |
| Base de Datos | Railway PostgreSQL | `tokaido.proxy.rlwy.net:45341` (add-on `protective-smile`) |
| Storage (PDFs + backups) | Supabase S3 | Bucket `payslips` / `backups` |
| Redis (Celery broker) | Upstash | `sharp-lizard-160244.upstash.io:6379` |
| Email activo | Resend (trial) | https://resend.com |
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
| `DATABASE_URL` | `postgresql+asyncpg://postgres:RgqsoMkfPQrnuVJquvpxMwVhPuiIaaEm@tokaido.proxy.rlwy.net:45341/railway` |
| `REDIS_URL` | `rediss://default:gQAAAAAAAnH0AAIgcDEyNDI5NTk4NWNjNDA0ZDdiYjI5MDBlMDk1NGI0OTNhOA@sharp-lizard-160244.upstash.io:6379` |
| `SECRET_KEY` | `sNWOnUaWDrWSYSmlTj2Mn8SeJUDABZhstoEIA_B6v0Q` |
| `FRONTEND_URL` | `https://boleta-saas.vercel.app` |
| `MAILTRAP_API_TOKEN` | `e6947423540394d97e879c51ad44a7de` |
| `RESEND_API_KEY` | `re_gHS6yzqA_D4uzBiWMRNsWuiifYMEto5Wp` |
| `SUPABASE_S3_ENDPOINT` | `https://eryogftdkxuxyfrilstq.supabase.co/storage/v1/s3` |
| `SUPABASE_S3_ACCESS_KEY` | (S3-specific key en Railway) |
| `SUPABASE_S3_SECRET_KEY` | (S3-specific key en Railway) |
| `SUPABASE_S3_REGION` | `sa-east-1` |
| `STORAGE_BUCKET` | `payslips` |
| `SUPABASE_S3_PUBLIC_URL` | `https://eryogftdkxuxyfrilstq.supabase.co/storage/v1/object/public/payslips` |

---

## Servicios externos

### Supabase (solo Storage)
- URL: https://supabase.com → dashboard → proyecto `eryogftdkxuxyfrilstq`
- S3-compatible Storage (NO base de datos)
- Buckets: `payslips` (PDFs), `backups` (backups BD)
- Acceso vía `SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_ACCESS_KEY`, `SUPABASE_S3_SECRET_KEY`

### Railway PostgreSQL
- Host: `tokaido.proxy.rlwy.net:45341` (add-on en proyecto `protective-smile`)
- DB: `railway`, User: `postgres`, Password en Railway variables
- 14 tablas: super_admins, companies, company_users, user_company_assignments, employees, employee_company_assignments, payroll_uploads, pay_slips, unregistered_workers, email_logs, license_history, system_settings, monthly_send_quotas, webhook_events

### Upstash Redis
- URL: https://console.upstash.com
- DB: `sharp-lizard-160244` (Free)
- Broker/backend de Celery (colas de tareas)

### Resend (email activo — trial)
- URL: https://resend.com
- API Key configurada en Railway: `re_gHS6yzqA_D4uzBiWMRNsWuiifYMEto5Wp`
- **Trial:** solo envía al dueño de la cuenta (`jn835513@gmail.com`). Para enviar a cualquier destinatario, verificar dominio en https://resend.com/domains
- **Límite:** 100 emails/día (Free)
- **Propósito:** Método principal de envío. Usa HTTPS (puerto 443) → funciona en Railway.
- Cuando se verifique dominio propio (`oteroasociados-boletas-pago.com.pe`), cambiar `RESEND_FROM_EMAIL` en Railway.

### Mailtrap (fallback — sandbox)
- URL: https://mailtrap.io
- API Token en Railway: `e6947423540394d97e879c51ad44a7de`
- **Sandbox:** Solo entrega al dueño de la cuenta
- **Límite:** 1000 emails/mes (Free)
- **Propósito:** Fallback si Resend falla

### Vercel
- URL: https://vercel.com → dashboard → proyecto `boleta-saas`
- Frontend desplegado automáticamente desde `main` de GitHub
- Env var: `VITE_API_URL` = `https://boleta-saas-production.up.railway.app`

### GitHub
- URL: https://github.com/x010080810/boleta-saas
- Rama `main` con auto-deploy a Railway + Vercel
- Push protection bloquea secrets

---

## Email: estado actual

### Diferencias entre Local y Web (Railway)

| Aspecto | Local (Docker) | Web (Railway) |
|---|---|---|
| SMTP directo | ✅ Funciona (puerto 587) | ❌ Puerto 587 bloqueado |
| SMTP puerto 465 | ✅ Funciona | ✅ Funciona |
| Resend API | No configurado | ✅ Activo (trial, solo al dueño `jn835513@gmail.com`) |
| Mailtrap API | No configurado | ⚠️ Fallback (trial, solo al dueño) |
| Registro empresa | Email va al destinatario real | Email va a `jn835513@gmail.com` |

### Flujo de envío en Railway
1. **Resend** (vía API HTTPS) — método principal
2. **Mailtrap** (vía API HTTPS) — fallback si Resend falla
3. **SMTP** (puerto 465) — último recurso, solo si las APIs fallan

### Para producción (enviar a cualquier destinatario)
- Opción A: Verificar dominio en Resend (`oteroasociados-boletas-pago.com.pe`) → cambiar `RESEND_FROM_EMAIL`
- Opción B: Cada empresa usa SMTP directo desde Local (Docker)

---

## Orden de envío de email (local)

1. **Resend** (si `RESEND_API_KEY` configurado) — solo si hay API key
2. **Mailtrap** (si `MAILTRAP_API_TOKEN` configurado) — solo si hay token
3. **SMTP** (puerto 465/587) — siempre que haya credenciales en BD/env

> En local, como no hay API keys configuradas, envía directo por SMTP.
> En Railway, prueba primero Resend → Mailtrap → SMTP (puerto 465).

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
      - Si hay cuota: enviar email (Resend/Mailtrap/SMTP según entorno y credenciales, con PDF adjunto)
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

- PDF: conceptos con valor >0 ahora se muestran (fix case-insensitive en `tasks/payroll.py`)
- Refactor completo de `email_sender.py`: método SMTP unificado, todas las funciones simplificadas
- Notificaciones al crear usuario desde admin: bienvenida al nuevo usuario + aviso a admins de la empresa
- Puerto SMTP cambiado a 465 para compatibilidad con Railway
- Resend como método principal de envío (trial, envía al dueño de la cuenta)
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
|---|---|---|
| Resend trial | Solo envía al dueño de la cuenta (`jn835513@gmail.com`). No puede enviar a destinatarios arbitrarios sin dominio verificado |
| Mailtrap sandbox | Misma limitación que Resend: solo al dueño de la cuenta |
| Sin dominio verificado | `oteroasociados-boletas-pago.com.pe` sin DNS configurado. Resend no puede enviar desde ese dominio |
| Railway puerto 587 bloqueado | SMTP en puerto 587 no funciona. Se usa puerto 465 como alternativa |
| Railway Free | Contenedor duerme tras inactividad. Developer ($5/mes) elimina sleep |
| Backups rotos | `pg_dump` no disponible en Railway Docker. Backups automáticos no funcionan |
| Local vs Web | En Local el SMTP funciona directo; en Web todo debe pasar por `jn835513@gmail.com` |

---

## Costos mensuales

| Servicio | Plan | Costo |
|---|---|---|
| Railway (API + PostgreSQL) | Free | $0 |
| Supabase (S3 Storage) | Free | $0 |
| Upstash Redis | Free | $0 |
| Vercel (Frontend) | Hobby | $0 |
| Resend (Email) | Free (100 emails/día) | $0 |
| Mailtrap (Email fallback) | Free (1000 emails/mes) | $0 |
| **Total** | | **$0/mes** |
