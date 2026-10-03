/**
 * F050 — canonical `campaign.limit.racial-maximum.*` citations in published prose.
 *
 * The canonical KB writes a shared maximum profile as a parenthetical
 * citation, for example «Sisters of Sigmar are Humans and use the Human racial
 * maximum profile (campaign.limit.racial-maximum.human).». The published prose
 * is canonical and keeps the reference; the read model must never show the
 * catalogue id to a reader. This resolver replaces each citation with the
 * profile the catalogue publishes for that id — the localized maximum
 * statline, composed with the same characteristic vocabulary the reference
 * sheet uses for profile cards — or, for an id the catalogue does not publish,
 * with the explicit localized absence label. It never returns the id and never
 * falls back to another language.
 *
 * Only the citation form the canonical corpus writes is interpreted: a
 * parenthesised `campaign.limit.racial-maximum.<key>` id. It is not a general
 * reference interpreter; other `campaign.limit.*` families and other prose
 * conventions are outside this lot and keep their published form.
 */
import type { ArtefactRow } from "../../adapters/knowledge-reader/artefact-types";
import type { ResolvedKbText } from "../../adapters/knowledge-reader/presentation";
import {
  catalogueCharacteristic,
  catalogueCharacteristicKey,
  catalogueCitationText,
  catalogueJoin,
  catalogueLabel,
  cataloguePunctuation,
  type CatalogueLocale,
  type CatalogueText,
} from "./catalogue-text";

/** Published characteristic key → display key, in profile-table order. */
const PROFILE_CHARACTERISTICS = [
  ["movement", "M"],
  ["weapon_skill", "WS"],
  ["ballistic_skill", "BS"],
  ["strength", "S"],
  ["toughness", "T"],
  ["wounds", "W"],
  ["initiative", "I"],
  ["attacks", "A"],
  ["leadership", "Ld"],
] as const;

/** The citation grammar of the canonical prose, captured id part only. */
const CITATION_SOURCE = "\\(campaign\\.limit\\.racial-maximum\\.([a-z0-9][a-z0-9-]*)\\)";
/** Canonical id prefix of the family this lot resolves. */
const CITATION_ID_PREFIX = "campaign.limit.racial-maximum.";
/** Cheapest possible probe before the published rows are read at all. */
const CITATION_PROBE = `(${CITATION_ID_PREFIX}`;

/**
 * One published maximum profile as localized text: every characteristic in
 * profile order. A row that does not publish all nine is an explicit absence,
 * never a partial statline that would bound the missing characteristic
 * wrongly.
 */
function maximumProfile(row: ArtefactRow, locale: CatalogueLocale): CatalogueText {
  const published = row.characteristics;
  const characteristics = published && typeof published === "object" && !Array.isArray(published)
    ? published as Readonly<Record<string, unknown>>
    : {};
  const values = PROFILE_CHARACTERISTICS.map(([key]) => characteristics[key]);
  if (!values.every((value) => typeof value === "number" && Number.isFinite(value))) {
    return catalogueLabel("racial-maximum-not-published", locale);
  }
  return catalogueJoin(
    PROFILE_CHARACTERISTICS.map(([, display], index) => catalogueJoin(
      [catalogueCharacteristicKey(display, locale), catalogueCharacteristic(display, values[index], locale)],
      " ",
    )),
    ", ",
  );
}

/**
 * The published profiles of this family, keyed by canonical id. An id the
 * catalogue publishes twice is not one profile: it is dropped instead of
 * letting an arbitrary last row win, so the citation degrades to the explicit
 * absence label. A row whose id does not belong to this family is ignored.
 */
function publishedProfiles(
  publishedRacialMaximums: () => readonly ArtefactRow[],
  locale: CatalogueLocale,
): ReadonlyMap<string, CatalogueText> {
  const profiles = new Map<string, CatalogueText>();
  const duplicated = new Set<string>();
  for (const row of publishedRacialMaximums()) {
    const id = row.id;
    if (typeof id !== "string" || !id.startsWith(CITATION_ID_PREFIX)) continue;
    if (profiles.has(id)) duplicated.add(id);
    profiles.set(id, maximumProfile(row, locale));
  }
  for (const id of duplicated) profiles.delete(id);
  return profiles;
}

/**
 * Replace every canonical limit citation of one already-resolved catalogue
 * text with the linked maximum profile. The published rows are read lazily,
 * so prose without a citation never touches the campaign catalogue.
 */
export function resolveLimitCitations(
  text: ResolvedKbText,
  publishedRacialMaximums: () => readonly ArtefactRow[],
  locale: CatalogueLocale,
): ResolvedKbText | CatalogueText {
  if (!text.includes(CITATION_PROBE)) return text;
  const profiles = publishedProfiles(publishedRacialMaximums, locale);
  // The grammar consumes the citation parentheses with the id; the resolved
  // phrase restores them, so the sentence keeps its original punctuation.
  return catalogueCitationText(text, new RegExp(CITATION_SOURCE, "g"), (key) => catalogueJoin([
    cataloguePunctuation("("),
    profiles.get(`${CITATION_ID_PREFIX}${key}`) ?? catalogueLabel("racial-maximum-not-published", locale),
    cataloguePunctuation(")"),
  ], ""));
}
