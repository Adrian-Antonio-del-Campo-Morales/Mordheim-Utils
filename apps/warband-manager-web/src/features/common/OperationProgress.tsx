import { useEffect, useState } from "react";

const OPERATION_EVENT = "warband-manager:operation";

export function reportOperation(started: boolean): void {
  window.dispatchEvent(new CustomEvent<number>(OPERATION_EVENT, { detail: started ? 1 : -1 }));
}

export async function withOperationProgress<T>(operation: () => Promise<T>): Promise<T> {
  reportOperation(true);
  try {
    // Let React paint the progress layer before a synchronous application
    // action starts doing catalogue or campaign work on the main thread.
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    return await operation();
  } finally {
    reportOperation(false);
  }
}

export function OperationProgress({ locale }: { locale: "es" | "en" }) {
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const update = (event: Event) => setPending((current) => Math.max(0, current + (event as CustomEvent<number>).detail));
    window.addEventListener(OPERATION_EVENT, update);
    return () => window.removeEventListener(OPERATION_EVENT, update);
  }, []);

  if (!pending) return null;
  const label = locale === "es" ? "Procesando…" : "Processing…";
  return <div className="operation-progress" role="status" aria-live="polite" aria-label={label}><span className="operation-spinner" aria-hidden="true" />{label}</div>;
}
