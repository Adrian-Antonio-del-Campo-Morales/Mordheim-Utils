import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { App } from "./App";

describe("App shell (P3.1)", () => {
  it("renders the empty shell without importing domain code", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Mordheim Warband Manager",
    );
  });
});
