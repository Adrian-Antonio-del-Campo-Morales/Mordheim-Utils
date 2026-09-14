import { createContext, useContext } from "react";

import type { Locale, UiMessage } from "./i18n-core";

export const I18nContext = createContext<{ readonly locale: Locale; readonly t: (message: UiMessage) => string } | null>(null);

/** Shared language seam for new UI; static chrome migrates here instead of component-local dictionaries. */
export function useI18n(): { readonly locale: Locale; readonly t: (message: UiMessage) => string } {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}
