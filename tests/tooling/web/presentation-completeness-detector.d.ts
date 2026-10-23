/**
 * Ambient types for the plain-ESM detector (`tools/web/presentation-completeness-
 * detector.mjs`) imported by the TS completeness tests. The declaration covers
 * only what those tests use; the detector itself remains a JS tool with no build
 * step.
 */
declare module "*.mjs" {
  export const FINDING_CLASSES: readonly string[];
  export const GENERIC_FALLBACKS: Readonly<Record<"es" | "en", readonly string[]>>;
  export const RAW_MARKERS: readonly string[];
  export const CATEGORY_COMPOSITION: Readonly<Record<string, { readonly allowedIdPrefixes: readonly string[]; readonly bandScoped: boolean }>>;
  export function foldCase(value: unknown): string;
  export function isTranslatedValue(value: unknown): value is string;
  export function isGenericFallback(value: unknown): boolean;
  export function buildIdInventory(artefact: unknown): Set<string>;
  export function classifyVisibleText(value: unknown, context?: Record<string, unknown>): Record<string, unknown> | null;
  export function classifyCategoryRow(row: unknown, context?: Record<string, unknown>): Record<string, unknown> | null;
}
