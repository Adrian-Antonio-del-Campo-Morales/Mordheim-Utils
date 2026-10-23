import { translate } from "@src/features/campaign/i18n-core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

import { DiceResolver } from "@src/features/dice/DiceResolver";

describe("DiceResolver", () => {
  it("replaces the completed roll with the dice required by the next step", async () => {
    const user = userEvent.setup();
    const resolve = vi.fn();
    const view = render(
      <DiceResolver count={2} sides={6} label={translate({ key: "ui.9a5040b02281" }, "es")} locale="es" onResolve={resolve} />,
    );

    await user.click(screen.getByRole("button", { name: "Tirar 2D6" }));
    expect(screen.getByRole("status")).toHaveTextContent("Resultado:");

    view.rerender(
      <DiceResolver count={1} sides={6} label={translate({ key: "ui.6421ce8b8f42" }, "es")} locale="es" onResolve={resolve} />,
    );

    expect(screen.getByRole("button", { name: "Tirar 1D6" })).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("does not submit its enclosing form when resolving dice", async () => {
    const user = userEvent.setup();
    const submit = vi.fn();
    render(<form onSubmit={(event) => { event.preventDefault(); submit(); }}><DiceResolver count={1} sides={6} label={translate({ key: "ui.90f3bdb4a942" }, "es")} locale="es" onResolve={vi.fn()} /></form>);

    await user.click(screen.getByRole("button", { name: "Tirar 1D6" }));

    expect(submit).not.toHaveBeenCalled();
  });
});
