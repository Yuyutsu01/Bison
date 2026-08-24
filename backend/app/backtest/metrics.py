"""
Quantitative Performance Analytics Engine.

Calculates key trading metrics:
- Total Return (%)
- Annualized Return (%)
- Sharpe Ratio (annualized, assuming risk-free rate = 0%)
- Max Drawdown (%)
- Win Rate (%)
- Profit Factor
- Total Trade Count
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd

from app.backtest.portfolio import TradeRecord


class PerformanceMetrics:
    """Computes financial statistics from equity curve time-series and trade logs."""

    @staticmethod
    def calculate(equity_curve: List[Dict[str, Any]], trades: List[TradeRecord], initial_capital: float) -> Dict[str, Any]:
        if not equity_curve:
            return {
                "total_return_pct": 0.0,
                "annualized_return_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "win_rate_pct": 0.0,
                "total_trades": 0,
                "profit_factor": 0.0,
                "winning_trades": 0,
                "losing_trades": 0
            }

        df_equity = pd.DataFrame(equity_curve)
        equities = df_equity["equity"].values
        final_equity = equities[-1]

        # 1. Total Return (%)
        total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0

        # 2. Daily Returns & Sharpe Ratio
        # Compute percentage change between consecutive equity snapshots
        returns = pd.Series(equities).pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            # Assuming daily frequency (252 trading days per year)
            sharpe_ratio = float((returns.mean() / returns.std()) * np.sqrt(252))
        else:
            sharpe_ratio = 0.0

        # 3. Maximum Drawdown (%)
        # Peak-to-trough decline of portfolio value
        cum_max = np.maximum.accumulate(equities)
        drawdowns = (equities - cum_max) / cum_max
        max_drawdown_pct = float(np.abs(np.min(drawdowns)) * 100.0) if len(drawdowns) > 0 else 0.0

        # 4. Trade Statistics
        closed_trades = [t for t in trades if not t.is_open]
        total_trades = len(closed_trades)
        
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]
        
        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        
        win_rate_pct = (num_wins / total_trades * 100.0) if total_trades > 0 else 0.0

        # Profit Factor = Gross Profits / Gross Losses
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = gross_profit if gross_profit > 0 else 0.0

        # 5. Annualized Return (%)
        num_days = max(1, len(equities))
        annualized_return_pct = (((final_equity / initial_capital) ** (252.0 / num_days)) - 1.0) * 100.0 if final_equity > 0 else 0.0

        return {
            "initial_capital": round(initial_capital, 2),
            "final_equity": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annualized_return_pct": round(annualized_return_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "win_rate_pct": round(win_rate_pct, 2),
            "total_trades": total_trades,
            "winning_trades": num_wins,
            "losing_trades": num_losses,
            "profit_factor": round(profit_factor, 2)
        }
