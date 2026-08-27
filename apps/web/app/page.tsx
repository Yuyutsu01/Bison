'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { TrendingUp, Cpu, Plus, Layers, Play, CheckCircle, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { apiClient, StrategySummary } from '../lib/api';

export default function HomePage() {
  const router = useRouter();
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await apiClient.get('/strategies');
        setStrategies(res.data);
      } catch (err) {
        console.log('No auth or strategies found');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleLaunchPreset = async () => {
    try {
      // 1. Create Preset Strategy
      const dsl = {
        name: 'NIFTY EMA 20/50 Crossover Preset',
        instrument: { symbol: 'NIFTY', exchange: 'NSE', timeframe: '5m' },
        entry: {
          operator: 'AND',
          conditions: [
            {
              left: { type: 'indicator', name: 'EMA', parameters: { period: 20 } },
              operator: 'CROSS_ABOVE',
              right: { type: 'indicator', name: 'EMA', parameters: { period: 50 } },
            },
          ],
        },
        exit: { operator: 'OR', conditions: [] },
        risk: { stop_loss_percent: 1.0, target_percent: 2.0, end_of_day_exit: true },
        position_sizing: { type: 'FIXED_QUANTITY', value: 50 },
      };

      // Register temporary user if needed
      let token = localStorage.getItem('bison_token');
      if (!token) {
        const regRes = await apiClient.post('/auth/register', {
          email: `trader_${Date.now()}@bison.com`,
          password: 'Password123!',
          full_name: 'Quant Trader',
        });
        localStorage.setItem('bison_token', regRes.data.access_token);
      }

      const stratRes = await apiClient.post('/strategies', dsl);
      const btRes = await apiClient.post('/backtests', {
        strategy_id: stratRes.data.id,
        initial_capital: 100000.0,
      });

      router.push(`/backtests/${btRes.data.id}`);
    } catch (err) {
      console.error(err);
      alert('Failed to launch backtest preset. Please check backend connection.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-12 pb-16">
      {/* Hero Banner */}
      <div className="glass-panel p-10 rounded-3xl relative overflow-hidden border border-blue-500/20">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -z-10" />
        <div className="max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold">
            <Zap className="w-3.5 h-3.5" />
            Build Iteration 1 • Indian Market Event-Driven Engine
          </div>
          <h1 className="text-4xl font-extrabold text-white leading-tight">
            Institutional Algorithmic Trading Platform for Indian Traders
          </h1>
          <p className="text-gray-400 text-base leading-relaxed">
            Construct visual quantitative strategies with zero look-ahead bias, realistic Indian market friction (Brokerage, STT, GST, Stamp duty), and trade inspection.
          </p>

          <div className="pt-4 flex flex-wrap items-center gap-4">
            <button
              onClick={handleLaunchPreset}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-semibold shadow-lg shadow-blue-500/25 transition-all hover:scale-105"
            >
              <Play className="w-5 h-5 fill-current" />
              1-Click NIFTY Backtest
            </button>

            <Link
              href="/builder"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gray-900 hover:bg-gray-800 text-gray-200 font-semibold border border-gray-800 transition-colors"
            >
              <Cpu className="w-5 h-5 text-blue-400" />
              Open Visual Builder
            </Link>
          </div>
        </div>
      </div>

      {/* Feature Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel glass-panel-hover p-6 rounded-2xl space-y-3">
          <div className="p-3 w-fit rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white">Zero Look-Ahead Bias</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Signals generated at bar $t$ close execute strictly on bar $t+1$ Open, preventing optimistic future data leakage.
          </p>
        </div>

        <div className="glass-panel glass-panel-hover p-6 rounded-2xl space-y-3">
          <div className="p-3 w-fit rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <TrendingUp className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white">Indian Market Friction</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Accurate statutory tax accounting: Brokerage (₹20 cap), STT, Exchange fees, SEBI charges, 18% GST, and Stamp duty.
          </p>
        </div>

        <div className="glass-panel glass-panel-hover p-6 rounded-2xl space-y-3">
          <div className="p-3 w-fit rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white">Visual Strategy Builder</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            No-code rule canvas for building indicator crossovers (EMA, RSI, MACD, BB, ATR) and risk management rules.
          </p>
        </div>
      </div>

      {/* Recent Strategies Section */}
      <div className="glass-panel p-8 rounded-3xl space-y-6">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-400" />
              Your Strategy Library
            </h2>
            <p className="text-xs text-gray-400 mt-1">Saved quantitative strategies & versions</p>
          </div>
          <Link
            href="/builder"
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Strategy
          </Link>
        </div>

        {strategies.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map((s) => (
              <div
                key={s.id}
                className="bg-gray-900/60 p-5 rounded-2xl border border-gray-800 hover:border-blue-500/40 transition-all flex items-center justify-between"
              >
                <div>
                  <h3 className="font-bold text-white">{s.name}</h3>
                  <div className="text-xs text-gray-500 mt-1">
                    Version v{s.current_version} • Created {new Date(s.created_at).toLocaleDateString()}
                  </div>
                </div>
                <Link
                  href={`/builder?id=${s.id}`}
                  className="p-2 rounded-xl bg-gray-800 hover:bg-blue-600 text-gray-300 hover:text-white transition-colors"
                >
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 space-y-3">
            <p className="text-gray-500 text-sm">No saved strategies found in your library yet.</p>
            <button
              onClick={handleLaunchPreset}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold underline"
            >
              Launch Instant Preset Backtest
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
