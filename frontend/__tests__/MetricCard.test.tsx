import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MetricCard from "../components/MetricCard";
import { TrendingUp } from "lucide-react";

describe("MetricCard Component", () => {
  it("renders title, value, and icon correctly", () => {
    render(
      <MetricCard
        title="Sharpe Ratio"
        value="2.45"
        subtitle="Annualized"
        icon={TrendingUp}
        color="var(--primary-cyan)"
      />
    );

    expect(screen.getByText("Sharpe Ratio")).toBeDefined();
    expect(screen.getByText("2.45")).toBeDefined();
    expect(screen.getByText("Annualized")).toBeDefined();
  });
});
