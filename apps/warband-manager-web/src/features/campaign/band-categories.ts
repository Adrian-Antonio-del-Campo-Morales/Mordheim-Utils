/**
 * T11: warband categories offered by the picker, derived from the produced KB
 * artefact rows.
 *
 * The set of categories is data, not a React list: a band publishes its grade
 * (`2a`, `2b`, `1a`, `core`…) inside the Mordheim collection, or belongs to
 * another collection (`trollheim`). Adding a family to the KB therefore
 * publishes a new toggle without touching this application, and no row can be
 * dropped silently — an unknown category is still offered, labelled with the
 * shared unavailable message instead of its internal key.
 *
 * Banned in this module: raw ids as visible text, a hard-coded list of
 * categories to filter with, and any construction or campaign decision.
 */

import { translate, type Locale, type UiMessage } from "./i18n-core";

/** Category identity as the artefact publishes it (a grade or a collection). */
export type BandCategoryKey = string;

/**
 * Localized label per published category. This is translation, not an
 * allow-list: a category missing from this record is still selectable.
 */
const CATEGORY_LABELS = {
  core: "ui.706f7722a9f9",
  "1a": "shell.band-set-1a",
  "1b": "shell.band-set-1b",
  "1c": "shell.band-set-1c",
  "2a": "shell.band-set-2a",
  "2b": "shell.band-set-2b",
  trollheim: "shell.band-set-trollheim",
} as const;

/** Localized message of one category, never the internal key as visible text. */
function categoryMessage(key: BandCategoryKey): UiMessage {
  return Object.hasOwn(CATEGORY_LABELS, key)
    ? { key: CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS] }
    : { key: "knowledge.unavailable" };
}

/**
 * Category one produced band row declares. Mordheim bands are grouped by grade
 * (`2A`/`2B` included); every other collection is its own category. The result
 * is always a string, so a row whose category is missing keeps its own group
 * instead of vanishing from the picker.
 */
export function bandCategoryKey(row: unknown): BandCategoryKey {
  const values = (row ?? {}) as Readonly<Record<string, unknown>>;
  const grade = typeof values.grade === "string" ? values.grade.trim().toLowerCase() : "";
  const collection = typeof values.collection === "string" ? values.collection.trim().toLowerCase() : "";
  if (collection && collection !== "mordheim") return collection;
  return grade;
}

/**
 * Localized label of one category as a presentation value; an unpublished
 * category is never an id leak. Callers keep the type and call `translate` at
 * their own boundary, so provenance never depends on a plain string.
 */
export function bandCategoryMessage(key: BandCategoryKey): UiMessage {
  return categoryMessage(key);
}

export interface BandCategory {
  readonly key: BandCategoryKey;
  /** Untranslated, typed label the consumer resolves with the active locale. */
  readonly label: UiMessage;
}

/** Categories present in the artefact, labelled and ordered by that label. */
export function bandCategoriesOf(rows: readonly unknown[], locale: Locale): readonly BandCategory[] {
  const keys = [...new Set(rows.map((row) => bandCategoryKey(row)))];
  return keys
    .map((key) => ({ key, label: bandCategoryMessage(key) }))
    .sort((left, right) => String(translate(left.label, locale)).localeCompare(String(translate(right.label, locale)), locale, { sensitivity: "base" }));
}

/** Rows whose category is not excluded by the user. */
export function visibleBandsOf(
  rows: readonly Readonly<Record<string, unknown>>[],
  excluded: ReadonlySet<BandCategoryKey>,
): readonly Readonly<Record<string, unknown>>[] {
  return rows.filter((row) => !excluded.has(bandCategoryKey(row)));
}

/**
 * Why the picker shows what it shows. `no-data` means the artefact publishes no
 * band at all; `no-match` means the enabled categories exclude every published
 * band. T11 must never present both as the same empty state.
 */
export type BandPickerState = "ready" | "no-data" | "no-match";

export function bandPickerState(published: number, visible: number): BandPickerState {
  if (published === 0) return "no-data";
  return visible === 0 ? "no-match" : "ready";
}
