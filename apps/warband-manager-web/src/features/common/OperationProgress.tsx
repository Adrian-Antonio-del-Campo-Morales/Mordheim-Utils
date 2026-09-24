import { translate } from "../campaign/i18n-core";
import { presentationOutput } from "../campaign/presentation-output";
import { useEffect, useState } from "react";

import { OPERATION_EVENT } from "./operationProgressEvents";

export function OperationProgress({ locale }: { locale: "es" | "en" }) {
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const update = (event: Event) => setPending((current) => Math.max(0, current + (event as CustomEvent<number>).detail));
    window.addEventListener(OPERATION_EVENT, update);
    return () => window.removeEventListener(OPERATION_EVENT, update);
  }, []);

  if (!pending) return null;
  const label = translate({ key: "ui.fcad3ddee56a" }, locale);
  return <div className="operation-progress" role="status" aria-live="polite" aria-label={presentationOutput(label)}><span className="operation-spinner" aria-hidden="true" />{presentationOutput(label)}</div>;
}
