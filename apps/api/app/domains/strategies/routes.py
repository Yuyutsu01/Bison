"""
Strategy Management REST API Routes.

Handles strategy creation, visual validation, versioning, and retrieval.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import StrategyModel, StrategyVersionModel
from app.core.security import get_current_user_id
from app.domains.strategies.schemas import StrategyDSL
from app.domains.strategies.validator import StrategyValidator

router = APIRouter(prefix="/strategies", tags=["Strategies"])


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]


class StrategyResponse(BaseModel):
    id: str
    name: str
    description: str | None
    current_version: int
    created_at: str


class StrategyDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None
    current_version: int
    dsl: StrategyDSL


@router.post("/validate", response_model=ValidationResponse)
async def validate_strategy(dsl: StrategyDSL):
    errors = StrategyValidator.validate(dsl)
    return ValidationResponse(is_valid=len(errors) == 0, errors=errors)


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    dsl: StrategyDSL,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    errors = StrategyValidator.validate(dsl)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Strategy validation failed", "errors": errors})

    strategy = StrategyModel(
        user_id=user_id,
        name=dsl.name,
        description=dsl.description,
        current_version=1
    )
    db.add(strategy)
    await db.flush()

    version = StrategyVersionModel(
        strategy_id=strategy.id,
        version=1,
        dsl_json=dsl.model_dump()
    )
    db.add(version)
    await db.commit()
    await db.refresh(strategy)

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        current_version=strategy.current_version,
        created_at=strategy.created_at.isoformat()
    )


@router.get("", response_model=List[StrategyResponse])
async def list_strategies(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StrategyModel).where(StrategyModel.user_id == user_id).order_by(desc(StrategyModel.created_at))
    )
    strategies = result.scalars().all()
    return [
        StrategyResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            current_version=s.current_version,
            created_at=s.created_at.isoformat()
        )
        for s in strategies
    ]


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StrategyModel)
        .options(selectinload(StrategyModel.versions))
        .where(StrategyModel.id == strategy_id, StrategyModel.user_id == user_id)
    )
    strategy = result.scalars().first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    latest_version = max(strategy.versions, key=lambda v: v.version)
    return StrategyDetailResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        current_version=strategy.current_version,
        dsl=StrategyDSL(**latest_version.dsl_json)
    )


@router.post("/{strategy_id}/versions", response_model=StrategyDetailResponse)
async def create_strategy_version(
    strategy_id: str,
    dsl: StrategyDSL,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    errors = StrategyValidator.validate(dsl)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Strategy validation failed", "errors": errors})

    result = await db.execute(
        select(StrategyModel).where(StrategyModel.id == strategy_id, StrategyModel.user_id == user_id)
    )
    strategy = result.scalars().first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    new_version_num = strategy.current_version + 1
    strategy.current_version = new_version_num
    dsl.version = new_version_num

    version = StrategyVersionModel(
        strategy_id=strategy.id,
        version=new_version_num,
        dsl_json=dsl.model_dump()
    )
    db.add(version)
    await db.commit()

    return StrategyDetailResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        current_version=strategy.current_version,
        dsl=dsl
    )
