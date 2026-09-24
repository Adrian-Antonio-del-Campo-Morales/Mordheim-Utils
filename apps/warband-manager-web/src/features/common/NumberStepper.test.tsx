import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NumberStepper } from "./NumberStepper";
import { translate } from "../campaign/i18n-core";

describe("validated numeric output", () => {
  it("updates visible and accessible output when the locale changes", () => {
    const onChange = vi.fn();
    const view = (locale: "es" | "en") => <NumberStepper value={2.5} onChange={onChange} label={translate({ key: "availability.common" }, locale)} locale={locale} />;
    const { rerender } = render(view("es"));
    expect(screen.getByRole("status")).toHaveTextContent("2,5");
    expect(screen.getByRole("button", { name: `${translate({ key: "availability.common" }, "es")} +` })).toBeEnabled();
    rerender(view("en"));
    expect(screen.getByRole("status")).toHaveTextContent("2.5");
    expect(screen.getByRole("button", { name: `${translate({ key: "availability.common" }, "en")} +` })).toBeEnabled();
    rerender(view("es"));
    expect(screen.getByRole("status")).toHaveTextContent("2,5");
  });

  it("renders a localized notice and disables actions for invalid imported values", () => {
    render(<NumberStepper value={NaN} onChange={vi.fn()} label={translate({ key: "availability.common" }, "es")} locale="es" />);
    expect(screen.getByRole("status")).toHaveTextContent("Información no disponible");
    for (const button of screen.getAllByRole("button")) expect(button).toBeDisabled();
    expect(document.body).not.toHaveTextContent("NaN");
  });
});
