import os, subprocess
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import select
from app.core.celery_app import celery_app
from app.core.database import sync_session_factory
from app.models.company import Company
from app.models.license import LicenseHistory
from app.models.quota import MonthlySendQuota
from app.services.email_sender import send_license_expiry_warning
from app.core.config import settings


@celery_app.task
def check_expiring_licenses():
    db = sync_session_factory()
    try:
        target = date.today() + timedelta(days=15)
        companies = db.execute(
            select(Company).where(
                Company.licencia_fin == target,
                Company.notificado_15_dias == False,
                Company.is_active == True,
            )
        ).scalars().all()

        for company in companies:
            try:
                if not company.smtp_host or not company.smtp_user or not company.smtp_password:
                    continue
                send_license_expiry_warning(
                    smtp_host=company.smtp_host,
                    smtp_port=company.smtp_port,
                    smtp_user=company.smtp_user,
                    smtp_password=company.smtp_password,
                    from_email=company.smtp_from_email,
                    from_name=company.smtp_from_name,
                    to_email=company.smtp_from_email,
                    empresa=company.name,
                    ruc=company.ruc,
                    plan=company.plan_envios_mes,
                    fin=str(company.licencia_fin),
                    dias=15,
                    admin_name=company.smtp_from_name or "Administrador",
                )
                company.notificado_15_dias = True
            except Exception as e:
                print(f"Error notifying {company.name}: {e}")

        db.commit()
    finally:
        db.close()


@celery_app.task
def update_license_states():
    db = sync_session_factory()
    try:
        now = date.today()

        # activa → vencida
        companies = db.execute(
            select(Company).where(
                Company.licencia_fin < now,
                Company.licencia_estado == "activa",
            )
        ).scalars().all()
        for company in companies:
            company.licencia_estado = "vencida"
            db.add(LicenseHistory(
                company_id=company.id,
                tipo="vencimiento",
                notas=f"Licencia vencida automáticamente el {now}",
            ))

        # vencida → grace_period (still within grace window)
        companies = db.execute(
            select(Company).where(
                Company.licencia_grace_hasta >= now,
                Company.licencia_estado == "vencida",
            )
        ).scalars().all()
        for company in companies:
            company.licencia_estado = "grace_period"

        # vencida/grace_period → baja (grace window expired)
        companies = db.execute(
            select(Company).where(
                Company.licencia_grace_hasta < now,
                Company.licencia_estado.in_(["vencida", "grace_period"]),
            )
        ).scalars().all()
        for company in companies:
            company.licencia_estado = "baja"
            company.is_active = False
            db.add(LicenseHistory(
                company_id=company.id,
                tipo="baja",
                notas=f"Empresa dada de baja por licencia vencida el {now}",
            ))

        # activa → por_vencer (within 15 days of expiry)
        companies = db.execute(
            select(Company).where(
                Company.licencia_fin >= now,
                Company.licencia_fin <= now + timedelta(days=15),
                Company.licencia_estado == "activa",
            )
        ).scalars().all()
        for company in companies:
            company.licencia_estado = "por_vencer"

        db.commit()
    finally:
        db.close()


@celery_app.task
def backup_database():
    backup_dir = settings.BACKUP_DIR
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql.gz"
    filepath = os.path.join(backup_dir, filename)

    parts = settings.DATABASE_URL_SYNC.replace("postgresql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")
    host_port = host_db[0].split(":")

    env = os.environ.copy()
    env["PGPASSWORD"] = user_pass[1]

    cmd = [
        "pg_dump",
        "-h", host_port[0],
        "-p", host_port[1] if len(host_port) > 1 else "5432",
        "-U", user_pass[0],
        "-d", host_db[1],
        "--no-owner",
        "--no-acl",
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        import gzip
        with gzip.open(filepath, "wb") as gz:
            for chunk in iter(lambda: proc.stdout.read(65536), b""):
                gz.write(chunk)
        proc.wait()

        if proc.returncode == 0:
            print(f"Backup created: {filepath} ({os.path.getsize(filepath)} bytes)")
        else:
            stderr = proc.stderr.read().decode()
            print(f"Backup failed: {stderr}")
    except Exception as e:
        print(f"Backup error: {e}")
