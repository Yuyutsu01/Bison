"""
Cost Engine REST API Routes.

Handles retrieval of cost profiles and cost profile versions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import CostProfileModel, CostProfileVersionModel
from app.core.security import get_current_user_id

router = APIRouter(prefix="/cost-profiles", tags=["Cost Profiles"])


class CostProfileVersionDTO(BaseModel):
    id: str
    version: int
    name: str
    effective_from: str
    effective_to: str
    asset_class: str
    brokerage_model: str
    brokerage_rate: float
    brokerage_cap: float
    brokerage_flat: float
    stt_buy_rate: float
    stt_sell_rate: float
    exchange_charge_rate: float
    sebi_fee_rate: float
    stamp_duty_rate: float
    gst_rate: float


class CostProfileDTO(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    asset_class: str
    versions: List[CostProfileVersionDTO] = []


@router.get("", response_model=List[CostProfileDTO])
async def list_cost_profiles(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all available transaction cost profiles."""
    result = await db.execute(
        select(CostProfileModel)
        .options(selectinload(CostProfileModel.versions))
    )
    profiles = result.scalars().all()
    return [
        CostProfileDTO(
            id=p.id,
            name=p.name,
            description=p.description,
            asset_class=p.asset_class,
            versions=[
                CostProfileVersionDTO(
                    id=v.id,
                    version=v.version,
                    name=v.name,
                    effective_from=v.effective_from,
                    effective_to=v.effective_to,
                    asset_class=v.asset_class,
                    brokerage_model=v.brokerage_model,
                    brokerage_rate=v.brokerage_rate,
                    brokerage_cap=v.brokerage_cap,
                    brokerage_flat=v.brokerage_flat,
                    stt_buy_rate=v.stt_buy_rate,
                    stt_sell_rate=v.stt_sell_rate,
                    exchange_charge_rate=v.exchange_charge_rate,
                    sebi_fee_rate=v.sebi_fee_rate,
                    stamp_duty_rate=v.stamp_duty_rate,
                    gst_rate=v.gst_rate
                )
                for v in p.versions
            ]
        )
        for p in profiles
    ]


@router.get("/{profile_id}", response_model=CostProfileDTO)
async def get_cost_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific transaction cost profile."""
    result = await db.execute(
        select(CostProfileModel)
        .options(selectinload(CostProfileModel.versions))
        .where(CostProfileModel.id == profile_id)
    )
    p = result.scalars().first()
    if not p:
        raise HTTPException(status_code=404, detail="Cost profile not found.")

    return CostProfileDTO(
        id=p.id,
        name=p.name,
        description=p.description,
        asset_class=p.asset_class,
        versions=[
            CostProfileVersionDTO(
                id=v.id,
                version=v.version,
                name=v.name,
                effective_from=v.effective_from,
                effective_to=v.effective_to,
                asset_class=v.asset_class,
                brokerage_model=v.brokerage_model,
                brokerage_rate=v.brokerage_rate,
                brokerage_cap=v.brokerage_cap,
                brokerage_flat=v.brokerage_flat,
                stt_buy_rate=v.stt_buy_rate,
                stt_sell_rate=v.stt_sell_rate,
                exchange_charge_rate=v.exchange_charge_rate,
                sebi_fee_rate=v.sebi_fee_rate,
                stamp_duty_rate=v.stamp_duty_rate,
                gst_rate=v.gst_rate
            )
            for v in p.versions
        ]
    )
