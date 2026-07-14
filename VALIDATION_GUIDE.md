# Guía de Validación — Flujo Completo

> ⚠️ **Importante:** Esta guía aplica para entorno **Local (Docker)**.
> Para pruebas en **Web (Railway/Vercel)** ver diferencias al final.

## Prerrequisitos

```bash
docker compose up -d
# Esperar ~10s a que todos los servicios inicien
```

Si es la primera vez o se reseteó la base, ejecutar el seed (solo crea el Super Admin):
```bash
docker compose exec backend python seed.py
```

Credenciales del Super Admin:
- **Email:** `admin@sistema.com`
- **Password:** `123456`

---

## Paso 1: Registrar una empresa desde la UI

1. Abrir [http://localhost:5173/register](http://localhost:5173/register)
2. Completar el formulario:

| Campo | Local (Docker) | Web (Railway) |
|---|---|---|
| Empresa | `Mi Empresa S.A.C.` | `Mi Empresa S.A.C.` |
| RUC | `20123456789` | `20123456789` |
| Nombre completo | `Juan Pérez` | `Admin Test` |
| Email | `juan@miempresa.com` | **`jn835513@gmail.com`** |
| Contraseña | `123456` | `TestPass123!` |

3. Click **"Registrar Empresa"**
4. ✅ Aparece pantalla **"¡Registro Exitoso!"**
5. ✅ Redirige automáticamente a `/login` tras 2 segundos

> **Web:** Usar `jn835513@gmail.com` como email admin para recibir correos (Resend trial solo envía al dueño de la cuenta).

---

## Paso 2: Iniciar sesión como empresa nueva

1. En [http://localhost:5173/login](http://localhost:5173/login) ingresar:
   - **Email:** `juan@miempresa.com` (o `jn835513@gmail.com` en web)
   - **Contraseña:** `123456` (o `TestPass123!` en web)
2. ✅ Accede al dashboard con los datos del plan trial:
   - 50 envíos/mes
   - 30 días de vigencia
   - 90 días de gracia

---

## Paso 3: Configurar SMTP de la empresa

### Local (Docker)
1. Ir a **"Configuración"** → **"Configuración SMTP"**
2. Usar credenciales Gmail reales (puerto **587**):

| Campo | Ejemplo |
|---|---|
| Servidor SMTP | `smtp.gmail.com` |
| Puerto | `587` |
| Usuario SMTP | `tu_correo@gmail.com` |
| Contraseña SMTP | *(contraseña de aplicación de Gmail)* |
| Correo Remitente | `tu_correo@gmail.com` |
| Nombre Remitente | `Mi Empresa` |

3. ✅ Click **"Guardar Configuración"**

### Web (Railway)
- Railway **bloquea** el puerto 587. Usa **puerto 465** si configuras SMTP directo.
- Pero el email funciona vía **Resend** (trial), que solo envía al dueño `jn835513@gmail.com`.
- Configura la empresa con:
  - **Email admin:** `jn835513@gmail.com`
  - **Correo remitente:** `jn835513@gmail.com`

> **Nota:** Sin SMTP configurado, los envíos de boletas fallarán. Las credenciales SMTP se guardan por empresa.

## Paso 4: Gestionar empleados

### Opción A — Agregar manualmente
1. Ir a **"Empleados"** (menú lateral)
2. Click **"Agregar Empleado"**
3. Llenar: tipo documento, número documento, nombre, email, cargo, fecha ingreso
4. ✅ Empleado aparece en el listado

### Opción B — Carga masiva desde Excel
1. Ir a **"Planillas"** → **"Descargar Plantilla Excel"**
2. Abrir el archivo descargado y llenar con datos de empleados
3. Guardar el archivo

---

## Paso 5: Subir y procesar planilla

1. Ir a **"Planillas"** → **"Subir Planilla"**
2. Click para seleccionar el archivo Excel (o arrastrar)
3. Seleccionar tipo de planilla: `Ordinaria`
4. Click **"Subir"**
5. ✅ Se muestra preview con los registros detectados
6. Click **"Procesar"** para generar y enviar las boletas
7. ✅ La planilla pasa a estado `processing` → luego `completed`

---

## Paso 6: Revisar resultados

1. Ir a **"Planillas"** → **"Historial"**
2. ✅ Se ve la planilla subida con su ticket, fecha, total registros
3. Click en **"Ver Reporte"**
4. ✅ Reporte con:
   - Totales: procesados, enviados, fallidos, observados
   - Tabla de boletas con estado individual
   - Gráfico de resumen

### Validar PDF — conceptos

1. Click en **"Descargar PDF"** de una boleta
2. Abrir el PDF (contraseña: número de documento del empleado)
3. ✅ Verificar que el PDF muestre:
   - **Todos los conceptos** con valor > 0 (ingresos, descuentos, aportaciones)
   - Cada concepto con su nombre y monto individual
   - **Totales** al final de cada sección
   - **Resumen** al final (Total Ingresos, Total Descuentos, Neto a Pagar)
4. ❌ Si solo se ven los totales sin conceptos individuales, verificar que las columnas del Excel usen prefijos `ING_`, `DESC_`, `APOR_` (case-insensitive, el sistema normaliza a minúsculas)

---

## Paso 7: Acceder como Super Admin

1. Ir a [http://localhost:5173/login](http://localhost:5173/login)
2. Marcar **"Iniciar como Super Admin"**
3. Credenciales:
   - **Email:** `admin@sistema.com`
   - **Password:** `123456`
4. ✅ Panel Super Admin con:
   - Dashboard con estadísticas (total empresas, activas, por vencer, etc.)
   - Listado de empresas con estado de licencia y consumo
   - Detalle de cada empresa con opción de actualizar licencia

---

## Paso 8: Validar notificaciones por email

### Local (Docker)
El sistema usa SMTP directo. Configurar en `backend/.env`:

```env
SYSTEM_SMTP_HOST=smtp.gmail.com
SYSTEM_SMTP_PORT=587
SYSTEM_SMTP_USER=tu_correo@gmail.com
SYSTEM_SMTP_PASSWORD=tu_contraseña_app
SYSTEM_SMTP_FROM_EMAIL=tu_correo@gmail.com
SYSTEM_SMTP_FROM_NAME=Boleta SaaS
```

### Web (Railway)
El sistema prueba: **Resend** → **Mailtrap** → **SMTP** (puerto 465).

Resend está en **trial**: solo envía al dueño de la cuenta (`jn835513@gmail.com`).
Por lo tanto:
- El **email admin** al registrar empresa debe ser `jn835513@gmail.com`
- El **super admin** debe tener email `jn835513@gmail.com`
- La **notificación** y **bienvenida** llegarán a `jn835513@gmail.com`

### Flujos de email

| Evento | Remitente | Destinatario | Local | Web |
|---|---|---|---|---|
| Registro empresa | Sistema | Admin de la empresa | ✅ Al email del admin | ✅ Solo a `jn835513@gmail.com` |
| Registro empresa | Sistema | Super Admin | ✅ `admin@sistema.com` | ✅ `jn835513@gmail.com` |
| Crear usuario (admin) | Sistema | Nuevo usuario | ✅ Al email del usuario | ✅ Solo a `jn835513@gmail.com` |
| Crear usuario (admin) | Sistema | Admins de la empresa | ✅ A cada admin | ✅ Solo a `jn835513@gmail.com` |
| Boleta de pago | SMTP empresa | Trabajador | ✅ Al email del trabajador | ⚠️ Si SMTP empresa configurado |

---

## Resumen de rutas

| Ruta | Descripción |
|---|---|
| `/login` | Inicio de sesión |
| `/register` | Registro de nueva empresa |
| `/` | Dashboard empresa |
| `/employees` | Gestión de empleados |
| `/payroll/upload` | Subir planilla |
| `/payroll/history` | Historial de planillas |
| `/settings` | Configuración SMTP y plantillas |
| `/admin` | Dashboard Super Admin |
| `/admin/companies` | Listado de empresas (Super Admin) |

---

## Reseteo rápido de base de datos

> 🔒 **No truncar** `super_admins` ni `system_settings` — contienen configuraciones críticas.

### Local (Docker)

```bash
# Truncar solo tablas de negocio (preserva super_admins y system_settings)
docker compose exec db psql -U boleta_user -d boleta_saas -c "
TRUNCATE TABLE
  companies, company_users, email_logs,
  employee_company_assignments, employees,
  license_history, monthly_send_quotas,
  pay_slips, payroll_uploads, unregistered_workers,
  user_company_assignments, webhook_events
CASCADE;
"

# Re-ejecutar seed (solo si no hay super_admin)
docker compose exec backend python seed.py
```

### Web (Railway)

```bash
# Conectar y truncar a través del túnel de Railway
python -c "
import psycopg2
conn = psycopg2.connect(
    host='tokaido.proxy.rlwy.net', port=45341,
    user='postgres',
    password='<PASSWORD de Railway DATABASE_URL>',
    dbname='railway'
)
conn.autocommit = True
cur = conn.cursor()
tables = ['companies','company_users','email_logs',
          'employee_company_assignments','employees',
          'license_history','monthly_send_quotas',
          'pay_slips','payroll_uploads','unregistered_workers',
          'user_company_assignments','webhook_events']
for t in tables:
    cur.execute(f'TRUNCATE TABLE {t} CASCADE;')
print('OK')
cur.close()
conn.close()
"
```

---

## Diferencias Local vs Web

| Aspecto | Local (Docker) | Web (Railway/Vercel) |
|---|---|---|
| **URL frontend** | `http://localhost:5173` | `https://boleta-saas.vercel.app` |
| **URL backend** | `http://localhost:8000` | `https://boleta-saas-production.up.railway.app` |
| **Base de datos** | Docker PostgreSQL (`localhost:5432`) | Railway PostgreSQL (`tokaido.proxy.rlwy.net:45341`) |
| **Email registro** | SMTP directo (puerto 587) → llega al destinatario real | Resend trial → solo a `jn835513@gmail.com` |
| **Email boletas** | SMTP de la empresa (puerto 587) → llega al trabajador | SMTP de la empresa (puerto **465**) o Resend trial |
| **Super admin email** | `admin@sistema.com` (seed local) | `jn835513@gmail.com` |
| **Super admin password** | `123456` | `tLTEIxODb!p!d^X1` |
| **Puerto SMTP** | 587 (funciona) | 465 (el 587 está bloqueado) |
| **Adjuntar PDF** | Desde sistema de archivos local | Desde Supabase S3 |
| **Celery** | Worker local en Docker | Worker en Railway |
| **Redis** | Docker Redis (`localhost:6379`) | Upstash Redis (cloud) |
