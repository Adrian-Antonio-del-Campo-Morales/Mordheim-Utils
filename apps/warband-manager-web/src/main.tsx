import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import { App } from "./App";

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root container #root not found in index.html");
}

const explainDisabledControls = () => {
  document.querySelectorAll<HTMLElement>("button, input, select").forEach((control) => {
    // Anything carrying the app's own knowledge tooltip must not also grow a
    // native browser `title`: only the app tooltip is shown.
    if (control.closest("[data-tooltip]")) {
      control.removeAttribute("title");
      return;
    }
    const disabled = control.matches(":disabled");
    if (disabled && control.dataset.disabledReason) {
      control.removeAttribute("title");
      control.dataset.disabledTooltip = control.dataset.disabledReason;
      control.setAttribute("aria-description", control.dataset.disabledReason);
    } else if (control.dataset.disabledTooltip) {
      control.removeAttribute("aria-description");
      delete control.dataset.disabledTooltip;
    }
  });
};

new MutationObserver(explainDisabledControls).observe(container, { attributes: true, childList: true, subtree: true, attributeFilter: ["disabled", "data-disabled-reason"] });

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
