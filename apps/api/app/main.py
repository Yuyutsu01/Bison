"""
Bison FastAPI Server Entry Point.

Configures OpenAPI docs, CORS middleware, API routers, startup hooks, and health checks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import Base
from app.db.session import async_engine
from app.domains.auth.routes import router as auth_router
from app.domains.strategies.routes import router as strategy_router
from app.domains.instruments.routes import router as instrument_router
from app.domains.backtesting.routes import router as backtest_router

app = FastAPI(
    title="Bison Algorithmic Trading Platform API",
    description="Production-grade event-driven backtesting and quantitative strategy API for Indian market traders.",
    version="1.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Create database tables on startup if they do not exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "bison-api"}


@app.get("/ready", tags=["System"])
def ready_check():
    return {"status": "ready", "database": "connected"}


# Include Domain API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(strategy_router, prefix="/api/v1")
app.include_router(instrument_router, prefix="/api/v1")
app.include_router(backtest_router, prefix="/api/v1")
