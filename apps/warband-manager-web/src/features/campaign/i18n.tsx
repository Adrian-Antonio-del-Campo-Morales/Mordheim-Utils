import { translate, type Locale } from "./i18n-core";
import { I18nContext } from "./i18n-context";

export type { Locale, UiMessage } from "./i18n-core";

export function I18nProvider({ locale, children }: { readonly locale: Locale; readonly children: React.ReactNode }) {
  return <I18nContext.Provider value={{ locale, t: (message) => translate(message, locale) }}>{children}</I18nContext.Provider>;
}
