/**
 * Self-tests of the dynamic visible-completeness detector: the negative cases
 * (the detector must flag) and the positive cases (it must not flag) required
 * by the 2A2B plan. These run inside `check:presentation` (step 1), before the
 * static and dynamic audits, with node:test like their siblings.
 *
 * The detector is the shared classifier for every completeness layer: the
 * catalogue/prose/tooltip sweeps and the rendered sweeps. If it cannot
 * demonstrate each required detection here, the whole dynamic layer is blind.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { classifyVisibleText, classifyCategoryRow, CATEGORY_COMPOSITION, FINDING_CLASSES } from "../../../tools/web/presentation-completeness-detector.mjs";

const ES = { locale: "es", surface: "test/es" };
const EN = { locale: "en", surface: "test/en" };

// ---------------------------------------------------------------------------
// Negative cases: every problem class must be detected.
// ---------------------------------------------------------------------------

test("flags a name equal to its id (technical-id)", () => {
  const finding = classifyVisibleText("shared-rule.fear", { ...ES, field: "name", ref: { kind: "rule", id: "shared-rule.fear" } });
  assert.equal(finding?.kind, "technical-id");
  assert.equal(finding.found, "shared-rule.fear");
  assert.equal(finding.locale, "es");
});

test("flags an effect equal to its id (technical-id)", () => {
  const finding = classifyVisibleText("skill.acrobatics", { ...EN, field: "effect", ref: { kind: "skill", id: "skill.acrobatics" } });
  assert.equal(finding?.kind, "technical-id");
  assert.equal(finding.field, "effect");
});

test("flags English text shown in the ES locale when a translation exists (wrong-locale)", () => {
  const finding = classifyVisibleText("Fear", { ...ES, field: "name", published: { es: "Miedo", en: "Fear" } });
  assert.equal(finding?.kind, "wrong-locale");
  assert.equal(finding.expected, "Miedo");
});

test("flags Spanish text shown in the EN locale when a translation exists (wrong-locale)", () => {
  const finding = classifyVisibleText("Miedo", { ...EN, field: "name", published: { es: "Miedo", en: "Fear" } });
  assert.equal(finding?.kind, "wrong-locale");
  assert.equal(finding.expected, "Fear");
});

test("flags the Spanish generic fallback (generic-fallback)", () => {
  const finding = classifyVisibleText("Información no disponible", ES);
  assert.equal(finding?.kind, "generic-fallback");
  // Accent/case-insensitive on purpose: the defect is the fallback, not its typography.
  assert.equal(classifyVisibleText("informacion No disponible", ES)?.kind, "generic-fallback");
});

test("flags the English generic fallback in either locale (generic-fallback)", () => {
  assert.equal(classifyVisibleText("Information unavailable", EN)?.kind, "generic-fallback");
  // The English notice inside a Spanish view is the same defect.
  assert.equal(classifyVisibleText("Information unavailable", ES)?.kind, "generic-fallback");
});

test("flags raw persisted text and poison markers (raw-text)", () => {
  assert.equal(classifyVisibleText("TODO-TRANSLATE: effect of item.rare-gem", ES)?.kind, "raw-text");
  assert.equal(classifyVisibleText("RAW_KB_POISON_profile_name", EN)?.kind, "raw-text");
});

test("flags a pending injury-table translation inside a composed result row (raw-text)", () => {
  // The serious-injury results used to reach the catalogue as `11-15 — TODO-TRANSLATE`.
  assert.equal(classifyVisibleText("11-15 — TODO-TRANSLATE", { ...ES, category: "injuries", field: "result" })?.kind, "raw-text");
  assert.equal(classifyVisibleText("22 — TODO-TRANSLATE: Leg Wound", { ...ES, category: "injuries", field: "name" })?.kind, "raw-text");
});

// Each visible family the dynamic layer must never accept as "complete": a
// fallback glued to a label, a bullet, a die result or a chip. Exact-match
// detection missed all of them; fragment detection must flag each one and name
// the fragment that carries it, never the surrounding composed text.
test("flags a generic fallback embedded in a composed value, per family", () => {
  const cases = [
    ["Autor: Información no disponible", ES],
    ["Autor: Information unavailable", EN],
    ["Notas: Información no disponible", ES],
    ["• 5+ Información no disponible", ES],
    ["• 4+ Information unavailable", EN],
    ["Nigromancia · Dificultad Información no disponible", ES],
    ["Lesser Magic · difficulty Information unavailable", EN],
    ["Fear\nAutor: Información no disponible", ES],
  ];
  for (const [text, context] of cases) {
    const finding = classifyVisibleText(text, context);
    assert.equal(finding?.kind, "generic-fallback", `not flagged: ${text}`);
    assert.ok(finding.found === "Información no disponible" || finding.found === "Information unavailable" || finding.found.endsWith("Información no disponible") || finding.found.endsWith("Information unavailable"), `fragment not tight: ${finding.found}`);
    assert.ok(!finding.found.includes("\n"), `fragment crossed a line: ${finding.found}`);
  }
});

test("flags a problem inside an aria-label (attribute context)", () => {
  const finding = classifyVisibleText("Información no disponible", { ...ES, attribute: "aria-label", surface: "test/attribute" });
  assert.equal(finding?.kind, "generic-fallback");
  assert.equal(finding.attribute, "aria-label");
});

test("flags a problem inside a tooltip (attribute context)", () => {
  const finding = classifyVisibleText("TODO-TRANSLATE", { ...ES, attribute: "data-tooltip", surface: "test/tooltip" });
  assert.equal(finding?.kind, "raw-text");
  assert.equal(finding.attribute, "data-tooltip");
});

test("flags a band-local row appearing inside the shared rules category (unexpected-row-in-category)", () => {
  const finding = classifyCategoryRow({ id: "abomination--fear", band_id: "necrarchs-mou", names: { es: "Miedo", en: "Fear" } }, { category: "special-rules", index: 68, origin: "rules_prose/special-rules/68" });
  assert.equal(finding?.kind, "unexpected-row-in-category");
  assert.equal(finding.category, "special-rules");
  assert.equal(finding.ref, "abomination--fear");
  assert.equal(finding.expected, "shared-rule.");
  // The 68 real shared rows pass the composition check.
  assert.equal(classifyCategoryRow({ id: "shared-rule.fear" }, { category: "special-rules", index: 0 }), null);
});

// ---------------------------------------------------------------------------
// Positive cases: legitimate surfaces must not be flagged.
// ---------------------------------------------------------------------------

test("does not flag ids used only as internal identity (invisible)", () => {
  // visible: false is the option-value / React key / structural attribute case.
  assert.equal(classifyVisibleText("shared-rule.fear", { ...ES, visible: false }), null);
  assert.equal(classifyVisibleText("Información no disponible", { ...ES, visible: false }), null);
  // Empty or whitespace-only text is nothing visible.
  assert.equal(classifyVisibleText("   ", ES), null);
  assert.equal(classifyVisibleText(null, ES), null);
});

test("does not flag technical control values that are not visible text", () => {
  // A select whose option value is the id is identity; the captured value of
  // such a control is classified with visible: false by the sweep.
  assert.equal(classifyVisibleText("item.mirror-of-yth", { ...EN, visible: false, surface: "test/select-value" }), null);
  // Prose that merely contains hyphenated words is not id-shaped evidence.
  assert.equal(classifyVisibleText("A close-combat weapon grants +1 Strength", EN), null);
});

test("does not flag correctly resolved ES and EN text", () => {
  const published = { es: "Miedo", en: "Fear" };
  assert.equal(classifyVisibleText("Miedo", { ...ES, field: "name", published, ref: { kind: "rule", id: "shared-rule.fear" } }), null);
  assert.equal(classifyVisibleText("Fear", { ...EN, field: "name", published, ref: { kind: "rule", id: "shared-rule.fear" } }), null);
  // Real effects, both locales.
  assert.equal(classifyVisibleText("Las Abominaciones son criaturas retorcidas y repulsivas que causan Miedo.", ES), null);
  assert.equal(classifyVisibleText("Abominations are twisted and repulsive looking creatures, which cause Fear.", EN), null);
});

test("does not flag the localized difficulty value or other real chip text", () => {
  // `difficulty: auto` is a published semantic value, labelled in place.
  assert.equal(classifyVisibleText("Nigromancia · Dificultad Automática", ES), null);
  assert.equal(classifyVisibleText("Lesser Magic · difficulty Automatic", EN), null);
});

test("does not flag resolved loot, note, author or condition fragments", () => {
  // The composed scenario and roster texts the six families used to leak into.
  assert.equal(classifyVisibleText("Autor: Tuomas Pirinen", ES), null);
  assert.equal(classifyVisibleText("Notas: El escenario se juega de noche.", ES), null);
  assert.equal(classifyVisibleText("• 5+ Fragmento de piedra bruja", ES), null);
  assert.equal(classifyVisibleText("Herido (Herida en la Pierna)", ES), null);
  assert.equal(classifyVisibleText("Injured (Leg Wound)", EN), null);
});

test("does not flag the specific unknown-reference notice", () => {
  // A stored label the KB cannot recognize is a structured absence, not a
  // generic fallback: the reader names it specifically in both locales.
  assert.equal(classifyVisibleText("La referencia no está reconocida en la base de conocimiento.", ES), null);
  assert.equal(classifyVisibleText("The reference is not recognized in the knowledge base.", EN), null);
});

test("does not flag specific localized error or absence messages", () => {
  // The product's own absence notices (i18n-core "knowledge.description-absent")
  // and the reader's localized rejection messages are specific, not fallbacks.
  assert.equal(classifyVisibleText("No hay una descripción disponible para este elemento.", ES), null);
  assert.equal(classifyVisibleText("No description is available for this entry.", EN), null);
  assert.equal(
    classifyVisibleText("Este archivo usa un formato retirado (versión 4). Solo se admite la versión 5 y no hay migración automática.", ES),
    null,
  );
  // A locale whose published translation equals the shown text is correct.
  assert.equal(classifyVisibleText("Miedo", { ...ES, published: { es: "Miedo", en: "Fear" } }), null);
});

// ---------------------------------------------------------------------------
// Contract: the finding classes the tool reports, verbatim.
// ---------------------------------------------------------------------------

test("declares exactly the seven finding classes of the plan", () => {
  assert.deepEqual([...FINDING_CLASSES], [
    "raw-text",
    "technical-id",
    "wrong-locale",
    "generic-fallback",
    "missing-presentation-entry",
    "unexpected-row-in-category",
    "unsupported-document-rendered",
  ]);
  assert.deepEqual(Object.keys(CATEGORY_COMPOSITION), ["special-rules"]);
});
