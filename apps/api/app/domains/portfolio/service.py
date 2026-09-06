"""
Portfolio Accounting Service.

Applies Execution fills to Portfolio state, maintains average entry pricing,
computes realized/unrealized P&L, and performs bar-by-bar mark-to-market revaluation.
"""

import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, List

from app.domains.execution.models import Execution
from app.domains.orders.models import OrderSide
from app.domains.portfolio.models import (
    Portfolio,
    Position,
    PositionSide,
    PositionStatus,
    PortfolioSnapshot
)


class PortfolioService:
    """Core application & domain service managing Portfolio financial accounting."""

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def apply_execution(self, execution: Execution) -> None:
        """
        Applies a simulated Execution fill to the Portfolio.

        Important Logic:
        1. Idempotency Protection: Ignores execution if execution.id has already been processed.
        2. Execution Source of Truth: Only Executions modify cash, position quantity, or average entry price.
        3. Long/Short Entry & Exit Accounting:
           - Entry increases position size and recalculates weighted average entry price.
           - Exit calculates realized P&L = (Exit Price - Entry Price) * Quantity for Longs.
           - Increases cash upon sell and updates portfolio realized P&L.
        """
        if execution.id in self.portfolio.processed_execution_ids:
            return  # Idempotent guard: already applied

        self.portfolio.processed_execution_ids.add(execution.id)

        symbol = execution.symbol
        exec_side = execution.side
        exec_qty = execution.quantity
        exec_price = execution.execution_price
        timestamp = execution.timestamp

        existing_pos = self.portfolio.positions.get(symbol)

        # Check if execution is a BUY / Long Entry / Short Exit
        is_buy_intent = exec_side in ("BUY", "LONG_ENTRY", OrderSide.BUY.value, OrderSide.LONG_ENTRY.value)
        is_sell_intent = exec_side in ("SELL", "LONG_EXIT", OrderSide.SELL.value, OrderSide.LONG_EXIT.value)

        if is_buy_intent:
            if existing_pos is None or existing_pos.status == PositionStatus.CLOSED:
                # Open new LONG position
                pos_id = f"POS_{uuid.uuid4().hex[:12]}"
                new_pos = Position(
                    id=pos_id,
                    portfolio_id=self.portfolio.id,
                    instrument_id=execution.instrument_id,
                    symbol=symbol,
                    side=PositionSide.LONG,
                    quantity=exec_qty,
                    average_entry_price=exec_price,
                    current_price=exec_price,
                    opened_at=timestamp,
                    last_updated_at=timestamp
                )
                self.portfolio.positions[symbol] = new_pos
                self.portfolio.cash -= (exec_qty * exec_price)
            elif existing_pos.side == PositionSide.LONG:
                # Add to existing LONG position (Weighted Average Entry Price)
                total_cost = (existing_pos.quantity * existing_pos.average_entry_price) + (exec_qty * exec_price)
                new_qty = existing_pos.quantity + exec_qty
                existing_pos.average_entry_price = total_cost / new_qty
                existing_pos.quantity = new_qty
                existing_pos.last_updated_at = timestamp
                self.portfolio.cash -= (exec_qty * exec_price)
            elif existing_pos.side == PositionSide.SHORT:
                # Close/Reduce existing SHORT position
                closed_qty = min(existing_pos.quantity, exec_qty)
                realized_pnl = (existing_pos.average_entry_price - exec_price) * closed_qty

                existing_pos.realized_pnl += realized_pnl
                self.portfolio.realized_pnl += realized_pnl
                self.portfolio.cash += (closed_qty * existing_pos.average_entry_price) + realized_pnl

                if exec_qty >= existing_pos.quantity:
                    existing_pos.status = PositionStatus.CLOSED
                    del self.portfolio.positions[symbol]
                else:
                    existing_pos.quantity -= exec_qty
                    existing_pos.last_updated_at = timestamp

        elif is_sell_intent:
            if existing_pos is not None and existing_pos.side == PositionSide.LONG:
                # Close/Reduce existing LONG position
                closed_qty = min(existing_pos.quantity, exec_qty)
                realized_pnl = (exec_price - existing_pos.average_entry_price) * closed_qty

                existing_pos.realized_pnl += realized_pnl
                self.portfolio.realized_pnl += realized_pnl
                self.portfolio.cash += (closed_qty * exec_price)

                if exec_qty >= existing_pos.quantity:
                    existing_pos.status = PositionStatus.CLOSED
                    del self.portfolio.positions[symbol]
                else:
                    existing_pos.quantity -= exec_qty
                    existing_pos.last_updated_at = timestamp

    def mark_to_market(self, bar_dict: Dict[str, Any], timestamp: str) -> PortfolioSnapshot:
        """
        Performs bar-by-bar mark-to-market portfolio revaluation.

        Important Logic:
        - Updates open position current market price to bar_close.
        - Recalculates unrealized P&L, gross exposure, net exposure, and equity.
        - Equity = Cash + Position Market Value.
        - Generates a PortfolioSnapshot.
        """
        bar_close_raw = bar_dict.get("close")
        if bar_close_raw is not None:
            bar_close = Decimal(str(bar_close_raw))
            symbol = bar_dict.get("symbol")
            if symbol and symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                pos.update_market_price(bar_close)
                pos.holding_bars += 1

        unrealized_sum = Decimal("0.0")
        gross_exp = Decimal("0.0")
        net_exp = Decimal("0.0")

        for pos in self.portfolio.positions.values():
            if pos.status == PositionStatus.OPEN:
                unrealized_sum += pos.unrealized_pnl
                mkt_val = pos.market_value
                gross_exp += mkt_val
                if pos.side == PositionSide.LONG:
                    net_exp += mkt_val
                else:
                    net_exp -= mkt_val

        self.portfolio.unrealized_pnl = unrealized_sum
        self.portfolio.gross_exposure = gross_exp
        self.portfolio.net_exposure = net_exp
        self.portfolio.equity = self.portfolio.cash + gross_exp
        self.portfolio.total_pnl = self.portfolio.realized_pnl + self.portfolio.unrealized_pnl

        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            cash=self.portfolio.cash,
            equity=self.portfolio.equity,
            gross_exposure=self.portfolio.gross_exposure,
            net_exposure=self.portfolio.net_exposure,
            realized_pnl=self.portfolio.realized_pnl,
            unrealized_pnl=self.portfolio.unrealized_pnl,
            total_pnl=self.portfolio.total_pnl,
            open_position_count=len(self.portfolio.positions)
        )
        return snapshot
