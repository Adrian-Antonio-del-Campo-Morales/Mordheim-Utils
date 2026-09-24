import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "@src/features/campaign/types";
import { CampaignStatistics } from "@src/features/statistics/CampaignStatistics";

const document = {
  campaign: {
    current_state_number: 2,
    battles: [
      { number: 2, result: "win" },
      { number: 1, result: "loss" },
      { number: 3, result: "victory" },
    ],
    states: [
      { number: 1, rating: 100, models: 5 },
      { number: 2, rating: 115, models: 6 },
    ],
  },
} as unknown as CampaignDocument;

describe("CampaignStatistics", () => {
  it("counts only committed battles and victories", () => {
    render(<CampaignStatistics document={document} locale="en" />);
    expect(screen.getByText("2", { selector: "dd" })).toHaveTextContent("2");
    expect(screen.getByText("1", { selector: "dd" })).toHaveTextContent("1");
  });

  it("shows the current state and rating progression", () => {
    render(<CampaignStatistics document={document} locale="en" />);
    expect(screen.getAllByText("115")).not.toHaveLength(0);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders localized zero metrics when no state has been committed", () => {
    const empty = { campaign: { current_state_number: 0, battles: [], states: [] } } as unknown as CampaignDocument;
    render(<CampaignStatistics document={empty} locale="es" />);

    expect(screen.getByRole("heading", { name: "Estadísticas de campaña" })).toBeInTheDocument();
    expect(screen.getByText("Todavía no hay estados confirmados.")).toBeInTheDocument();
    expect(screen.getAllByText("0", { selector: "dd" })).toHaveLength(4);
  });
});
