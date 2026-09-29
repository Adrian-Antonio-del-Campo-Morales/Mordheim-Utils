/**
 * Dynamic visible-completeness detector — the shared classifier for the
 * completeness layer of `check-presentation` (step 5).
 *
 * This module is deliberately pure: no I/O, no artefact knowledge, no React.
 * The dynamic audit (tests/web/tools/presentation-completeness-sweep.test.tsx)
 * loads the real generated artefacts through the maintained helpers and renders
 * the real consumers; every visible value it captures is classified here with
 * the context of its surface (locale, published translations, id inventory,
 * category composition).
 *
 * Policy (docs/reference/web-presentation.md, "Visible completeness"):
 * for published data and supported formats, every visible text must resolve to
 * real, localized content. A generic fallback visible to a person is a defect.
 * There are no allowlists, exclusions or suppressions in this detector.
 *
 * The detector is a complement, never a replacement: the static/flow/type
 * detectors of `presentation-audit.mjs` keep running before it, and their
 * findings are reported separately.
 */

/** Finding classes of the dynamic completeness layer. */
export const FINDING_CLASSES = Object.freeze([
  "raw-text",
  "technical-id",
  "wrong-locale",
  "generic-fallback",
  "missing-presentation-entry",
  "unexpected-row-in-category",
  "unsupported-document-rendered",
]);

/**
 * The reader's branded unavailable notice per locale
 * (`packages/typescript/adapters/knowledge-reader/presentation.ts`,
 * `unavailableText`). Both locales are always checked: showing the English
 * notice inside a Spanish view is the same defect.
 */
export const GENERIC_FALLBACKS = Object.freeze({
  es: Object.freeze(["Información no disponible"]),
  en: Object.freeze(["Information unavailable"]),
});

/**
 * Controlled markers the presentation contract reserves for tests and pending
 * editorial work. Reaching a visible surface at runtime is a raw-text leak.
 */
export const RAW_MARKERS = Object.freeze(["TODO-TRANSLATE", "RAW_KB_POISON_"]);

/**
 * Composition of the browsable rules categories (`RulesCatalogue.rawRows`).
 * "special-rules" is the shared catalogue: exactly the rules promoted into it
 * by the generator (`shared-rule.*`), never a band-local copy. Band rules live
 * in "band-rules" / "profile-special-rules".
 */
export const CATEGORY_COMPOSITION = Object.freeze({
  "special-rules": Object.freeze({ allowedIdPrefixes: Object.freeze(["shared-rule."]), bandScoped: false }),
});

/**
 * Every id the artefacts publish (bands, profiles, items, skills, rules and
 * presentation-entry references), for the technical-id comparison.
 *
 * @param {object} artefact the merged artefact (readArtefactDocument shape).
 * @returns {Set<string>} the id inventory.
 */
export function buildIdInventory(artefact) {
  const inventory = new Set();
  const add = (value) => { if (typeof value === "string" && value) inventory.add(value); };
  for (const row of artefact.bands ?? []) add(row.id);
  for (const row of artefact.profiles ?? []) add(row.id);
  for (const row of artefact.skills ?? []) add(row.id);
  for (const row of artefact.items ?? []) add(row.item_id);
  for (const stem of Object.keys(artefact.rules_prose ?? {})) for (const row of artefact.rules_prose[stem]) add(row.id);
  for (const entry of artefact.presentation_entries ?? []) add(entry.ref?.id);
  return inventory;
}

/** Case- and accent-insensitive comparison key. */
export function foldCase(value) {
  return String(value).normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase().trim();
}

/** A published value that can be shown: non-empty, not a pending/raw marker. */
export function isTranslatedValue(value) {
  return typeof value === "string" && Boolean(value.trim()) && !RAW_MARKERS.some((marker) => value.includes(marker));
}

/** True when the value is the generic unavailable notice of any locale. */
export function isGenericFallback(value) {
  const folded = foldCase(value);
  return Object.values(GENERIC_FALLBACKS).flat().some((candidate) => foldCase(candidate) === folded);
}

