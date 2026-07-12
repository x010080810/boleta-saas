import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.database import init_db
from app.core.rate_limit import limiter
from app.routers import auth, companies, payroll, admin, templates, health


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        app.state.db_ready = True
    except Exception as e:
        logging.warning(f"Database initialization failed: {e}")
        app.state.db_ready = False
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(payroll.router, prefix="/api/companies/{company_id}/payroll", tags=["Payroll"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(health.router, prefix="/api", tags=["Health"])
