import { act, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it, vi } from "vitest";

import { OperationProgress } from "@src/features/common/OperationProgress";
import { reportOperation, withOperationProgress } from "@src/features/common/operationProgressEvents";

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

  it("gives the progress indicator a paint opportunity before starting work", async () => {
    vi.useFakeTimers();
    const operation = vi.fn(async () => "done");
    const pending = withOperationProgress(operation);
    expect(operation).not.toHaveBeenCalled();
    await vi.runAllTimersAsync();
    await expect(pending).resolves.toBe("done");
    vi.useRealTimers();
  });
});
