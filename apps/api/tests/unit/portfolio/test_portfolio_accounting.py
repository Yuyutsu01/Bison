"""
Unit Tests for Portfolio Accounting, Average Entry Price, and Realized/Unrealized P&L.
"""

import pytest
from decimal import Decimal
from app.domains.execution.models import Execution, ExecutionStatus
from app.domains.portfolio.models import Portfolio, PositionSide, PositionStatus
from app.domains.portfolio.service import PortfolioService


def test_portfolio_initialization():
    portfolio = Portfolio(
        id="PORT_1",
        backtest_run_id="B1",
        initial_capital=Decimal("100000.0"),
        cash=Decimal("100000.0"),
        equity=Decimal("100000.0")
    )
    assert portfolio.cash == Decimal("100000.0")
    assert portfolio.equity == Decimal("100000.0")
    assert portfolio.realized_pnl == Decimal("0.0")
    assert portfolio.unrealized_pnl == Decimal("0.0")


def test_apply_long_execution_and_weighted_average_entry():
    portfolio = Portfolio(
        id="PORT_2",
        backtest_run_id="B2",
        initial_capital=Decimal("100000.0"),
        cash=Decimal("100000.0"),
        equity=Decimal("100000.0")
    )
    service = PortfolioService(portfolio)

    # 1. First Buy: 10 @ ₹100
    exec1 = Execution(
        id="EXEC_1",
        order_id="ORD_1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        timestamp="10:05",
        side="BUY",
        quantity=Decimal("10"),
        reference_price=Decimal("100.0"),
        execution_price=Decimal("100.0"),
        slippage=Decimal("0.0")
    )
    service.apply_execution(exec1)

    pos = portfolio.positions["NIFTY"]
    assert pos.quantity == Decimal("10")
    assert pos.average_entry_price == Decimal("100.0")
    assert portfolio.cash == Decimal("99000.0")

    # 2. Second Buy: 10 @ ₹120 -> Average price = (10*100 + 10*120)/20 = ₹110
    exec2 = Execution(
        id="EXEC_2",
        order_id="ORD_2",
        instrument_id="NIFTY",
        symbol="NIFTY",
        timestamp="10:10",
        side="BUY",
        quantity=Decimal("10"),
        reference_price=Decimal("120.0"),
        execution_price=Decimal("120.0"),
        slippage=Decimal("0.0")
    )
    service.apply_execution(exec2)

    pos = portfolio.positions["NIFTY"]
    assert pos.quantity == Decimal("20")
    assert pos.average_entry_price == Decimal("110.0")
    assert portfolio.cash == Decimal("97800.0")


def test_long_exit_realized_pnl():
    portfolio = Portfolio(
        id="PORT_3",
        backtest_run_id="B3",
        initial_capital=Decimal("100000.0"),
        cash=Decimal("100000.0"),
        equity=Decimal("100000.0")
    )
    service = PortfolioService(portfolio)

    # Buy 50 @ ₹24,000
    exec_buy = Execution(
        id="EXEC_B1",
        order_id="ORD_B1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        timestamp="10:05",
        side="BUY",
        quantity=Decimal("50"),
        reference_price=Decimal("24000.0"),
        execution_price=Decimal("24000.0"),
        slippage=Decimal("0.0")
    )
    service.apply_execution(exec_buy)

    # Sell 50 @ ₹24,150 -> Realized PnL = (24150 - 24000) * 50 = ₹7,500
    exec_sell = Execution(
        id="EXEC_S1",
        order_id="ORD_S1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        timestamp="10:15",
        side="SELL",
        quantity=Decimal("50"),
        reference_price=Decimal("24150.0"),
        execution_price=Decimal("24150.0"),
        slippage=Decimal("0.0")
    )
    service.apply_execution(exec_sell)

    assert portfolio.realized_pnl == Decimal("7500.0")
    assert portfolio.cash == Decimal("107500.0")
    assert "NIFTY" not in portfolio.positions


def test_idempotent_execution_application():
    portfolio = Portfolio(
        id="PORT_4",
        backtest_run_id="B4",
        initial_capital=Decimal("100000.0"),
        cash=Decimal("100000.0"),
        equity=Decimal("100000.0")
    )
    service = PortfolioService(portfolio)

    exec_buy = Execution(
        id="EXEC_DUP",
        order_id="ORD_DUP",
        instrument_id="NIFTY",
        symbol="NIFTY",
        timestamp="10:05",
        side="BUY",
        quantity=Decimal("50"),
        reference_price=Decimal("24000.0"),
        execution_price=Decimal("24000.0"),
        slippage=Decimal("0.0")
    )
    service.apply_execution(exec_buy)
    cash_after_first = portfolio.cash

    # Re-apply exact same execution ID
    service.apply_execution(exec_buy)
    assert portfolio.cash == cash_after_first
    assert portfolio.positions["NIFTY"].quantity == Decimal("50")
