"""
Unit tests verifying determinism and reproducibility of TransactionCostEngine calculations.
"""

from decimal import Decimal
from app.domains.costs.models import CostProfileVersion, AssetClass, BrokerageModel
from app.domains.costs.engine import TransactionCostEngine
from app.domains.execution.models import Execution


def test_transaction_cost_engine_reproducibility():
    """Identical execution parameters across multiple engine invocations must produce bit-exact identical cost breakdowns."""
    v1 = CostProfileVersion(
        id="v1",
        profile_id="p1",
        version=1,
        name="Zerodha 2025",
        effective_from="2024-01-01T00:00:00",
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

    execution = Execution(
        id="ex-100",
        order_id="ord-100",
        instrument_id="inst-1",
        symbol="RELIANCE",
        timestamp="2025-05-20T11:15:00",
        side="SELL",
        quantity=Decimal("500"),
        reference_price=Decimal("1250.75"),
        execution_price=Decimal("1250.75"),
        slippage=Decimal("0.0")
    )

    res1 = TransactionCostEngine.calculate_cost_breakdown(execution, v1)
    res2 = TransactionCostEngine.calculate_cost_breakdown(execution, v1)

    assert res1.turnover == res2.turnover
    assert res1.brokerage == res2.brokerage
    assert res1.stt == res2.stt
    assert res1.exchange_charges == res2.exchange_charges
    assert res1.sebi_fees == res2.sebi_fees
    assert res1.stamp_duty == res2.stamp_duty
    assert res1.gst == res2.gst
    assert res1.total_cost == res2.total_cost
