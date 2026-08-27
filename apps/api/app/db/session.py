"""
Database Session Management.

Provides async & sync SQLAlchemy database engines, session factories, and FastAPI dependencies.
Defaults to an in-memory SQLite database if PostgreSQL URL is unavailable during standalone testing.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./bison.db"
)

# Convert postgresql:// to postgresql+asyncpg:// if necessary
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Async Engine for FastAPI
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Async DB Dependency."""
    async with AsyncSessionLocal() as session:
        yield session
