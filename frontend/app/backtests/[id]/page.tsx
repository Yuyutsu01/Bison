"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import PerformanceDashboard from "@/components/PerformanceDashboard";
import { AlertCircle } from "lucide-react";

export default function BacktestResultsPage() {
  const params = useParams();
  const backtestId = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!backtestId) return;

    fetch(`/api/backtests/${backtestId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Backtest result not found.");
        return res.json();
      })
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [backtestId]);

  if (loading) {
    return (
      <div style={{ padding: "80px 24px", textAlign: "center", color: "var(--text-muted)" }}>
        <div style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px" }} className="gradient-text">
          Loading Analytics Dashboard...
        </div>
        <p style={{ fontSize: "14px", color: "var(--text-dim)" }}>Processing trade logs and mark-to-market equity curve...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-card" style={{ padding: "40px", textAlign: "center", maxWidth: "600px", margin: "40px auto", border: "1px solid rgba(244, 63, 94, 0.3)" }}>
        <AlertCircle size={32} color="var(--danger-red)" style={{ marginBottom: "12px" }} />
        <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>Backtest Not Found</h2>
        <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "20px" }}>{error || "Unable to retrieve backtest analytics."}</p>
        <a href="/builder" className="btn-primary" style={{ textDecoration: "none" }}>
          Return to Visual Builder
        </a>
      </div>
    );
  }

  return <PerformanceDashboard data={data} />;
}
