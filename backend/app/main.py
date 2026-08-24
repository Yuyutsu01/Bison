"""
FastAPI Server Entry Point.

Provides REST API routes for Algorithmic Trading Platform Phase 1 backend.
Enables CORS for Next.js frontend communication.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.data.sample_data import ensure_sample_data_dir

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to initialize sample data on startup."""
    logger.info("Initializing Algorithmic Trading Core Backend...")
    ensure_sample_data_dir("data")
    logger.info("Sample market datasets (AAPL, MSFT, SPY) initialized successfully.")
    yield
    logger.info("Shutting down backend services.")


app = FastAPI(
    title="Algorithmic Trading Platform Engine",
    description="Event-Driven Core & Backtesting REST API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from Next.js dev server & Docker containers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router under /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check():
    """Service health check endpoint."""
    return {"status": "HEALTHY", "engine": "Event-Driven Backtester v1.0"}
