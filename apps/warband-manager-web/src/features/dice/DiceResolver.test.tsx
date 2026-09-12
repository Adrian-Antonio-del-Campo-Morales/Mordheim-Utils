import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

import { DiceResolver } from "./DiceResolver";

describe("DiceResolver", () => {
  it("replaces the completed roll with the dice required by the next step", async () => {
    const user = userEvent.setup();
    const resolve = vi.fn();
    const view = render(
      <DiceResolver count={2} sides={6} label="Tirada principal" locale="es" onResolve={resolve} />,
    );

    await user.click(screen.getByRole("button", { name: "Tirar 2D6" }));
    expect(screen.getByRole("status")).toHaveTextContent("Resultado:");

    view.rerender(
      <DiceResolver count={1} sides={6} label="Siguiente paso" locale="es" onResolve={resolve} />,
    );

    expect(screen.getByRole("button", { name: "Tirar 1D6" })).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
