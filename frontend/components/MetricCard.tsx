"use client";

import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  color?: string;
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend = "neutral",
  color = "var(--primary-cyan)",
}: MetricCardProps) {
  return (
    <div className="glass-card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px", position: "relative", overflow: "hidden" }}>
      {/* Background Accent Glow */}
      <div
        style={{
          position: "absolute",
          top: "-20px",
          right: "-20px",
          width: "80px",
          height: "80px",
          borderRadius: "50%",
          background: color,
          opacity: 0.12,
          filter: "blur(20px)",
        }}
      />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: 500 }}>{title}</span>
        <div style={{ background: "rgba(255, 255, 255, 0.05)", padding: "8px", borderRadius: "8px", color }}>
          <Icon size={18} />
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
        <span style={{ fontSize: "26px", fontWeight: "700", letterSpacing: "-0.5px" }}>{value}</span>
        {subtitle && <span style={{ fontSize: "12px", color: "var(--text-dim)" }}>{subtitle}</span>}
      </div>
    </div>
  );
}
