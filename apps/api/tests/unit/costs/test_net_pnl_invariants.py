"""
Unit tests verifying Net PnL invariants and Portfolio cash deduction accounting.
"""

from decimal import Decimal
import pytest
from app.domains.costs.models import CostProfileVersion, AssetClass, BrokerageModel, TransactionCostBreakdown
from app.domains.costs.engine import TransactionCostEngine
from app.domains.portfolio.service import PortfolioService
from app.domains.portfolio.models import Portfolio
from app.domains.execution.models import Execution


def test_transaction_cost_breakdown_total_sum():
    """Verify total_cost is strictly the exact sum of all cost components."""
    v1 = CostProfileVersion(
        id="v1",
        profile_id="p1",
        version=1,
        name="Zerodha Standard",
        effective_from="2020-01-01T00:00:00",
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
        id="ex-1",
        order_id="ord-1",
        instrument_id="inst-1",
        symbol="RELIANCE",
        timestamp="2025-01-10T10:00:00",
        side="BUY",
        quantity=Decimal("100"),
        reference_price=Decimal("500.00"),
        execution_price=Decimal("500.00"),
        slippage=Decimal("0.0")
    )

    breakdown_buy = TransactionCostEngine.calculate_cost_breakdown(execution, v1)

    sum_components = (
        breakdown_buy.brokerage +
        breakdown_buy.stt +
        breakdown_buy.exchange_charges +
        breakdown_buy.sebi_fees +
        breakdown_buy.stamp_duty +
        breakdown_buy.gst +
        breakdown_buy.other_charges
    )

    assert breakdown_buy.total_cost == sum_components


def test_portfolio_net_cash_accounting_with_costs():
    """Verify portfolio cash & realized PnL correctly deduct total costs.

    Buy 100 shares @ ₹100. Total cost = ₹10.00.
    Sell 100 shares @ ₹110. Total cost = ₹12.00.
    Gross PnL = (110 - 100) * 100 = ₹1,000.00.
    Total Costs = ₹10.00 + ₹12.00 = ₹22.00.
    Net PnL = ₹1,000.00 - ₹22.00 = ₹978.00.
    """
    portfolio = Portfolio(
        id="port-1",
        backtest_run_id="run-1",
        initial_capital=Decimal("100000.00"),
        cash=Decimal("100000.00"),
        equity=Decimal("100000.00")
    )
    service = PortfolioService(portfolio)

    ex_buy = Execution(
        id="ex-buy",
        order_id="ord-1",
        instrument_id="inst-1",
        symbol="RELIANCE",
        timestamp="2025-01-10T10:00:00",
        side="BUY",
        quantity=Decimal("100"),
        reference_price=Decimal("100.00"),
        execution_price=Decimal("100.00"),
        slippage=Decimal("0.0")
    )
    cost_buy = TransactionCostBreakdown(
        id="cb-1",
        execution_id="ex-buy",
        cost_profile_version_id="v1",
        turnover=Decimal("10000.00"),
        brokerage=Decimal("3.00"),
        stt=Decimal("0.00"),
        exchange_charges=Decimal("0.35"),
        sebi_fees=Decimal("0.01"),
        stamp_duty=Decimal("0.30"),
        gst=Decimal("0.60"),
        other_charges=Decimal("5.74"),
        total_cost=Decimal("10.00")
    )

    # Process BUY execution
    service.apply_execution(ex_buy, cost_buy)

    # Cash should be initial (100,000) - cost_outflow (10,000) - transaction_cost (10) = 89,990.00
    assert portfolio.cash == Decimal("89990.00")

    ex_sell = Execution(
        id="ex-sell",
        order_id="ord-2",
        instrument_id="inst-1",
        symbol="RELIANCE",
        timestamp="2025-01-10T11:00:00",
        side="SELL",
        quantity=Decimal("100"),
        reference_price=Decimal("110.00"),
        execution_price=Decimal("110.00"),
        slippage=Decimal("0.0")
    )
    cost_sell = TransactionCostBreakdown(
        id="cb-2",
        execution_id="ex-sell",
        cost_profile_version_id="v1",
        turnover=Decimal("11000.00"),
        brokerage=Decimal("3.30"),
        stt=Decimal("2.75"),
        exchange_charges=Decimal("0.38"),
        sebi_fees=Decimal("0.01"),
        stamp_duty=Decimal("0.00"),
        gst=Decimal("0.66"),
        other_charges=Decimal("4.90"),
        total_cost=Decimal("12.00")
    )

    # Process SELL execution
    service.apply_execution(ex_sell, cost_sell)

    # Cash should be 89,990 + cost_inflow (11,000) - transaction_cost (12) = 100,978.00
    assert portfolio.cash == Decimal("100978.00")
    assert portfolio.cash - portfolio.initial_capital == Decimal("978.00")
