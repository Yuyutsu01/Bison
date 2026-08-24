"use client";

import dynamic from "next/dynamic";

// Dynamic import with ssr: false as React Flow relies on browser DOM APIs
const VisualBuilder = dynamic(() => import("@/components/VisualBuilder"), {
  ssr: false,
  loading: () => (
    <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
      Loading No-Code Visual Builder Canvas...
    </div>
  ),
});

export default function BuilderPage() {
  return <VisualBuilder />;
}