/**
 * The separators a composed visible text is built from: line breaks and the
 * catalogue's punctuation (`". "` label joins, ` · ` chips, `• ` bullets and
 * ` — ` table rows). They delimit the fragment a value carries, so a fallback
 * glued to a label (`Autor: …`, `5+ …`, `Dificultad …`) is still its own
 * fragment and cannot hide behind the surrounding text.
 */
const FRAGMENT_DELIMITERS = Object.freeze(["\n", " · ", " • ", "• ", ": ", " — "]);

/**
 * The fragment of `text` around a match at `[start, end)`: the run of text
 * between the nearest delimiter before and the nearest delimiter after it.
 */
function fragmentAround(text, start, end) {
  let begin = 0;
  for (const delimiter of FRAGMENT_DELIMITERS) {
    const at = text.lastIndexOf(delimiter, start - 1);
    if (at >= 0) begin = Math.max(begin, at + delimiter.length);
  }
  let finish = text.length;
  for (const delimiter of FRAGMENT_DELIMITERS) {
    const at = text.indexOf(delimiter, end);
    if (at >= 0) finish = Math.min(finish, at);
  }
  return text.slice(begin, finish).trim();
}

/**
 * Every generic fallback embedded in a composed text, as the fragment that
 * carries it. Exact-match detection cannot see a notice joined to a label, a
 * bullet or a die result, which is exactly how the reader's notice used to hide
 * inside a composed scenario, note, loot line or difficulty chip.
 *
 * @param {unknown} value the visible text.
 * @returns {string[]} the delimiting fragments that contain a fallback.
 */
export function genericFallbackFragments(value) {
  if (typeof value !== "string" || !value) return [];
  const lower = value.toLocaleLowerCase();
  const fragments = [];
  for (const phrase of Object.values(GENERIC_FALLBACKS).flat()) {
    const needle = phrase.toLocaleLowerCase();
    if (!needle) continue;
    let from = 0;
    for (;;) {
      const at = lower.indexOf(needle, from);
      if (at < 0) break;
      const fragment = fragmentAround(value, at, at + phrase.length);
      if (fragment && !fragments.includes(fragment)) fragments.push(fragment);
      from = at + needle.length;
    }
  }
  return fragments;
}

/**
 * Dotted/underscored lowercase identifiers (`item.sword`, `shared-rule.fear`,
 * `magical_artefact.x`) never occur in prose. Their segments may themselves
 * carry hyphens (`shared-rule.leader`, `scenario.hidden-treasure.loot.1.1`),
 * and the band-rule grammar is pure kebab with the `--` owner separator
 * (`band--knights-feats`). The shape therefore requires the id character set,
 * a leading letter, an alnum tail, and at least one dot/underscore separator
 * or the `--` grammar — prose ("close-combat", "p. ej.", "3.5") stays outside,
 * and a known id shown bare is still caught through the inventory/reference.
 */
const ID_SHAPE = /^(?=.*(?:[._][a-z0-9]+|--))[a-z][a-z0-9._-]*[a-z0-9]$/;

/**
 * Classify one visible value.
 *
 * @param {unknown} value the visible text (textContent, attribute value,
 *   control value, export line, PDF cell). Empty and whitespace-only values
 *   are nothing visible and never flagged.
 * @param {object} [context] surface context:
 *   - `locale`: "es" | "en" of the view the value was captured in.
 *   - `surface`: free-form surface name (e.g. "rules-catalogue/special-rules").
 *   - `attribute`: when captured from an attribute (aria-label, title, ...).
 *   - `category`: browsable category, when known.
 *   - `ref`: internal reference the value is expected to resolve for; used
 *     only as a diagnostic and for the name==id / effect==id checks.
 *   - `field`: presentation field ("name", "effect", ...).
 *   - `expected`: the reference or text the value was expected to be.
 *   - `origin`: artefact origin of the row, when known.
 *   - `visible`: false for selection identity (option `value`, React keys,
 *     structural attributes, internal ids) — those are never classified.
 *   - `published`: `{ es?, en? }` translations published for the same
 *     reference, for the wrong-locale comparison.
 *   - `idInventory`: Set of every id the artefacts publish, for the
 *     technical-id check.
 * @returns {object | null} a finding `{ kind, surface, locale, ... }` or null.
 */
