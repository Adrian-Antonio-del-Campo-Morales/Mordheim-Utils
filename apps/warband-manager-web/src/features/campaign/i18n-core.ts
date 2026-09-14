export type Locale = "es" | "en";

const messages = {
  "knowledge.unavailable": { es: "Información no disponible", en: "Information unavailable" },
  "knowledge.description-unavailable": { es: "No hay una descripción disponible para este elemento.", en: "No description is available for this entry." },
  "knowledge.english-fallback": { es: "EN · traducción pendiente: {text}", en: "{text}" },
  "error.action-failed": { es: "No se pudo completar la acción.", en: "The action could not be completed." },
} as const;

export type UiMessage = { readonly key: keyof typeof messages; readonly args?: Readonly<Record<string, string | number>> };

export function isUiMessageKey(value: unknown): value is keyof typeof messages {
  return typeof value === "string" && value in messages;
}

export function translate(message: UiMessage, locale: Locale): string {
  return messages[message.key][locale].replace(/\{(\w+)\}/g, (_, key: string) => String(message.args?.[key] ?? ""));
}
