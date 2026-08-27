'use client';

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Award,
  DollarSign,
  PieChart,
  Download,
  Info,
  X,
  FileSpreadsheet,
} from 'lucide-react';
import { BacktestDetailDTO, TradeDTO, apiClient } from '../lib/api';

interface Props {
  data: BacktestDetailDTO;
}

export default function PerformanceDashboard({ data }: Props) {
  const [selectedTrade, setSelectedTrade] = useState<TradeDTO | null>(null);

  const handleExportCSV = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/backtests/${data.id}/export/csv`, '_blank');
  };

  const isProfitable = (data.total_net_pnl || 0) >= 0;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Header Card */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{data.strategy_name}</h1>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              ID: {data.id.slice(0, 8)}
            </span>
            <span
              className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                data.status === 'COMPLETED'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
              }`}
            >
              {data.status}
            </span>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            Executed on NSE Market Data • Initial Capital: ₹{data.initial_capital.toLocaleString()}
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium border border-gray-700 transition-colors"
        >
          <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
          Export Trades CSV
        </button>
      </div>

      {/* Quantitative Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Net PnL Card */}
        <div className="glass-panel glass-panel-hover p-5 rounded-2xl">
          <div className="flex items-center justify-between text-gray-400 text-xs font-bold uppercase tracking-wider">
            <span>Net Profit & Loss</span>
            <DollarSign className="w-4 h-4 text-blue-400" />
          </div>
          <div
            className={`text-2xl font-bold mt-2 ${
              isProfitable ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {isProfitable ? '+' : ''}₹{(data.total_net_pnl || 0).toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Final Capital: ₹{(data.final_capital || data.initial_capital).toLocaleString()}
          </div>
        </div>

        {/* Sharpe Ratio Card */}
        <div className="glass-panel glass-panel-hover p-5 rounded-2xl">
          <div className="flex items-center justify-between text-gray-400 text-xs font-bold uppercase tracking-wider">
            <span>Sharpe Ratio</span>
            <Award className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {data.sharpe_ratio ?? 0.0}
          </div>
          <div className="text-xs text-gray-500 mt-1">Risk-Adjusted Return</div>
        </div>

        {/* Max Drawdown Card */}
        <div className="glass-panel glass-panel-hover p-5 rounded-2xl">
          <div className="flex items-center justify-between text-gray-400 text-xs font-bold uppercase tracking-wider">
            <span>Max Drawdown</span>
            <TrendingDown className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-red-400 mt-2">
            -{data.max_drawdown_percent ?? 0.0}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Peak-to-Trough Decline</div>
        </div>

        {/* Win Rate & Profit Factor Card */}
        <div className="glass-panel glass-panel-hover p-5 rounded-2xl">
          <div className="flex items-center justify-between text-gray-400 text-xs font-bold uppercase tracking-wider">
            <span>Win Rate</span>
            <PieChart className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {data.win_rate ?? 0.0}%
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Profit Factor: {data.profit_factor ?? 0.0} ({data.total_trades} trades)
          </div>
        </div>
      </div>

      {/* Equity Curve Chart */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          Portfolio Mark-to-Market Equity Curve
        </h2>
        <div className="h-72 w-full">
          {data.equity_curve && data.equity_curve.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.equity_curve}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="timestamp" stroke="#6B7280" tick={{ fontSize: 11 }} />
                <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#equityGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              No equity curve points available.
            </div>
          )}
        </div>
      </div>

      {/* Executed Trade Log Table */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h2 className="text-lg font-semibold text-white">Executed Trade History Log</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-900/60 text-xs uppercase font-bold text-gray-400 border-b border-gray-800">
              <tr>
                <th className="px-4 py-3">Trade ID</th>
                <th className="px-4 py-3">Symbol</th>
                <th className="px-4 py-3">Side</th>
                <th className="px-4 py-3">Entry Time</th>
                <th className="px-4 py-3">Entry Price</th>
                <th className="px-4 py-3">Exit Price</th>
                <th className="px-4 py-3">Net PnL (₹)</th>
                <th className="px-4 py-3">Exit Reason</th>
                <th className="px-4 py-3">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {data.trades && data.trades.length > 0 ? (
                data.trades.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-blue-400 font-bold">
                      {t.trade_identifier}
                    </td>
                    <td className="px-4 py-3 font-bold text-white">{t.symbol}</td>
                    <td className="px-4 py-3">
                      <span className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-xs font-bold border border-emerald-500/20">
                        {t.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs">{t.entry_time}</td>
                    <td className="px-4 py-3">₹{t.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      {t.exit_price ? `₹${t.exit_price.toFixed(2)}` : '-'}
                    </td>
                    <td
                      className={`px-4 py-3 font-bold ${
                        t.net_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {t.net_pnl >= 0 ? '+' : ''}₹{t.net_pnl.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      {t.exit_reason || 'N/A'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedTrade(t)}
                        className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-blue-400 transition-colors"
                      >
                        <Info className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-gray-500">
                    No trades executed in this backtest run.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trade Inspector Modal */}
      {selectedTrade && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel max-w-lg w-full p-6 rounded-2xl space-y-6 relative border border-gray-700">
            <button
              onClick={() => setSelectedTrade(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white p-1 rounded-lg bg-gray-800"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="border-b border-gray-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-400" />
                Trade Inspection ({selectedTrade.trade_identifier})
              </h3>
              <p className="text-xs text-gray-400 mt-1">
                Detailed execution breakdown & indicator state snapshots
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                <div className="text-xs text-gray-400">Entry Details</div>
                <div className="font-bold text-white mt-1">₹{selectedTrade.entry_price}</div>
                <div className="text-xs text-gray-500">{selectedTrade.entry_time}</div>
              </div>
              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                <div className="text-xs text-gray-400">Exit Details</div>
                <div className="font-bold text-white mt-1">
                  {selectedTrade.exit_price ? `₹${selectedTrade.exit_price}` : '-'}
                </div>
                <div className="text-xs text-gray-500">{selectedTrade.exit_time || 'Open'}</div>
              </div>
            </div>

            {/* Financial & Friction Breakdown */}
            <div className="space-y-2 text-xs bg-gray-950 p-4 rounded-xl border border-gray-800">
              <div className="flex justify-between">
                <span className="text-gray-400">Gross PnL:</span>
                <span className="font-mono text-white">₹{selectedTrade.gross_pnl}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Statutory Fees & Slippage:</span>
                <span className="font-mono text-red-400">-₹{selectedTrade.total_costs}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-gray-800 font-bold">
                <span className="text-gray-200">Net Realized PnL:</span>
                <span
                  className={selectedTrade.net_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}
                >
                  ₹{selectedTrade.net_pnl}
                </span>
              </div>
            </div>

            {/* Indicator Snapshots */}
            {selectedTrade.entry_indicators && (
              <div>
                <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                  Signal Bar Indicator Values
                </div>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  {Object.entries(selectedTrade.entry_indicators).map(([k, v]) => (
                    <div key={k} className="bg-gray-900 px-3 py-1.5 rounded border border-gray-800 flex justify-between">
                      <span className="text-gray-400">{k}:</span>
                      <span className="text-blue-400 font-bold">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
