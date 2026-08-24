"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Cpu, Layers, Play, Zap, ShieldCheck, BarChart3, ArrowRight } from "lucide-react";

export default function Home() {
  const router = useRouter();

  // Preset quick launcher
  const quickLaunchPresets = [
    { name: "Golden Crossover", symbol: "AAPL", fast: 20, slow: 50, desc: "Classic trend-following strategy on Apple Inc." },
    { name: "Fast Momentum", symbol: "MSFT", fast: 10, slow: 30, desc: "Aggressive short-term crossover on Microsoft Corp." },
    { name: "Broad Market Trend", symbol: "SPY", fast: 50, slow: 200, desc: "Institutional long-term trend filter on S&P 500 ETF." },
  ];

  const handleQuickLaunch = async (symbol: string, fast: number, slow: number) => {
    const payload = {
      strategy_config: {
        name: `Quick Launch (${fast}/${slow}) - ${symbol}`,
        strategy_type: "moving_average_crossover",
        symbol,
        parameters: { fast_period: fast, slow_period: slow },
      },
      initial_capital: 100000.0,
      commission: 1.0,
      slippage_bps: 5.0,
    };

    try {
      const res = await fetch("/api/backtests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      router.push(`/backtests/${data.backtest_id}`);
    } catch (e) {
      console.error("Failed to run preset backtest:", e);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "40px", paddingBottom: "60px" }}>
      
      {/* Hero Section */}
      <div className="glass-card" style={{ padding: "48px", textAlign: "center", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: "-50px", left: "50%", transform: "translateX(-50%)", width: "400px", height: "200px", background: "linear-gradient(135deg, rgba(0,242,254,0.15) 0%, rgba(121,40,202,0.15) 100%)", filter: "blur(60px)", borderRadius: "50%" }} />
        
        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(0, 242, 254, 0.08)", border: "1px solid rgba(0, 242, 254, 0.2)", padding: "6px 16px", borderRadius: "20px", fontSize: "13px", color: "var(--primary-cyan)", marginBottom: "20px" }}>
          <Zap size={14} />
          <span>High-Performance Event-Driven Backtesting Core</span>
        </div>

        <h1 style={{ fontSize: "42px", fontWeight: 800, lineHeight: 1.2, marginBottom: "16px" }} className="gradient-text">
          Institutional Algorithmic Trading Platform
        </h1>
        
        <p style={{ fontSize: "16px", color: "var(--text-muted)", maxWidth: "680px", margin: "0 auto 32px auto", lineHeight: 1.6 }}>
          Build, backtest, and optimize quantitative trading strategies using a visual no-code interface backed by a deterministic 1M+ event/sec Python execution engine.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: "16px" }}>
          <Link href="/builder" className="btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>
            <Layers size={18} />
            Open Visual Builder
          </Link>
        </div>
      </div>

      {/* Feature Highlights Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px" }}>
        <div className="glass-card" style={{ padding: "24px" }}>
          <Cpu size={24} color="var(--primary-cyan)" style={{ marginBottom: "12px" }} />
          <h3 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "8px" }}>Event-Driven Core</h3>
          <p style={{ fontSize: "14px", color: "var(--text-muted)", lineHeight: 1.5 }}>
            Synchronous event loop routing MarketData, Signal, Order, and Fill events chronologically without look-ahead bias.
          </p>
        </div>

        <div className="glass-card" style={{ padding: "24px" }}>
          <Layers size={24} color="var(--accent-purple)" style={{ marginBottom: "12px" }} />
          <h3 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "8px" }}>No-Code Strategy Builder</h3>
          <p style={{ fontSize: "14px", color: "var(--text-muted)", lineHeight: 1.5 }}>
            React Flow canvas allowing users to connect data feeds, indicators, and risk settings visually without coding.
          </p>
        </div>

        <div className="glass-card" style={{ padding: "24px" }}>
          <ShieldCheck size={24} color="var(--success-green)" style={{ marginBottom: "12px" }} />
          <h3 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "8px" }}>Realistic Friction</h3>
          <p style={{ fontSize: "14px", color: "var(--text-muted)", lineHeight: 1.5 }}>
            Fills executed at next bar Open price with per-trade commission fees and basis-point slippage modeling.
          </p>
        </div>
      </div>

      {/* Quick Launch Strategy Presets */}
      <div className="glass-card" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "6px" }}>Instant Preset Backtests</h2>
          <p style={{ fontSize: "14px", color: "var(--text-muted)" }}>
            Launch a pre-configured strategy backtest in 1-click on pre-seeded market data.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
          {quickLaunchPresets.map((p) => (
            <div key={p.name} className="glass-card glass-card-interactive" style={{ padding: "20px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                  <span style={{ fontSize: "16px", fontWeight: 700 }}>{p.name}</span>
                  <span className="badge-success">{p.symbol}</span>
                </div>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "16px" }}>{p.desc}</p>
                <div style={{ fontSize: "12px", color: "var(--primary-cyan)", marginBottom: "16px" }}>
                  Fast: {p.fast} SMA | Slow: {p.slow} SMA
                </div>
              </div>

              <button
                className="btn-secondary"
                onClick={() => handleQuickLaunch(p.symbol, p.fast, p.slow)}
                style={{ width: "100%", justifyContent: "center" }}
              >
                <Play size={14} />
                Run Backtest
              </button>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
