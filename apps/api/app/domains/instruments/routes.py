"""
Instruments REST API Routes.

Provides Indian market instrument metadata (NSE/BSE indices and equities).
"""

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/instruments", tags=["Instruments"])


class InstrumentDTO(BaseModel):
    symbol: str
    name: str
    exchange: str = "NSE"
    lot_size: int = 1
    tick_size: float = 0.05
    timeframes: List[str] = ["1m", "5m", "15m", "1h", "1d"]


INDIAN_INSTRUMENTS = [
    InstrumentDTO(symbol="NIFTY", name="NIFTY 50 Index", exchange="NSE", lot_size=50),
    InstrumentDTO(symbol="BANKNIFTY", name="NIFTY Bank Index", exchange="NSE", lot_size=15),
    InstrumentDTO(symbol="FINNIFTY", name="NIFTY Financial Services", exchange="NSE", lot_size=40),
    InstrumentDTO(symbol="RELIANCE", name="Reliance Industries Ltd", exchange="NSE", lot_size=250),
    InstrumentDTO(symbol="TCS", name="Tata Consultancy Services", exchange="NSE", lot_size=175),
    InstrumentDTO(symbol="INFY", name="Infosys Limited", exchange="NSE", lot_size=400),
    InstrumentDTO(symbol="HDFCBANK", name="HDFC Bank Limited", exchange="NSE", lot_size=550),
    InstrumentDTO(symbol="ICICIBANK", name="ICICI Bank Limited", exchange="NSE", lot_size=700)
]


@router.get("", response_model=List[InstrumentDTO])
async def list_instruments():
    return INDIAN_INSTRUMENTS
