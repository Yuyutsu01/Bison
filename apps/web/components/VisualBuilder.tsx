'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Save, Plus, Trash2, CheckCircle, AlertTriangle, Cpu, Sliders, ShieldAlert } from 'lucide-react';
import { apiClient, StrategyDSL } from '../lib/api';

export default function VisualBuilder() {
  const router = useRouter();

  const [strategyName, setStrategyName] = useState('NIFTY EMA 20/50 Crossover');
  const [symbol, setSymbol] = useState('NIFTY');
  const [timeframe, setTimeframe] = useState('5m');
  const [exchange, setExchange] = useState('NSE');

  // Rule Group Entry Conditions
  const [entryConditions, setEntryConditions] = useState([
    {
      leftType: 'indicator',
      leftName: 'EMA',
      leftParamPeriod: 20,
      leftPriceField: 'close',
      operator: 'CROSS_ABOVE',
      rightType: 'indicator',
      rightName: 'EMA',
      rightParamPeriod: 50,
      rightPriceField: 'close',
      rightConstant: 50,
    },
    {
      leftType: 'indicator',
      leftName: 'RSI',
      leftParamPeriod: 14,
      leftPriceField: 'close',
      operator: 'GREATER_THAN',
      rightType: 'constant',
      rightName: 'EMA',
      rightParamPeriod: 20,
      rightPriceField: 'close',
      rightConstant: 50,
    },
  ]);

  // Risk & Position Sizing
  const [stopLossPercent, setStopLossPercent] = useState<number>(1.0);
  const [targetPercent, setTargetPercent] = useState<number>(2.0);
  const [trailingStopPercent, setTrailingStopPercent] = useState<number>(0.5);
  const [positionQty, setPositionQty] = useState<number>(50);

  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isValidated, setIsValidated] = useState<boolean | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  const buildDSL = (): StrategyDSL => ({
    name: strategyName,
    instrument: { symbol, exchange, timeframe },
    entry: {
      operator: 'AND',
      conditions: entryConditions.map((c) => ({
        left:
          c.leftType === 'price'
            ? { type: 'price', field: c.leftPriceField }
            : { type: 'indicator', name: c.leftName, parameters: { period: Number(c.leftParamPeriod) } },
        operator: c.operator,
        right:
          c.rightType === 'constant'
            ? { type: 'constant', value: Number(c.rightConstant) }
            : c.rightType === 'price'
            ? { type: 'price', field: c.rightPriceField }
            : { type: 'indicator', name: c.rightName, parameters: { period: Number(c.rightParamPeriod) } },
      })),
    },
    exit: { operator: 'OR', conditions: [] },
    risk: {
      stop_loss_percent: stopLossPercent || undefined,
      target_percent: targetPercent || undefined,
      trailing_stop_percent: trailingStopPercent || undefined,
      end_of_day_exit: true,
    },
    position_sizing: {
      type: 'FIXED_QUANTITY',
      value: positionQty,
    },
  });

  const handleValidate = async () => {
    try {
      const dsl = buildDSL();
      const res = await apiClient.post('/strategies/validate', dsl);
      setIsValidated(res.data.is_valid);
      setValidationErrors(res.data.errors || []);
    } catch (err: any) {
      setIsValidated(false);
      setValidationErrors([err.response?.data?.detail || 'Validation failed server error.']);
    }
  };

  const handleSaveAndRun = async () => {
    setIsSaving(true);
    try {
      const dsl = buildDSL();
      const stratRes = await apiClient.post('/strategies', dsl);
      const stratId = stratRes.data.id;

      const btRes = await apiClient.post('/backtests', {
        strategy_id: stratId,
        initial_capital: 100000.0,
      });

      router.push(`/backtests/${btRes.data.id}`);
    } catch (err: any) {
      setIsSaving(false);
      setIsValidated(false);
      const errors = err.response?.data?.detail?.errors || [err.response?.data?.detail || 'Failed to save strategy.'];
      setValidationErrors(errors);
    }
  };

  const addCondition = () => {
    setEntryConditions([
      ...entryConditions,
      {
        leftType: 'indicator',
        leftName: 'SMA',
        leftParamPeriod: 20,
        leftPriceField: 'close',
        operator: 'GREATER_THAN',
        rightType: 'constant',
        rightName: 'EMA',
        rightParamPeriod: 20,
        rightPriceField: 'close',
        rightConstant: 100,
      },
    ]);
  };

  const removeCondition = (idx: number) => {
    setEntryConditions(entryConditions.filter((_, i) => i !== idx));
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-2xl">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-6 h-6 text-blue-500" />
            Visual Rule-Based Strategy Builder
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Construct quantitative strategy rules visually for Indian markets (NSE/BSE).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleValidate}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-200 text-sm font-medium border border-gray-700 transition-colors"
          >
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            Validate Rules
          </button>
          <button
            onClick={handleSaveAndRun}
            disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {isSaving ? 'Launching...' : 'Run Backtest'}
          </button>
        </div>
      </div>

      {/* Validation Status Banner */}
      {isValidated !== null && (
        <div
          className={`p-4 rounded-xl border ${
            isValidated
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-red-500/10 border-red-500/30 text-red-300'
          }`}
        >
          <div className="flex items-center gap-2 font-semibold">
            {isValidated ? (
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-red-400" />
            )}
            {isValidated ? 'Strategy Validated Successfully! Ready for Backtest.' : 'Strategy Validation Errors Found:'}
          </div>
          {validationErrors.length > 0 && (
            <ul className="list-disc list-inside mt-2 text-sm space-y-1">
              {validationErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Configuration Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategy Metadata & Instrument */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-gray-800 pb-3">
            <Sliders className="w-5 h-5 text-blue-400" />
            Instrument & Timeframe
          </h2>
          <div>
            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Strategy Name</label>
            <input
              type="text"
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
              className="w-full mt-1 px-4 py-2.5 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm"
              >
                <option value="NIFTY">NIFTY 50</option>
                <option value="BANKNIFTY">BANKNIFTY</option>
                <option value="RELIANCE">RELIANCE</option>
                <option value="TCS">TCS</option>
                <option value="INFY">INFY</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="1d">Daily</option>
              </select>
            </div>
          </div>
        </div>

        {/* Risk & Position Management */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-gray-800 pb-3">
            <ShieldAlert className="w-5 h-5 text-emerald-400" />
            Risk Management & Position Sizing
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold">Stop Loss (%)</label>
              <input
                type="number"
                step="0.1"
                value={stopLossPercent}
                onChange={(e) => setStopLossPercent(parseFloat(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold">Target (%)</label>
              <input
                type="number"
                step="0.1"
                value={targetPercent}
                onChange={(e) => setTargetPercent(parseFloat(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold">Trailing Stop (%)</label>
              <input
                type="number"
                step="0.1"
                value={trailingStopPercent}
                onChange={(e) => setTrailingStopPercent(parseFloat(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold">Lot Quantity</label>
              <input
                type="number"
                value={positionQty}
                onChange={(e) => setPositionQty(parseInt(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Entry Rule Canvas / Visual Rules List */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded font-mono font-bold">
                IF (ENTRY RULE GROUP - AND)
              </span>
            </h2>
            <p className="text-xs text-gray-400 mt-1">All conditions must evaluate TRUE at bar close to trigger signal.</p>
          </div>
          <button
            onClick={addCondition}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Rule
          </button>
        </div>

        <div className="space-y-4">
          {entryConditions.map((cond, idx) => (
            <div key={idx} className="bg-gray-900/80 p-4 rounded-xl border border-gray-800 flex flex-wrap items-center gap-3">
              <span className="text-xs font-bold text-gray-500 px-2 py-1 bg-gray-800 rounded">
                #{idx + 1}
              </span>

              {/* Left Operand */}
              <div className="flex items-center gap-2 bg-gray-950 p-2 rounded-lg border border-gray-800">
                <select
                  value={cond.leftType}
                  onChange={(e) => {
                    const updated = [...entryConditions];
                    updated[idx].leftType = e.target.value;
                    setEntryConditions(updated);
                  }}
                  className="bg-transparent text-xs text-blue-400 font-bold"
                >
                  <option value="indicator">INDICATOR</option>
                  <option value="price">PRICE</option>
                </select>

                {cond.leftType === 'indicator' ? (
                  <>
                    <select
                      value={cond.leftName}
                      onChange={(e) => {
                        const updated = [...entryConditions];
                        updated[idx].leftName = e.target.value;
                        setEntryConditions(updated);
                      }}
                      className="bg-transparent text-xs text-white"
                    >
                      <option value="EMA">EMA</option>
                      <option value="SMA">SMA</option>
                      <option value="RSI">RSI</option>
                      <option value="ATR">ATR</option>
                    </select>
                    <input
                      type="number"
                      value={cond.leftParamPeriod}
                      onChange={(e) => {
                        const updated = [...entryConditions];
                        updated[idx].leftParamPeriod = parseInt(e.target.value);
                        setEntryConditions(updated);
                      }}
                      className="w-14 bg-gray-900 text-xs text-white px-2 py-1 rounded border border-gray-800"
                    />
                  </>
                ) : (
                  <select
                    value={cond.leftPriceField}
                    onChange={(e) => {
                      const updated = [...entryConditions];
                      updated[idx].leftPriceField = e.target.value;
                      setEntryConditions(updated);
                    }}
                    className="bg-transparent text-xs text-white"
                  >
                    <option value="close">CLOSE</option>
                    <option value="open">OPEN</option>
                    <option value="high">HIGH</option>
                    <option value="low">LOW</option>
                  </select>
                )}
              </div>

              {/* Operator */}
              <select
                value={cond.operator}
                onChange={(e) => {
                  const updated = [...entryConditions];
                  updated[idx].operator = e.target.value;
                  setEntryConditions(updated);
                }}
                className="bg-blue-600/20 text-blue-300 font-mono text-xs px-3 py-2 rounded-lg border border-blue-500/30"
              >
                <option value="CROSS_ABOVE">CROSS_ABOVE</option>
                <option value="CROSS_BELOW">CROSS_BELOW</option>
                <option value="GREATER_THAN">GREATER_THAN (&gt;)</option>
                <option value="LESS_THAN">LESS_THAN (&lt;)</option>
                <option value="GREATER_THAN_EQUAL">GREATER_THAN_EQUAL (&gt;=)</option>
                <option value="LESS_THAN_EQUAL">LESS_THAN_EQUAL (&lt;=)</option>
              </select>

              {/* Right Operand */}
              <div className="flex items-center gap-2 bg-gray-950 p-2 rounded-lg border border-gray-800">
                <select
                  value={cond.rightType}
                  onChange={(e) => {
                    const updated = [...entryConditions];
                    updated[idx].rightType = e.target.value;
                    setEntryConditions(updated);
                  }}
                  className="bg-transparent text-xs text-emerald-400 font-bold"
                >
                  <option value="indicator">INDICATOR</option>
                  <option value="constant">CONSTANT</option>
                  <option value="price">PRICE</option>
                </select>

                {cond.rightType === 'indicator' ? (
                  <>
                    <select
                      value={cond.rightName}
                      onChange={(e) => {
                        const updated = [...entryConditions];
                        updated[idx].rightName = e.target.value;
                        setEntryConditions(updated);
                      }}
                      className="bg-transparent text-xs text-white"
                    >
                      <option value="EMA">EMA</option>
                      <option value="SMA">SMA</option>
                      <option value="RSI">RSI</option>
                    </select>
                    <input
                      type="number"
                      value={cond.rightParamPeriod}
                      onChange={(e) => {
                        const updated = [...entryConditions];
                        updated[idx].rightParamPeriod = parseInt(e.target.value);
                        setEntryConditions(updated);
                      }}
                      className="w-14 bg-gray-900 text-xs text-white px-2 py-1 rounded border border-gray-800"
                    />
                  </>
                ) : cond.rightType === 'constant' ? (
                  <input
                    type="number"
                    value={cond.rightConstant}
                    onChange={(e) => {
                      const updated = [...entryConditions];
                      updated[idx].rightConstant = parseFloat(e.target.value);
                      setEntryConditions(updated);
                    }}
                    className="w-20 bg-gray-900 text-xs text-white px-2 py-1 rounded border border-gray-800"
                  />
                ) : (
                  <select
                    value={cond.rightPriceField}
                    onChange={(e) => {
                      const updated = [...entryConditions];
                      updated[idx].rightPriceField = e.target.value;
                      setEntryConditions(updated);
                    }}
                    className="bg-transparent text-xs text-white"
                  >
                    <option value="close">CLOSE</option>
                    <option value="open">OPEN</option>
                  </select>
                )}
              </div>

              <button
                onClick={() => removeCondition(idx)}
                className="ml-auto text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
