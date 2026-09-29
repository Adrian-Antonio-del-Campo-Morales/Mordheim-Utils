/**
 * Dynamic visible-completeness audit — step 5 of `check-presentation`.
 *
 * Complementary to the static/flow/type gates (`presentation-audit.mjs`): the
 * static detectors prove how text reaches the GUI; this layer executes the real
 * consumers against the real generated artefacts and classifies what is
 * actually visible. Policy: for published data and supported formats every
 * visible text must resolve to real, localized content — a generic fallback
 * visible to a person is a defect (`docs/reference/web-presentation.md`,
 * "Visible completeness"). No allowlists, exclusions or suppressions.
 *
 * Layers, all classified with the shared detector
 * (`presentation-completeness-detector.mjs`):
 * 1. Rules catalogue through the real `RulesCatalogue` read model, both
 *    locales, every browsable category — the "Reglas compartidas" regression.
 * 2. Table localization: every published prose row resolved in both locales
 *    through the reader, compared against its published translations.
 * 3. Accessible tooltips: `knowledgeHintDetails` for every catalogue entry.
 * 4. Rendered surfaces: the dynamic sweep test (`tests/web/tools/
 *    presentation-completeness-sweep.test.tsx`) renders the rules page and all
 *    categories, the band picker, band construction, equipment/market, a loaded
 *    campaign, history, advances and the PDF text model against the real
 *    artefacts, and rejects supported campaign formats before render. Its
 *    findings are parsed here from vitest's JSON reporter and merged.
 *
 * Findings of this layer never mix with the static report's 700+ findings:
 * they are written to `gui-text-completeness.{json,md}` and exit non-zero when
 * at least one problem exists, even if every static gate is green.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { publishedArtefact } from "./load-kb-artefact.mjs";
import { classifyVisibleText, classifyCategoryRow, FINDING_CLASSES } from "./presentation-completeness-detector.mjs";

const TOOL_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(TOOL_DIR, "..", "..");
const ARTEFACT_DIR = resolve(REPO_ROOT, "outputs", "web-public", "knowledge");
const SWEEP_TEST = resolve(REPO_ROOT, "tests", "web", "tools", "presentation-completeness-sweep.test.tsx");

/** The catalogue categories whose rows resolve as prose rules. */
const RULE_STEMS = [["special-rules", "special-rules"], ["profile-special-rules", "band-rules"], ["conditions", "conditions"], ["core-combat", "core-rules"]];

/** Import a TS file through the loader's hooks (it installs them lazily). */
function tsImport(path) {
  return import(pathToFileURL(path).href);
}

/** Full reader over the merged artefact (hooks already installed). */
async function readerOf(artefact) {
  const adapters = await tsImport(resolve(REPO_ROOT, "packages", "typescript", "adapters", "knowledge-reader", "index.ts"));
  return adapters.ArtefactKnowledgeReader.from(artefact);
}

function idInventoryOf(artefact) {
  const inventory = new Set();
  for (const row of artefact.bands ?? []) if (typeof row.id === "string") inventory.add(row.id);
  for (const row of artefact.profiles ?? []) if (typeof row.id === "string") inventory.add(row.id);
  for (const row of artefact.skills ?? []) if (typeof row.id === "string") inventory.add(row.id);
  for (const row of artefact.items ?? []) if (typeof row.item_id === "string") inventory.add(row.item_id);
  for (const stem of Object.keys(artefact.rules_prose ?? {})) for (const row of artefact.rules_prose[stem]) if (typeof row.id === "string") inventory.add(row.id);
  for (const entry of artefact.presentation_entries ?? []) if (typeof entry.ref?.id === "string") inventory.add(entry.ref.id);
  return inventory;
}

/**
 * Catalogue audit: the real `RulesCatalogue` over the merged artefact, every
 * category, both locales. Uses the reader and read model the product uses —
 * transpiled through the loader's hooks, not a mock.
 */
