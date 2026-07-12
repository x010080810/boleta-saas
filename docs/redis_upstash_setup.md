# Configurar Upstash Redis

1. Ve a https://console.upstash.com/ y crea una cuenta (GitHub/Google)
2. Haz clic en "Create Database"
3. Configura:
   - **Name**: `boleta-saas-redis`
   - **Region**: Same as Supabase (us-east-1 o sa-east-1)
   - **Tier**: Free
4. Haz clic en "Create"
5. En la página del database, copia el **UPSTASH_REDIS_URL** (ej: `rediss://default:XXXXX@XXXXX.upstash.io:6379`)
6. Agrega esa URL como `REDIS_URL` en Railway (para los 3 servicios: api, worker, beat)

> **Nota**: La URL usa `rediss://` (con TLS). El backend ya soporta TLS en celery_app.py.
