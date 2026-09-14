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

export { OPERATION_EVENT };
