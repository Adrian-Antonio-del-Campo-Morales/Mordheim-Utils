import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import { App } from "./App";

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root container #root not found in index.html");
}

const disabledReason = "Acción no disponible: completa los campos obligatorios o los pasos anteriores.";
const explainDisabledControls = () => {
  document.querySelectorAll<HTMLElement>("button, input, select").forEach((control) => {
    // Anything carrying the app's own knowledge tooltip must not also grow a
    // native browser `title`: only the app tooltip is shown.
    if (control.closest("[data-tooltip]")) {
      control.removeAttribute("title");
      return;
    }
    const disabled = control.matches(":disabled");
    if (disabled) {
      const reason = control.dataset.disabledReason || disabledReason;
      control.removeAttribute("title");
      control.dataset.disabledTooltip = reason;
      control.setAttribute("aria-description", reason);
    } else if (control.dataset.disabledTooltip) {
      control.removeAttribute("aria-description");
      delete control.dataset.disabledTooltip;
    }
  });
};

new MutationObserver(explainDisabledControls).observe(container, { attributes: true, childList: true, subtree: true, attributeFilter: ["disabled"] });

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