export async function auditRulesCatalogue(artefact) {
  const reader = await readerOf(artefact);
  const catalogueModule = await tsImport(resolve(REPO_ROOT, "packages", "typescript", "application", "rules", "rules-catalogue.ts"));
  const catalogue = new catalogueModule.RulesCatalogue(reader);
  const inventory = idInventoryOf(artefact);
  const findings = [];
  const categories = catalogueModule.CATEGORY_ORDER ?? ["special-rules", "band-rules", "conditions", "core-rules", "skills", "equipment", "spells", "scenarios", "injuries"];
  for (const categoryId of categories) {
    for (const locale of ["es", "en"]) {
      let entries;
      try {
        entries = catalogue.entries(categoryId, locale);
      } catch (error) {
        findings.push({ kind: "missing-presentation-entry", surface: `rules-catalogue/${categoryId}`, locale, category: categoryId, found: String(error), expected: "readable entries", origin: "rules-catalogue" });
        continue;
      }
      for (const [index, entry] of entries.entries()) {
        const publishedName = artefact.display_names?.[entry.entry_id];
        for (const [field, text, published] of [["name", entry.name, publishedName], ["effect", entry.effect, artefact.display_effects?.[entry.entry_id]]]) {
          const finding = classifyVisibleText(text, {
            locale,
            surface: `rules-catalogue/${categoryId}`,
            category: categoryId,
            field,
            ref: { kind: "rule", id: entry.entry_id },
            published,
            idInventory: inventory,
            origin: entry.source_refs?.length ? undefined : `rules_prose/${categoryId}`,
          });
          if (finding) findings.push(finding);
        }
        if (index === 0) continue;
      }
    }
    // Composition: declared once per category (locale-independent).
    const rows = RULE_STEMS.find(([stem]) => stem === categoryId) ? artefact.rules_prose?.[categoryId] ?? [] : [];
    for (const [index, row] of rows.entries()) {
      const finding = classifyCategoryRow(row, { category: categoryId, index, origin: `rules_prose/${categoryId}/${index}` });
      if (finding) findings.push(finding);
    }
  }
  return { surface: "rules-catalogue", findings };
}

/**
 * Table localization audit: every prose row of the shared documents must
 * resolve name and effect in both locales through the reader, and the resolved
 * text must be the published translation (wrong-locale), a real id (technical-id)
 * or nothing (missing-presentation-entry). Rows already condemned by the
 * category composition are skipped so each defect is counted once.
 */
export async function auditTableLocalization(artefact) {
  const reader = await readerOf(artefact);
  const inventory = idInventoryOf(artefact);
  const findings = [];
  for (const [stem, category] of RULE_STEMS) {
    const rows = artefact.rules_prose?.[stem] ?? [];
    for (const [index, row] of rows.entries()) {
      // Composition-condemned rows are counted once by the catalogue layer.
      if (classifyCategoryRow(row, { category, index })) continue;
      const ref = { kind: "rule", id: String(row.id), ...(typeof row.band_id === "string" ? { bandId: row.band_id } : {}) };
      for (const locale of ["es", "en"]) {
        for (const field of ["name", "effect"]) {
          // The real consumer path: the reader binds the row object to its
          // presentation entry through `recordText` (source-addressed).
          const resolved = reader.recordText(row, field, locale);
          const published = row[field === "name" ? "names" : "effects"];
          if (!resolved || !resolved.trim() || resolved === reader.recordText({}, field, locale)) {
            // The row's text did not resolve through the index at all.
            const display = artefact[field === "name" ? "display_names" : "display_effects"]?.[String(row.id)]?.[locale];
            findings.push({
              kind: "missing-presentation-entry",
              surface: `prose/${stem}`,
              locale,
              category,
              field,
              ref: { kind: "rule", id: String(row.id) },
              found: "",
              expected: `${locale} ${field}`,
              origin: `rules_prose/${stem}/${index}`,
              ...(display ? { note: "display text exists but no entry resolves this row" } : {}),
            });
            continue;
          }
          const finding = classifyVisibleText(resolved, {
            locale, surface: `prose/${stem}`, category, field, ref,
            published,
            idInventory: inventory,
            origin: `rules_prose/${stem}/${index}`,
          });
          if (finding) findings.push(finding);
        }
      }
    }
  }
  return { surface: "prose-tables", findings };
}

/**
 * Accessible tooltips: every catalogue entry's hint (name + tooltip) must
 * resolve in both locales. This is the KnowledgeHint seam the products render.
 */
