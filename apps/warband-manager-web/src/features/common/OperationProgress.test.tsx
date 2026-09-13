import { act, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";

import { OperationProgress, reportOperation } from "./OperationProgress";

describe("OperationProgress", () => {
  it("shows until every overlapping operation finishes", () => {
    render(<OperationProgress locale="es" />);
    expect(screen.queryByRole("status")).toBeNull();

    act(() => { reportOperation(true); reportOperation(true); });
    expect(screen.getByRole("status")).toHaveTextContent("Procesando…");

    act(() => reportOperation(false));
    expect(screen.getByRole("status")).toBeInTheDocument();

    act(() => reportOperation(false));
    expect(screen.queryByRole("status")).toBeNull();
  });
});