export function classifyVisibleText(value, context = {}) {
  if (value == null) return null;
  const text = String(value);
  const found = text.trim();
  if (!found) return null;
  const { locale = "es", surface = "unknown", attribute, category, ref, field, expected, origin, visible = true, published, idInventory } = context;
  // Selection identity and internal ids are not visible text.
  if (!visible) return null;
  const finding = (kind, extra = {}) => ({
    kind,
    surface,
    locale,
    ...(attribute ? { attribute } : {}),
    ...(category ? { category } : {}),
    ...(ref !== undefined ? { ref: typeof ref === "object" ? { ...ref } : ref } : {}),
    ...(field ? { field } : {}),
    found,
    ...(expected !== undefined ? { expected } : {}),
    ...(origin ? { origin } : {}),
    ...extra,
  });
  // 1. Generic fallbacks, in any locale, case/accent-insensitive.
  if (isGenericFallback(found)) return finding("generic-fallback");
  // 1b. A fallback embedded in a composed text (after a label, a bullet, a
  //     die result or inside a chip) is the same defect: report the fragment
  //     that carries it, never the surrounding page text.
  const embedded = genericFallbackFragments(found);
  if (embedded.length) return finding("generic-fallback", { found: embedded[0], fragment: true });
  // 2. Raw persisted text and poison markers.
  if (RAW_MARKERS.some((marker) => found.includes(marker))) return finding("raw-text");
  // 3. Wrong locale: the other locale's published value is shown while this
  //    locale publishes a different, real translation.
  if (published && typeof published === "object") {
    const other = locale === "es" ? "en" : "es";
    const mine = published[locale];
    const theirs = published[other];
    if (
      isTranslatedValue(theirs) && foldCase(theirs) === foldCase(found) &&
      isTranslatedValue(mine) && foldCase(mine) !== foldCase(found)
    ) return finding("wrong-locale", { expected: mine });
  }
  // 4. Technical ids shown as text: a known id, the row's own id in place of
  //    its name/effect, or a dotted/underscored identifier shape.
  if (idInventory && idInventory.has(found)) return finding("technical-id");
  if (ref && typeof ref === "object" && typeof ref.id === "string" && found === ref.id) return finding("technical-id");
  if (ID_SHAPE.test(found)) return finding("technical-id");
  return null;
}

/**
 * Classify one artefact row against its category's declared composition.
 * Locale-independent: the presence of a foreign row is itself the defect.
 *
 * @param {object} row the artefact row (needs `id`; `band_id` optional).
 * @param {object} [context] `{ category, index, origin }`.
 * @returns {object | null} an `unexpected-row-in-category` finding or null.
 */
export function classifyCategoryRow(row, context = {}) {
  const composition = row && typeof row.id === "string" ? CATEGORY_COMPOSITION[context.category] : undefined;
  if (!composition) return null;
  const id = row.id;
  const prefixOk = composition.allowedIdPrefixes.some((prefix) => id.startsWith(prefix));
  const bandScoped = row.band_id != null && row.band_id !== "";
  if (prefixOk && (bandScoped === composition.bandScoped)) return null;
  return {
    kind: "unexpected-row-in-category",
    surface: "rules-catalogue",
    locale: null,
    category: context.category,
    ref: id,
    found: id,
    expected: composition.allowedIdPrefixes.join(" | "),
    origin: context.origin ?? `rules_prose/${context.category}/${context.index ?? "?"}`,
  };
}
