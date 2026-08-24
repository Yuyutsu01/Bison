"use client";

import React, { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Node,
  Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Database, Sliders, Play, Rocket, ShieldAlert, Sparkles } from "lucide-react";

// Default Nodes for Visual Builder Canvas
const initialNodes: Node[] = [
  {
    id: "data-node",
    type: "input",
    position: { x: 50, y: 150 },
    data: { label: "Data Source: AAPL" },
    style: {
      background: "rgba(18, 24, 38, 0.9)",
      color: "#f3f4f6",
      border: "1px solid #00f2fe",
      borderRadius: "12px",
      padding: "16px",
      boxShadow: "0 0 20px rgba(0, 242, 254, 0.2)",
    },
  },
  {
    id: "strategy-node",
    position: { x: 350, y: 150 },
    data: { label: "MA Crossover (20 / 50)" },
    style: {
      background: "rgba(18, 24, 38, 0.9)",
      color: "#f3f4f6",
      border: "1px solid #7928ca",
      borderRadius: "12px",
      padding: "16px",
      boxShadow: "0 0 20px rgba(121, 40, 202, 0.2)",
    },
  },
  {
    id: "backtest-node",
    type: "output",
    position: { x: 650, y: 150 },
    data: { label: "Backtest Execution" },
    style: {
      background: "rgba(18, 24, 38, 0.9)",
      color: "#f3f4f6",
      border: "1px solid #10b981",
      borderRadius: "12px",
      padding: "16px",
      boxShadow: "0 0 20px rgba(16, 185, 129, 0.2)",
    },
  },
];

const initialEdges: Edge[] = [
  { id: "e1-2", source: "data-node", target: "strategy-node", animated: true, style: { stroke: "#00f2fe" } },
  { id: "e2-3", source: "strategy-node", target: "backtest-node", animated: true, style: { stroke: "#7928ca" } },
];

export default function VisualBuilder() {
  const router = useRouter();

  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  // Strategy & Backtest Parameters State
  const [symbol, setSymbol] = useState("AAPL");
  const [fastPeriod, setFastPeriod] = useState(20);
  const [slowPeriod, setSlowPeriod] = useState(50);
  const [initialCapital, setInitialCapital] = useState(100000);
  const [commission, setCommission] = useState(1.0);
  const [slippageBps, setSlippageBps] = useState(5.0);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const onNodesChange = useCallback(
    (changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    []
  );

  // Trigger Backtest Execution via REST API
  const handleRunBacktest = async () => {
    setIsSubmitting(true);
    setErrorMsg("");

    const payload = {
      strategy_config: {
        name: `MA Crossover (${fastPeriod}/${slowPeriod}) - ${symbol}`,
        strategy_type: "moving_average_crossover",
        symbol: symbol,
        parameters: {
          fast_period: Number(fastPeriod),
          slow_period: Number(slowPeriod),
        },
      },
      initial_capital: Number(initialCapital),
      commission: Number(commission),
      slippage_bps: Number(slippageBps),
    };

    try {
      const res = await fetch("/api/backtests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to execute backtest.");
      }

      const data = await res.json();
      // Redirect to detailed results dashboard
      router.push(`/backtests/${data.backtest_id}`);
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "24px", height: "calc(100vh - 120px)" }}>
      
      {/* React Flow Canvas Container */}
      <div className="glass-card" style={{ position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: "16px", left: "16px", zIndex: 10, display: "flex", alignItems: "center", gap: "8px", background: "rgba(10, 14, 23, 0.8)", padding: "8px 14px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
          <Sparkles size={16} color="var(--primary-cyan)" />
          <span style={{ fontSize: "13px", fontWeight: 600 }}>No-Code Strategy Canvas</span>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Controls style={{ background: "rgba(18, 24, 38, 0.9)", color: "#fff", borderColor: "var(--border-color)" }} />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="rgba(255,255,255,0.08)" />
        </ReactFlow>
      </div>

      {/* Properties & Configuration Side Panel */}
      <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Sliders size={20} color="var(--primary-cyan)" />
          <h2 style={{ fontSize: "16px", fontWeight: 700 }}>Strategy Configuration</h2>
        </div>

        {errorMsg && (
          <div style={{ background: "rgba(244, 63, 94, 0.15)", border: "1px solid rgba(244, 63, 94, 0.3)", color: "var(--danger-red)", padding: "12px", borderRadius: "8px", fontSize: "13px", display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldAlert size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Symbol Selector */}
        <div>
          <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Historical Asset Symbol
          </label>
          <select
            className="form-input"
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value);
              setNodes((nds) =>
                nds.map((n) => (n.id === "data-node" ? { ...n, data: { label: `Data Source: ${e.target.value}` } } : n))
              );
            }}
          >
            <option value="AAPL">AAPL (Apple Inc.)</option>
            <option value="MSFT">MSFT (Microsoft Corp.)</option>
            <option value="SPY">SPY (S&P 500 ETF)</option>
          </select>
        </div>

        {/* Fast MA Period */}
        <div>
          <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Fast SMA Lookback Period ({fastPeriod} bars)
          </label>
          <input
            type="range"
            min={2}
            max={50}
            value={fastPeriod}
            onChange={(e) => {
              const val = Number(e.target.value);
              setFastPeriod(val);
              setNodes((nds) =>
                nds.map((n) => (n.id === "strategy-node" ? { ...n, data: { label: `MA Crossover (${val} / ${slowPeriod})` } } : n))
              );
            }}
            style={{ width: "100%", accentColor: "var(--primary-cyan)" }}
          />
        </div>

        {/* Slow MA Period */}
        <div>
          <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Slow SMA Lookback Period ({slowPeriod} bars)
          </label>
          <input
            type="range"
            min={10}
            max={200}
            value={slowPeriod}
            onChange={(e) => {
              const val = Number(e.target.value);
              setSlowPeriod(val);
              setNodes((nds) =>
                nds.map((n) => (n.id === "strategy-node" ? { ...n, data: { label: `MA Crossover (${fastPeriod} / ${val})` } } : n))
              );
            }}
            style={{ width: "100%", accentColor: "var(--accent-purple)" }}
          />
        </div>

        <hr style={{ borderColor: "var(--border-color)" }} />

        {/* Initial Capital */}
        <div>
          <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Initial Capital ($)
          </label>
          <input
            type="number"
            className="form-input"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
          />
        </div>

        {/* Commission */}
        <div>
          <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Commission per Trade ($)
          </label>
          <input
            type="number"
            step="0.1"
            className="form-input"
            value={commission}
            onChange={(e) => setCommission(Number(e.target.value))}
          />
        </div>

        {/* Slippage */}
        <div>
          <label style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Slippage (Basis Points)
          </label>
          <input
            type="number"
            className="form-input"
            value={slippageBps}
            onChange={(e) => setSlippageBps(Number(e.target.value))}
          />
        </div>

        {/* Submit Button */}
        <button
          className="btn-primary"
          onClick={handleRunBacktest}
          disabled={isSubmitting}
          style={{ width: "100%", justifyContent: "center", marginTop: "auto", padding: "14px" }}
        >
          {isSubmitting ? (
            <span>Executing Engine...</span>
          ) : (
            <>
              <Rocket size={18} />
              <span>Run Backtest</span>
            </>
          )}
        </button>
      </div>

    </div>
  );
}
