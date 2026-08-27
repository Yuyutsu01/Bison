import pytest
from app.domains.backtesting.costs import IndianTransactionCostCalculator, CostModelConfig


def test_indian_transaction_cost_breakdown():
    # Buy 100 shares of RELIANCE at ₹2500 (Turnover = ₹2,50,000)
    buy_cost = IndianTransactionCostCalculator.calculate_cost("BUY", 100, 2500.0, CostModelConfig())

    assert buy_cost.brokerage <= 20.0  # Capped at ₹20
    assert buy_cost.stt == 0.0  # STT 0 on buy side for intraday
    assert buy_cost.stamp_duty > 0.0  # Stamp duty applies on buy
    assert buy_cost.executed_price_with_slippage > 2500.0  # Slippage increases buy price

    # Sell 100 shares of RELIANCE at ₹2550 (Turnover = ₹2,55,000)
    sell_cost = IndianTransactionCostCalculator.calculate_cost("SELL", 100, 2550.0, CostModelConfig())

    assert sell_cost.stt > 0.0  # STT applies on sell side
    assert sell_cost.stamp_duty == 0.0  # Stamp duty 0 on sell side
    assert sell_cost.executed_price_with_slippage < 2550.0  # Slippage lowers sell price
