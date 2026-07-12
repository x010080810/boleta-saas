import asyncio, asyncpg
from urllib.parse import urlparse

url = "postgresql://postgres:RgqsoMkfPQrnuVJquvpxMwVhPuiIaaEm@tokaido.proxy.rlwy.net:45341/railway"
parsed = urlparse(url)
user = parsed.username
pw = parsed.password
host = parsed.hostname
port = parsed.port
db = parsed.path.lstrip("/")

async def check():
    conn = await asyncpg.connect(user=user, password=pw, host=host, port=port, database=db)

    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
    )
    print("=== TABLAS ===")
    for t in tables:
        row = await conn.fetchrow(f'SELECT COUNT(*) as cnt FROM "{t["table_name"]}"')
        print(f'  {t["table_name"]}: {row["cnt"]} registros')

    admin = await conn.fetch("SELECT id, email, full_name, is_active FROM super_admins")
    print("\n=== SUPER ADMINS ===")
    for a in admin:
        print(f'  {a["email"]} | active={a["is_active"]}')

    companies = await conn.fetch("SELECT id, name, ruc, is_active FROM companies")
    print("\n=== EMPRESAS ===")
    for c in companies:
        print(f'  {c["name"]} ({c["ruc"]}) | active={c["is_active"]}')

    await conn.close()

asyncio.run(check())
print("\nOK - Railway PostgreSQL conectado")
