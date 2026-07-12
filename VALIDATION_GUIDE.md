# Guía de Validación — Flujo Completo

## Prerrequisitos

```bash
docker-compose up -d
# Esperar ~10s a que todos los servicios inicien
```

Si es la primera vez o se reseteó la base, ejecutar el seed (solo crea el Super Admin):
```bash
docker-compose exec backend python seed.py
```

Credenciales del Super Admin:
- **Email:** `admin@sistema.com`
- **Password:** `123456`

---

## Paso 1: Registrar una empresa desde la UI

1. Abrir [http://localhost:5173/register](http://localhost:5173/register)
2. Completar el formulario:

| Campo | Valor ejemplo |
|---|---|
| Empresa | `Mi Empresa S.A.C.` |
| RUC | `20123456789` |
| Nombre completo | `Juan Pérez` |
| Email | `juan@miempresa.com` |
| Contraseña | `123456` |

3. Click **"Registrar Empresa"**
4. ✅ Aparece pantalla **"¡Registro Exitoso!"**
5. ✅ Redirige automáticamente a `/login` tras 2 segundos

---

## Paso 2: Iniciar sesión como empresa nueva

1. En [http://localhost:5173/login](http://localhost:5173/login) ingresar:
   - **Email:** `juan@miempresa.com`
   - **Contraseña:** `123456`
2. ✅ Accede al dashboard con los datos del plan trial:
   - 50 envíos/mes
   - 30 días de vigencia
   - 90 días de gracia

---

## Paso 3: Configurar SMTP de la empresa

1. Ir a **"Configuración"** (menú lateral izquierdo, o [http://localhost:5173/settings](http://localhost:5173/settings))
2. En la sección **"Configuración SMTP"** llenar con credenciales reales:

| Campo | Ejemplo |
|---|---|
| Servidor SMTP | `smtp.gmail.com` |
| Puerto | `587` |
| Usuario SMTP | `tu_correo@gmail.com` |
| Contraseña SMTP | *(contraseña de aplicación de Gmail)* |
| Correo Remitente | `tu_correo@gmail.com` |
| Nombre Remitente | `Mi Empresa` |

3. Click **"Guardar Configuración"**
4. ✅ Mensaje verde **"Configuración guardada correctamente"**

> **Nota:** Sin SMTP configurado, los envíos de boletas fallarán. Las credenciales SMTP se guardan por empresa.

---

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

### Nota importante
Para recibir correos reales, se deben configurar las variables `SYSTEM_SMTP_*` en el archivo `backend/.env`:

```env
SYSTEM_SMTP_HOST=smtp.gmail.com
SYSTEM_SMTP_PORT=587
SYSTEM_SMTP_USER=tu_correo@gmail.com
SYSTEM_SMTP_PASSWORD=tu_contraseña_app
SYSTEM_SMTP_FROM_EMAIL=noreply@boletasaas.com
SYSTEM_SMTP_FROM_NAME=Boleta SaaS
```

Si no se configuran, el registro de empresas funciona igual pero los emails se omiten silenciosamente (tolerante a fallos).

### Flujos de email

| Evento | Remitente | Destinatario | Tipo |
|---|---|---|---|
| Registro de empresa | Sistema (`SYSTEM_SMTP`) | Admin de la empresa | Welcome email con detalles del plan trial |
| Registro de empresa | Sistema (`SYSTEM_SMTP`) | Super Admin (`admin@sistema.com`) | Notificación de nueva empresa registrada |

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

Para volver a estado inicial (solo Super Admin):

```bash
# Truncar todas las tablas
docker-compose exec db psql -U boleta_user -d boleta_saas -c "
TRUNCATE TABLE
  license_history, email_logs, monthly_send_quotas,
  pay_slips, unregistered_workers, payroll_uploads,
  employee_company_assignments, employees,
  user_company_assignments, company_users,
  companies, super_admins
RESTART IDENTITY CASCADE;
"

# Re-ejecutar seed
docker-compose exec backend python seed.py
```
