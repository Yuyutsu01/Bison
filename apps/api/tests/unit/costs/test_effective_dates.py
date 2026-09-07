"""
Unit tests for CostProfileResolver date matching and error handling.
"""

from decimal import Decimal
import pytest
from app.domains.costs.models import CostProfileVersion, AssetClass, BrokerageModel, CostProfileNotFoundError
from app.domains.costs.effective_date import CostProfileResolver


def test_effective_date_matching_within_range():
    """Timestamp falling squarely within version range should be resolved correctly."""
    v1 = CostProfileVersion(
        id="v1",
        profile_id="p1",
        version=1,
        name="Zerodha 2024",
        effective_from="2024-01-01T00:00:00",
        effective_to="2024-12-31T23:59:59",
        asset_class=AssetClass.EQUITY_INTRADAY,
        brokerage_model=BrokerageModel.PERCENTAGE_WITH_CAP,
        brokerage_rate=Decimal("0.0003"),
        brokerage_cap=Decimal("20.00"),
        brokerage_flat=Decimal("20.00"),
        stt_buy_rate=Decimal("0.00"),
        stt_sell_rate=Decimal("0.00025"),
        exchange_charge_rate=Decimal("0.0000345"),
        sebi_fee_rate=Decimal("0.000001"),
        stamp_duty_rate=Decimal("0.00003"),
        gst_rate=Decimal("0.18")
    )
    v2 = CostProfileVersion(
        id="v2",
        profile_id="p1",
        version=2,
        name="Zerodha 2025",
        effective_from="2025-01-01T00:00:00",
        effective_to="2099-12-31T23:59:59",
        asset_class=AssetClass.EQUITY_INTRADAY,
        brokerage_model=BrokerageModel.PERCENTAGE_WITH_CAP,
        brokerage_rate=Decimal("0.0003"),
        brokerage_cap=Decimal("20.00"),
        brokerage_flat=Decimal("20.00"),
        stt_buy_rate=Decimal("0.00"),
        stt_sell_rate=Decimal("0.00025"),
        exchange_charge_rate=Decimal("0.0000345"),
        sebi_fee_rate=Decimal("0.000001"),
        stamp_duty_rate=Decimal("0.00003"),
        gst_rate=Decimal("0.18")
    )

    res_2024 = CostProfileResolver.resolve_effective_profile("2024-06-15T10:00:00", [v1, v2])
    assert res_2024.id == "v1"

    res_2025 = CostProfileResolver.resolve_effective_profile("2025-03-01T14:30:00", [v1, v2])
    assert res_2025.id == "v2"


def test_effective_date_out_of_bounds_raises_error():
    """Empty list or non-matching date should raise CostProfileNotFoundError."""
    with pytest.raises(CostProfileNotFoundError):
        CostProfileResolver.resolve_effective_profile("2023-12-31T23:59:59", [])
