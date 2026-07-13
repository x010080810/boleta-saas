# Boleta SaaS — Resumen de Mantenimiento

## Stack

| Componente | Servicio | URL / Acceso |
|---|---|---|
| Frontend | Vercel | https://boleta-saas.vercel.app |
| Backend API | Railway | https://boleta-saas-production.up.railway.app |
| Base de Datos | Supabase | `db.eryogftdkxuxyfrilstq.supabase.co` |
| Storage (PDFs) | Supabase S3 | Bucket `payslips` |
| Redis | Upstash | `sharp-lizard-160244.upstash.io:6379` |
| Email | Mailtrap | https://mailtrap.io |
| Email (fallback) | Resend | https://resend.com |
| Email (fallback) | SendGrid | https://sendgrid.com |
| Código | GitHub | https://github.com/x010080810/boleta-saas |

---

## URLs funcionales

| URL | Descripción |
|---|---|
| https://boleta-saas.vercel.app | Frontend (usuarios finales) |
| https://boleta-saas-production.up.railway.app | Backend API |
| https://boleta-saas-production.up.railway.app/api/health | Health check |
| https://boleta-saas-production.up.railway.app/api/setup | Setup super admin (POST) |
| https://boleta-saas-production.up.railway.app/docs | Swagger UI (FastAPI docs) |

---

## Credenciales de acceso

### Super Admin (sistema)
| Campo | Valor |
|---|---|
| Email | `jn835513@gmail.com` |
| Password | `66*z$3nZ093ZpIyZ` |

> **Nota:** Para regenerar, ejecutar `POST /api/setup` con header `X-Setup-Key: sNWOnUaWDrWSYSmlTj2Mn8SeJUDABZhstoEIA_B6v0Q`. Genera nueva password automáticamente.

---

### App Password de Gmail (16 dígitos)

Para que el sistema pueda enviar correos SMTP desde `jn835513@gmail.com` (cuando esté en un VPS que no bloquee puertos):

1. Ir a https://myaccount.google.com/security
2. Activar **Verificación en dos pasos** (si no lo está)
3. Ir a **Contraseñas de aplicaciones** (buscar en la barra de Google)
4. Seleccionar **Correo** + **Windows** (u otro dispositivo)
5. Copiar la **contraseña de 16 dígitos** que genera

---

## Configuración SMTP del Sistema (en el frontend)

Al entrar como super admin, ir a **Configuración del Sistema** → **SMTP** y configurar:

| Campo | Valor |
|---|---|
| Host | `smtp.gmail.com` |
| Puerto | `587` |
| Usuario | `jn835513@gmail.com` |
| Password | App Password de 16 dígitos (generado desde tu Gmail) |
| Email from | `jn835513@gmail.com` |
| Nombre from | `Boleta SaaS` |

> **Importante en Railway:** Railway bloquea puertos SMTP (587/465/25). Esta configuración no funciona en Railway. El envío real usa **Mailtrap** automáticamente (HTTPS). La config SMTP se usa solo como `Reply-To`. Cuando el backend esté en un VPS sin bloqueo de puertos, el SMTP funcionará directamente.

### Configuración SMTP de cada empresa (Reply-To)

Cada empresa configura su propio Gmail en **Empresa** → **Configuración** → **SMTP**. Esa dirección se usa como `Reply-To` en los correos. El envío real sigue yendo por Mailtrap.

---

## Variables de entorno — Railway

Configuradas en https://railway.app → dashboard → `backend` → Variables

| Variable | Valor |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:lI28KCz3mTYJ2bm5@db.eryogftdkxuxyfrilstq.supabase.co:5432/postgres` |
| `REDIS_URL` | `rediss://default:gQAAAAAAAnH0AAIgcDEyNDI5NTk4NWNjNDA0ZDdiYjI5MDBlMDk1NGI0OTNhOA@sharp-lizard-160244.upstash.io:6379` |
| `SECRET_KEY` | `sNWOnUaWDrWSYSmlTj2Mn8SeJUDABZhstoEIA_B6v0Q` |
| `FRONTEND_URL` | `https://boleta-saas.vercel.app` |
| `MAILTRAP_API_TOKEN` | `97868e26191c0f30a752675049347812` |
| `RESEND_API_KEY` | `re_4t7y3QyR_PR87vT8da2uquBdstW7Yq32u` |
| `RESEND_FROM_EMAIL` | `jn835513@gmail.com` |
| `SUPABASE_S3_ENDPOINT` | `https://eryogftdkxuxyfrilstq.supabase.co/storage/v1/s3` |
| `SUPABASE_S3_ACCESS_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyeW9nZnRka3h1eHlmcmlsc3RxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM4MDYwNzQsImV4cCI6MjA5OTM4MjA3NH0.POOeJBkus8VqrqWBXZwiCx2MyeHLPtbgauNDqTDFkDg` |
| `SUPABASE_S3_SECRET_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyeW9nZnRka3h1eHlmcmlsc3RxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzgwNjA3NCwiZXhwIjoyMDk5MzgyMDc0fQ.lPl0uIzwtG5VpD2Ztb0BjBszZy_j9h2aFlXwE48ajM0` |
| `SUPABASE_S3_REGION` | `sa-east-1` |
| `STORAGE_BUCKET` | `payslips` |
| `SUPABASE_S3_PUBLIC_URL` | `https://eryogftdkxuxyfrilstq.supabase.co/storage/v1/object/public/payslips` |

