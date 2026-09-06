"""
Risk Management Engine.

Evaluates position risk rules (Stop-Loss, Target, Trailing Stop, Max Holding, EOD Exit, Max Positions)
against market price bars. Enforces conservative Intrabar Conflict Policy and Gap Execution.
Emits exit instructions; NEVER mutates positions directly.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple

from app.domains.strategies.schemas import RiskManagement
from app.domains.portfolio.models import Portfolio, Position, PositionSide
from app.domains.risk.models import RiskDecision, RiskEventType, RiskEvent


class RiskEngine:
    """Evaluates risk controls and generates deterministic exit decisions."""

    @staticmethod
    def evaluate_entry_risk(
        portfolio: Portfolio,
        max_simultaneous_positions: Optional[int] = None
    ) -> RiskDecision:
        """
        Evaluates risk controls for a new entry signal.

        Important Logic:
        - Rejects entry if open positions count >= max_simultaneous_positions.
        """
        if max_simultaneous_positions is not None and max_simultaneous_positions > 0:
            open_count = len([p for p in portfolio.positions.values() if p.status == "OPEN"])
            if open_count >= max_simultaneous_positions:
                return RiskDecision(
                    allowed=False,
                    action="REJECT_ENTRY",
                    reason="MAX_POSITIONS_REACHED"
                )
        return RiskDecision(allowed=True, action="ALLOW_ENTRY")

    @staticmethod
    def evaluate_position_risk(
        portfolio: Portfolio,
        position: Position,
        bar: Dict[str, Any],
        risk_config: RiskManagement,
        is_final_bar: bool = False
    ) -> Optional[RiskEvent]:
        """
        Evaluates active position against risk rules during a price bar.

        Important Logic:
        1. Intrabar Conflict Policy: If both Stop-Loss and Target are touched in the same bar,
           the conservative policy assumes the adverse event (Stop-Loss) occurred first.
        2. Gap Execution: If market opens beyond a Stop-Loss threshold (e.g. Open < SL price),
           the trigger price is bar Open (the next available executable price).
        3. Trailing Stop: Tracks highest price since entry and moves stop level strictly in favorable direction.
        4. Exits generate a RiskEvent; actual position mutation happens only after simulated Execution fill.
        """
        timestamp = str(bar.get("timestamp", position.last_updated_at))
        bar_open = Decimal(str(bar.get("open", position.current_price)))
        bar_high = Decimal(str(bar.get("high", position.current_price)))
        bar_low = Decimal(str(bar.get("low", position.current_price)))
        bar_close = Decimal(str(bar.get("close", position.current_price)))

        entry_price = position.average_entry_price

        # Update high/low trailing trackers
        if position.side == PositionSide.LONG:
            if position.highest_price_since_entry is None or bar_high > position.highest_price_since_entry:
                position.highest_price_since_entry = bar_high
        else:
            if position.lowest_price_since_entry is None or bar_low < position.lowest_price_since_entry:
                position.lowest_price_since_entry = bar_low

        sl_triggered = False
        sl_trigger_price = bar_close
        target_triggered = False
        target_trigger_price = bar_close

        # 1. Stop-loss check
        if risk_config.stop_loss_percent is not None:
            sl_pct = Decimal(str(risk_config.stop_loss_percent)) / Decimal("100.0")
            if position.side == PositionSide.LONG:
                sl_level = entry_price * (Decimal("1.0") - sl_pct)
                if bar_low <= sl_level:
                    sl_triggered = True
                    # Gap handling: if Open < sl_level, fill at Open
                    sl_trigger_price = min(bar_open, sl_level) if bar_open < sl_level else sl_level
            else:
                sl_level = entry_price * (Decimal("1.0") + sl_pct)
                if bar_high >= sl_level:
                    sl_triggered = True
                    sl_trigger_price = max(bar_open, sl_level) if bar_open > sl_level else sl_level

        # 2. Target check
        if risk_config.target_percent is not None:
            target_pct = Decimal(str(risk_config.target_percent)) / Decimal("100.0")
            if position.side == PositionSide.LONG:
                target_level = entry_price * (Decimal("1.0") + target_pct)
                if bar_high >= target_level:
                    target_triggered = True
                    target_trigger_price = max(bar_open, target_level) if bar_open > target_level else target_level
            else:
                target_level = entry_price * (Decimal("1.0") - target_pct)
                if bar_low <= target_level:
                    target_triggered = True
                    target_trigger_price = min(bar_open, target_level) if bar_open < target_level else target_level

        # Intrabar Conflict Policy: Conservative assumption -> Adverse event (Stop-Loss) wins
        if sl_triggered and target_triggered:
            event_id = f"RSK_{uuid.uuid4().hex[:12]}"
            return RiskEvent(
                id=event_id,
                portfolio_id=portfolio.id,
                position_id=position.id,
                symbol=position.symbol,
                event_type=RiskEventType.STOP_LOSS_TRIGGERED,
                timestamp=timestamp,
                trigger_price=sl_trigger_price,
                reason="INTRABAR_CONFLICT_CONSERVATIVE_STOP_LOSS",
                metadata={"intrabar_conflict": True, "target_also_touched": True}
            )

        if sl_triggered:
            event_id = f"RSK_{uuid.uuid4().hex[:12]}"
            return RiskEvent(
                id=event_id,
                portfolio_id=portfolio.id,
                position_id=position.id,
                symbol=position.symbol,
                event_type=RiskEventType.STOP_LOSS_TRIGGERED,
                timestamp=timestamp,
                trigger_price=sl_trigger_price,
                reason="STOP_LOSS_BREACHED"
            )

        if target_triggered:
            event_id = f"RSK_{uuid.uuid4().hex[:12]}"
            return RiskEvent(
                id=event_id,
                portfolio_id=portfolio.id,
                position_id=position.id,
                symbol=position.symbol,
                event_type=RiskEventType.TARGET_TRIGGERED,
                timestamp=timestamp,
                trigger_price=target_trigger_price,
                reason="TARGET_REACHED"
            )

        # 3. Trailing Stop check
        if risk_config.trailing_stop_percent is not None:
            trail_pct = Decimal(str(risk_config.trailing_stop_percent)) / Decimal("100.0")
            if position.side == PositionSide.LONG and position.highest_price_since_entry is not None:
                trail_stop_level = position.highest_price_since_entry * (Decimal("1.0") - trail_pct)
                if bar_low <= trail_stop_level:
                    event_id = f"RSK_{uuid.uuid4().hex[:12]}"
                    return RiskEvent(
                        id=event_id,
                        portfolio_id=portfolio.id,
                        position_id=position.id,
                        symbol=position.symbol,
                        event_type=RiskEventType.TRAILING_STOP_TRIGGERED,
                        timestamp=timestamp,
                        trigger_price=trail_stop_level,
                        reason="TRAILING_STOP_BREACHED"
                    )

        # 4. Max Holding Period check
        if risk_config.max_holding_bars is not None:
            if position.holding_bars >= risk_config.max_holding_bars:
                event_id = f"RSK_{uuid.uuid4().hex[:12]}"
                return RiskEvent(
                    id=event_id,
                    portfolio_id=portfolio.id,
                    position_id=position.id,
                    symbol=position.symbol,
                    event_type=RiskEventType.MAX_HOLDING_TRIGGERED,
                    timestamp=timestamp,
                    trigger_price=bar_close,
                    reason="MAX_HOLDING_BARS_EXCEEDED"
                )

        # 5. End of Day Exit check
        if risk_config.end_of_day_exit and is_final_bar:
            event_id = f"RSK_{uuid.uuid4().hex[:12]}"
            return RiskEvent(
                id=event_id,
                portfolio_id=portfolio.id,
                position_id=position.id,
                symbol=position.symbol,
                event_type=RiskEventType.EOD_EXIT_TRIGGERED,
                timestamp=timestamp,
                trigger_price=bar_close,
                reason="END_OF_DAY_EXIT"
            )

        return None
