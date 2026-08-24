"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Cpu, Layers, BarChart3, Zap } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Overview", href: "/", icon: Activity },
    { name: "Visual Strategy Builder", href: "/builder", icon: Layers },
  ];

  return (
    <nav className="glass-card" style={{ borderRadius: 0, borderTop: "none", borderLeft: "none", borderRight: "none", position: "sticky", top: 0, zIndex: 50, backdropFilter: "blur(20px)" }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        
        {/* Brand Logo */}
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "linear-gradient(135deg, #00f2fe 0%, #7928ca 100%)", padding: "8px", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Cpu size={22} color="#fff" />
          </div>
          <div>
            <span style={{ fontSize: "18px", fontWeight: "700", letterSpacing: "-0.5px" }} className="gradient-text">
              QUANTENGINE
            </span>
            <span style={{ fontSize: "10px", color: "var(--primary-cyan)", marginLeft: "6px", border: "1px solid rgba(0, 242, 254, 0.3)", padding: "2px 6px", borderRadius: "4px" }}>
              PHASE 1
            </span>
          </div>
        </Link>

        {/* Nav Links */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  textDecoration: "none",
                  padding: "8px 16px",
                  borderRadius: "8px",
                  fontSize: "14px",
                  fontWeight: 500,
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  color: isActive ? "var(--primary-cyan)" : "var(--text-muted)",
                  background: isActive ? "rgba(0, 242, 254, 0.08)" : "transparent",
                  border: isActive ? "1px solid rgba(0, 242, 254, 0.2)" : "1px solid transparent",
                  transition: "all 0.2s ease"
                }}
              >
                <Icon size={16} />
                {item.name}
              </Link>
            );
          })}
        </div>

        {/* Engine Status Indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "var(--success-green)", background: "rgba(16, 185, 129, 0.08)", padding: "6px 12px", borderRadius: "20px", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--success-green)", boxShadow: "0 0 8px var(--success-green)" }}></span>
          <span>Event Engine Online</span>
        </div>

      </div>
    </nav>
  );
}