---

## Servicios externos

### Supabase
- URL: https://supabase.com → dashboard → proyecto `eryogftdkxuxyfrilstq`
- Tablas: companies, company_users, employees, pay_slips, payroll_uploads, email_logs, monthly_send_quotas, license_history, super_admins, system_settings, webhook_events
- Storage: bucket `payslips` (PDFs generados)

### Upstash Redis
- URL: https://console.upstash.com
- Base de datos: `sharp-lizard-160244` (plan Free)
- Usado como broker/backend de Celery

### Mailtrap (email activo)
- URL: https://mailtrap.io
- Email API Token: `97868e26191c0f30a752675049347812`
- Sandbox domain: `demomailtrap.co`
- Recipientes autorizados: `jn835513@gmail.com`
- **Límite:** 1000 emails/mes (plan Free)

### Resend (fallback)
- URL: https://resend.com
- API Key: `re_4t7y3QyR_PR87vT8da2uquBdstW7Yq32u`
- Estado: **inactivo** (requiere dominio verificado para enviar a destinatarios arbitrarios)

### Vercel
- URL: https://vercel.com → dashboard → proyecto `boleta-saas`
- Frontend desplegado
- Env var requerida: `VITE_API_URL` = `https://boleta-saas-production.up.railway.app`

### GitHub
- URL: https://github.com/x010080810/boleta-saas
- Rama: `main` (auto-deploy a Railway + Vercel)
- Push protection: bloquea secrets (OAuth credentials, etc.)
- .gitattributes: LF line endings para `.sh`, `.py`, `Dockerfile`

---

## Orden de envío de email

Cuando se envía una boleta, el sistema prueba en este orden:

1. **Resend** → si `RESEND_API_KEY` configurado
2. **Gmail API** → si `GMAIL_TOKEN_JSON` configurado
3. **SendGrid** → si `SENDGRID_API_KEY` configurado
4. **Mailtrap** → si `MAILTRAP_API_TOKEN` configurado ← **activo ahora**
5. **SMTP directo** → bloqueado en Railway (puertos 587/465/25)

**Comportamiento actual:** Mailtrap es el método activo. El remitente se muestra como `usuario@demomailtrap.co` y el `Reply-To` es el email configurado por la empresa.

---

## Comandos útiles

### Regenerar super admin
```powershell
curl.exe -s -X POST https://boleta-saas-production.up.railway.app/api/setup `
  -H "X-Setup-Key: sNWOnUaWDrWSYSmlTj2Mn8SeJUDABZhstoEIA_B6v0Q"
```

### Health check
```powershell
curl.exe -s https://boleta-saas-production.up.railway.app/api/health
```

### Login super admin
```powershell
$body = '{"email":"jn835513@gmail.com","password":"66*z$3nZ093ZpIyZ"}'
curl.exe -s -X POST https://boleta-saas-production.up.railway.app/api/auth/super-login `
  -H "Content-Type: application/json" -d $body
```

---

## Mantenimiento diario

- **Backups:** Se ejecutan automáticamente via Celery Beat y se suben a Supabase S3 bucket `backups/`
- **Licencias:** Celery Beat verifica licencias próximas a vencer (15 días) y actualiza estados
- **Monitoreo:** Revisar Railway logs (History) para errores de fondo
- **PDFs:** Se almacenan en Supabase S3 (persistentes, no se pierden al redeploy)

---

## Limitaciones conocidas

| Limitación | Detalle |
|---|---|
| Email solo a autorizados | Mailtrap sandbox solo entrega a `jn835513@gmail.com`. Para más destinatarios, agregar en Mailtrap → Recipients |
| Sin dominio custom | `oteroasociados.com.pe` no está conectado. Cuando tengas acceso DNS, se puede apuntar frontend y verificar dominio en Resend |
| Railway Free | Contenedor duerme tras inactividad. Mejorar a Developer ($5/mes) desactiva sleep y da más RAM |
| PDF en `/tmp` | WeasyPrint escribe en `/tmp` (efímero). No hay problema porque luego se sube a Supabase S3 |
| Sin Background Functions | Procesar batch de 50+ boletas puede tardar. Celery Worker en el mismo contenedor lo maneja |

---

## Costos mensuales

| Servicio | Plan | Costo |
|---|---|---|
| Railway | Free (Developer $5 opcional) | $0 |
| Supabase | Free | $0 |
| Upstash | Free | $0 |
| Mailtrap | Free (1000 emails/mes) | $0 |
| Vercel | Hobby | $0 |
| Resend | Free (inactivo) | $0 |
| **Total** | | **$0/mes** |