export async function auditTooltips(artefact) {
  const reader = await readerOf(artefact);
  const inventory = idInventoryOf(artefact);
  const findings = [];
  const detailsModule = await tsImport(resolve(REPO_ROOT, "apps", "warband-manager-web", "src", "features", "campaign", "KnowledgeHintDetails.ts"));
  const refs = [];
  for (const row of artefact.items ?? []) refs.push({ kind: "item", id: String(row.item_id) });
  for (const row of artefact.skills ?? []) refs.push({ kind: "skill", id: String(row.id) });
  for (const [stem] of RULE_STEMS) for (const row of artefact.rules_prose?.[stem] ?? []) {
    if (classifyCategoryRow(row, { category: stem })) continue;
    const appliesTo = row.applies_to;
    const profileIds = Array.isArray(appliesTo?.profile_ids) ? appliesTo.profile_ids : [];
    refs.push({ kind: "rule", id: String(row.id), ...(profileIds[0] ? { profileId: String(profileIds[0]) } : {}), ...(typeof row.band_id === "string" ? { bandId: row.band_id } : {}) });
  }
  for (const locale of ["es", "en"]) {
    for (const ref of refs) {
      let hint;
      try {
        hint = detailsModule.knowledgeHintDetails({ knowledge: reader, ...ref, locale });
      } catch (error) {
        findings.push({ kind: "missing-presentation-entry", surface: "tooltip", locale, ref, found: String(error), expected: "resolvable hint", origin: "KnowledgeHintDetails" });
        continue;
      }
      for (const [field, text] of [["name", hint.name], ["tooltip", hint.tooltip]]) {
        const finding = classifyVisibleText(text, {
          locale, surface: "tooltip", field,
          ref: { kind: ref.kind, id: ref.id },
          published: artefact[ref.kind === "item" ? "display_names" : "display_names"]?.[ref.id],
          idInventory: inventory,
          origin: "KnowledgeHintDetails",
        });
        if (finding) findings.push(finding);
      }
    }
  }
  return { surface: "tooltips", findings };
}

/**
 * Rendered-surface sweeps: the dynamic test file drives the real components
 * against the real artefacts and emits findings as `PRESENTATION_COMPLETENESS_FINDING`
 * JSON lines on the test process output; it also carries the mandatory
 * "Reglas compartidas" regression, whose assertions fail against the current
 * product (that red is the regression working, not a tool failure). A sweep
 * that cannot run at all is recorded as `sweepError` and fails the audit
 * without inventing per-class findings.
 */
export function runRenderedSweeps() {
  const vitest = resolve(REPO_ROOT, "node_modules", "vitest", "vitest.mjs");
  const outputFile = resolve(REPO_ROOT, "outputs", "web-presentation", "gui-text-completeness-sweep.json");
  const started = Date.now();
  const result = spawnSync(process.execPath, [vitest, "run", SWEEP_TEST, "--reporter=dot"], {
    cwd: resolve(REPO_ROOT, "apps", "warband-manager-web"),
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 64,
    timeout: 15 * 60 * 1000,
    env: { ...process.env, PRESENTATION_COMPLETENESS_OUTPUT: outputFile },
  });
  const output = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
  const findings = [];
  // Findings travel as line-delimited JSON: one per console line, written by
  // the sweep itself so nothing depends on vitest's reporter formatting.
  for (const line of output.split("\n")) {
    if (!line.includes("PRESENTATION_COMPLETENESS_FINDING ")) continue;
    const payload = line.slice(line.indexOf("PRESENTATION_COMPLETENESS_FINDING ") + "PRESENTATION_COMPLETENESS_FINDING ".length).trim();
    try {
      findings.push(JSON.parse(payload));
    } catch {
      findings.push({ kind: "raw-text", surface: "sweep", locale: null, found: payload.slice(0, 200), expected: "parseable finding JSON", origin: "sweep-reporter" });
    }
  }
  let summary = null;
  try {
    // The sweep writes its own results file (test titles + outcomes + failure
    // titles), so the audit never parses vitest reporter internals.
    const parsed = JSON.parse(readFileSync(outputFile, "utf8"));
    summary = {
      total: Array.isArray(parsed.tests) ? parsed.tests.length : 0,
      passed: Array.isArray(parsed.tests) ? parsed.tests.filter((test) => test.status === "passed").length : 0,
      failed: Array.isArray(parsed.tests) ? parsed.tests.filter((test) => test.status === "failed").length : 0,
      failures: Array.isArray(parsed.tests) ? parsed.tests.filter((test) => test.status === "failed").map((test) => ({ title: test.title, message: String(test.message ?? "").slice(0, 600) })) : [],
    };
  } catch {
    summary = null;
  }
  const status = summary ? (summary.failed > 0 ? "failed-tests" : "ok") : "crashed";
  return {
    findings,
    summary,
    status,
    sweepError: status === "crashed" ? `${result.stderr ?? ""}`.slice(0, 800) : undefined,
    elapsedMs: Date.now() - started,
  };
}

/** Run every layer; returns `{ layers, findings }` in stable report order. */
export async function auditCompleteness() {
  const artefact = await publishedArtefact();
  if (!artefact) return { layers: [{ surface: "artefact", findings: [{ kind: "missing-presentation-entry", surface: "artefact", locale: null, found: "outputs/web-public/knowledge/knowledge-web.json", expected: "generated artefact", origin: "generate_knowledge_web.py" }] }], findings: [] };
  const layers = [];
  layers.push(await auditRulesCatalogue(artefact));
  layers.push(await auditTableLocalization(artefact));
  layers.push(await auditTooltips(artefact));
  const rendered = runRenderedSweeps();
  layers.push({ surface: "rendered-surfaces", findings: rendered.findings, summary: rendered.summary, status: rendered.status, sweepError: rendered.sweepError, elapsedMs: rendered.elapsedMs });
  const findings = layers.flatMap((layer) => layer.findings);
  return { layers, findings, sweep: { status: rendered.status, summary: rendered.summary, sweepError: rendered.sweepError } };
}

