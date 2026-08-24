"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  TrendingUp,
  Award,
  TrendingDown,
  Percent,
  Repeat,
  DollarSign,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  BarChart2,
} from "lucide-react";
import MetricCard from "./MetricCard";

interface BacktestResult {
  backtest_id: string;
  symbol: string;
  status: string;
  metrics: {
    initial_capital: number;
    final_equity: number;
    total_return_pct: number;
    annualized_return_pct: number;
    sharpe_ratio: number;
    max_drawdown_pct: number;
    win_rate_pct: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    profit_factor: number;
  };
  equity_curve: Array<{ timestamp: string; equity: number; cash: number }>;
  trades: Array<{
    id: number;
    symbol: string;
    entry_time: string;
    exit_time: string;
    direction: string;
    quantity: number;
    entry_price: number;
    exit_price: number;
    pnl: number;
    pnl_pct: number;
  }>;
}

export default function PerformanceDashboard({ data }: { data: BacktestResult }) {
  const [filterDirection, setFilterDirection] = useState<string>("ALL");

  const { metrics, equity_curve, trades, symbol, backtest_id } = data;

  // Filter trades log
  const filteredTrades = trades.filter((t) => {
    if (filterDirection === "WINNERS") return t.pnl > 0;
    if (filterDirection === "LOSERS") return t.pnl <= 0;
    return true;
  });

  // Export trade log as CSV
  const handleExportCSV = () => {
    if (!trades.length) return;
    const headers = ["ID", "Symbol", "Direction", "Entry Time", "Entry Price", "Exit Time", "Exit Price", "Quantity", "P&L ($)", "P&L (%)"];
    const rows = trades.map((t) => [
      t.id,
      t.symbol,
      t.direction,
      t.entry_time,
      t.entry_price,
      t.exit_time,
      t.exit_price,
      t.quantity,
      t.pnl,
      t.pnl_pct,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `backtest_${symbol}_${backtest_id.slice(0, 8)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isPositiveReturn = metrics.total_return_pct >= 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1280px", margin: "0 auto", paddingBottom: "60px" }}>
      
      {/* Header Banner */}
      <div className="glass-card" style={{ padding: "24px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
            <h1 style={{ fontSize: "24px", fontWeight: 800 }} className="gradient-text">
              Backtest Performance Analytics
            </h1>
            <span className="badge-success">{symbol}</span>
            <span style={{ fontSize: "12px", color: "var(--text-dim)", fontFamily: "monospace" }}>ID: {backtest_id.slice(0, 13)}...</span>
          </div>
          <p style={{ fontSize: "14px", color: "var(--text-muted)" }}>
            Initial Capital: ${metrics.initial_capital.toLocaleString()} | Final Valuation: ${metrics.final_equity.toLocaleString()}
          </p>
        </div>

        <button className="btn-secondary" onClick={handleExportCSV}>
          <Download size={16} />
          Export Trade Log (CSV)
        </button>
      </div>

      {/* 6 Key Metric Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
        <MetricCard
          title="Total Return"
          value={`${metrics.total_return_pct > 0 ? "+" : ""}${metrics.total_return_pct}%`}
          subtitle={`Annualized: ${metrics.annualized_return_pct}%`}
          icon={isPositiveReturn ? TrendingUp : TrendingDown}
          color={isPositiveReturn ? "var(--success-green)" : "var(--danger-red)"}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={metrics.sharpe_ratio}
          subtitle="Risk-Adjusted Return"
          icon={Award}
          color="var(--primary-cyan)"
        />
        <MetricCard
          title="Max Drawdown"
          value={`-${metrics.max_drawdown_pct}%`}
          subtitle="Peak-to-Trough Decline"
          icon={TrendingDown}
          color="var(--danger-red)"
        />
        <MetricCard
          title="Win Rate"
          value={`${metrics.win_rate_pct}%`}
          subtitle={`${metrics.winning_trades}W / ${metrics.losing_trades}L`}
          icon={Percent}
          color="var(--primary-blue)"
        />
        <MetricCard
          title="Total Trades"
          value={metrics.total_trades}
          subtitle="Executed Fills"
          icon={Repeat}
          color="var(--accent-purple)"
        />
        <MetricCard
          title="Profit Factor"
          value={metrics.profit_factor}
          subtitle="Gross Profit / Gross Loss"
          icon={DollarSign}
          color="var(--warning-amber)"
        />
      </div>

      {/* Interactive Equity Curve Chart */}
      <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <BarChart2 size={20} color="var(--primary-cyan)" />
            <h2 style={{ fontSize: "18px", fontWeight: 700 }}>Portfolio Equity Curve</h2>
          </div>
          <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            Mark-to-Market Portfolio Valuation Over Time
          </span>
        </div>

        <div style={{ width: "100%", height: "360px" }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equity_curve} margin={{ top: 10, right: 30, left: 20, bottom: 0 }}>
              <defs>
                <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={isPositiveReturn ? "#00f2fe" : "#f43f5e"} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={isPositiveReturn ? "#00f2fe" : "#f43f5e"} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="timestamp" stroke="var(--text-dim)" fontSize={12} tickLine={false} />
              <YAxis
                stroke="var(--text-dim)"
                fontSize={12}
                domain={["auto", "auto"]}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "rgba(18, 24, 38, 0.95)",
                  border: "1px solid var(--border-glow)",
                  borderRadius: "12px",
                  color: "#fff",
                }}
                formatter={(val: any) => [`$${Number(val).toLocaleString()}`, "Portfolio Value"]}
              />
              <Area
                type="monotone"
                dataKey="equity"
                stroke={isPositiveReturn ? "#00f2fe" : "#f43f5e"}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#equityGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trade Log Table */}
      <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 700 }}>Trade Execution History ({filteredTrades.length})</h2>
          
          <div style={{ display: "flex", gap: "8px" }}>
            {["ALL", "WINNERS", "LOSERS"].map((f) => (
              <button
                key={f}
                onClick={() => setFilterDirection(f)}
                className="btn-secondary"
                style={{
                  padding: "6px 12px",
                  fontSize: "12px",
                  background: filterDirection === f ? "rgba(0, 242, 254, 0.15)" : "transparent",
                  borderColor: filterDirection === f ? "var(--primary-cyan)" : "var(--border-color)",
                  color: filterDirection === f ? "var(--primary-cyan)" : "var(--text-muted)",
                }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Trade #</th>
                <th>Symbol</th>
                <th>Direction</th>
                <th>Entry Time</th>
                <th>Entry Price</th>
                <th>Exit Time</th>
                <th>Exit Price</th>
                <th>Quantity</th>
                <th>P&L ($)</th>
                <th>P&L (%)</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.map((t) => {
                const isWin = t.pnl > 0;
                return (
                  <tr key={t.id}>
                    <td>#{t.id}</td>
                    <td style={{ fontWeight: 600 }}>{t.symbol}</td>
                    <td>
                      <span className={t.direction === "BUY" ? "badge-success" : "badge-danger"}>
                        {t.direction}
                      </span>
                    </td>
                    <td style={{ fontSize: "13px", color: "var(--text-muted)" }}>{t.entry_time}</td>
                    <td>${t.entry_price.toFixed(2)}</td>
                    <td style={{ fontSize: "13px", color: "var(--text-muted)" }}>{t.exit_time}</td>
                    <td>${t.exit_price ? `$${t.exit_price.toFixed(2)}` : "—"}</td>
                    <td>{t.quantity}</td>
                    <td style={{ color: isWin ? "var(--success-green)" : "var(--danger-red)", fontWeight: 600 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        {isWin ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                        ${t.pnl > 0 ? `+${t.pnl.toFixed(2)}` : t.pnl.toFixed(2)}
                      </div>
                    </td>
                    <td style={{ color: isWin ? "var(--success-green)" : "var(--danger-red)", fontWeight: 600 }}>
                      {t.pnl_pct > 0 ? `+${t.pnl_pct.toFixed(2)}` : t.pnl_pct.toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
              {filteredTrades.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: "center", color: "var(--text-dim)", padding: "24px" }}>
                    No trades match the selected filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