const CLASS_TITLES = {
  "generic-fallback": "Fallback genérico visible",
  "raw-text": "Texto crudo o marcador en superficie visible",
  "technical-id": "Identificador técnico mostrado como texto",
  "wrong-locale": "Texto en el locale equivocado",
  "missing-presentation-entry": "Fila publicada sin entrada de presentación resoluble",
  "unexpected-row-in-category": "Fila fuera de la composición declarada de su categoría",
  "unsupported-document-rendered": "Formato no soportado renderizado (o barrido no concluyente)",
};

function cell(value) {
  return String(value ?? "—").replaceAll("|", "\\|").replace(/\r?\n/g, " ").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

/** Stable markdown report next to the existing static reports. */
export function buildCompletenessReport(result) {
  const counts = new Map();
  for (const finding of result.findings) counts.set(finding.kind, (counts.get(finding.kind) ?? 0) + 1);
  const lines = [
    "# Auditoría dinámica de completitud visible",
    "",
    `${result.findings.length} hallazgos dinámicos. Esta capa ejecuta los consumidores reales contra los artefactos generados reales y clasifica lo visible; es complementaria a la auditoría estática (gui-text-audit-deep), cuyos hallazgos no se mezclan aquí. Un fallback genérico visible es un defecto, también para referencias desconocidas, datos antiguos, traducciones ausentes o filas sin índice de presentación: esos casos exigen mensaje específico, migración o rechazo del documento, no el fallback.`,
    "",
    "## Resumen",
    "",
    ...FINDING_CLASSES.map((kind) => `- ${kind}: ${counts.get(kind) ?? 0}`),
    "",
    "## Hallazgos",
    "",
    "| Clase | Superficie | Locale | Categoría | Referencia (diagnóstico) | Texto encontrado | Referencia esperada | Origen |",
    "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ...result.findings.map((finding) => `| ${cell(CLASS_TITLES[finding.kind] ?? finding.kind)} | ${cell(finding.surface)} | ${cell(finding.locale)} | ${cell(finding.category)} | ${cell(finding.ref && typeof finding.ref === "object" ? finding.ref.id : finding.ref)} | ${cell(finding.found)} | ${cell(finding.expected)} | ${cell(finding.origin)} |`),
    "",
    "## Capas ejecutadas",
    "",
    ...result.layers.map((layer) => {
      const summary = layer.summary ? ` (sweep: ${layer.summary.passed}/${layer.summary.total} pruebas, ${layer.elapsedMs ?? "?"} ms)` : "";
      return `- ${layer.surface}: ${layer.findings.length} hallazgos${summary}`;
    }),
    "",
    "Interpretación y resolución por clase: docs/reference/web-presentation.md, sección «Visible completeness». Reproducción: `python tools/mordheim-utils.py check-presentation` (paso 5) o `npm run audit:completeness` en apps/warband-manager-web.",
    "",
  ];
  return lines.join("\n");
}

/** CLI entry: write reports, exit non-zero on any finding. */
export async function main() {
  const result = await auditCompleteness();
  const output = resolve(REPO_ROOT, "outputs", "web-presentation", "gui-text-completeness.json");
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, JSON.stringify({ generatedAt: new Date().toISOString(), findings: result.findings, layers: result.layers.map(({ surface, findings, summary, elapsedMs }) => ({ surface, count: findings.length, ...(summary ? { summary, elapsedMs } : {}) })) }, null, 2) + "\n");
  writeFileSync(output.replace(/\.json$/, ".md"), buildCompletenessReport(result));
  const counts = new Map();
  for (const finding of result.findings) counts.set(finding.kind, (counts.get(finding.kind) ?? 0) + 1);
  const summary = FINDING_CLASSES.map((kind) => `${kind}=${counts.get(kind) ?? 0}`).join(" ");
  if (result.sweep?.sweepError) console.error(`Rendered sweep could not run: ${result.sweep.sweepError.split("\n")[0]}`);
  console.log(`Completeness audit: ${result.findings.length} dynamic findings (${summary}). ${output}`);
  // The rendered sweep failing to run at all is itself a finding: the gate
  // cannot claim completeness without executing the surfaces.
  if (result.findings.length || result.sweep?.status === "crashed") process.exitCode = 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
