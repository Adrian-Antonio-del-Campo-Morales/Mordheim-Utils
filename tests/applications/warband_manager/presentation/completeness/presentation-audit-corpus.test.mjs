/**
 * Regression corpus of the static GUI text audit (tools/web/presentation-audit.mjs).
 *
 * The audit is only useful in CI if both of its error rates stay pinned:
 *   - every LEAK case (a realistic way to put raw ids, KB fields, technical
 *     vocabulary or hard-coded copy on screen) must be flagged, and
 *   - every CONTROL case (correct code using the app's presentation adapters)
 *     must stay clean.
 * Each precision exemption in the audit has at least one adversarial LEAK case
 * next to the CONTROL case it exists for, so an exemption that starts hiding
 * real leaks fails here.
 *
 * All cases live in one virtual fixture served from memory inside the real
 * app (so imports and types resolve exactly as in product code); one case per
 * line, tagged `case:<name>`, so findings map back to cases by line. The
 * fixture is never written to disk.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { auditVirtualFile, inspectHtmlDocument } from "../../../../../tools/web/presentation-audit.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..", "..");
const APP = resolve(REPO, "apps", "warband-manager-web");

const FIXTURE = `import type { ReactNode } from "react";
import { presentationOutput } from "./presentation-output";
import { textNumber, textSymbol } from "./presentation-values";
import { knowledgeName, localizedLabel } from "./displayText";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { Warrior } from "./types";
import { WarriorProfileSummary } from "./WarriorProfileSummary";

export function Corpus({ warrior, knowledge, locale }: { warrior: Warrior; knowledge?: ArtefactKnowledgeReader; locale: "es" | "en" }) {
  return <>
    <span>{warrior.name}</span>{/* case:LEAK-raw-jsx-text */}
    <span>{warrior.profile_id}</span>{/* case:LEAK-raw-id-text */}
    <span title={warrior.profile_id} />{/* case:LEAK-raw-title-attr */}
    <button aria-label={String(warrior.id)} />{/* case:LEAK-raw-aria-label */}
    <span>{\`\${warrior.name} (\${warrior.kind})\`}</span>{/* case:LEAK-template-literal */}
    <p>{warrior.skill_access?.map((key) => key)}</p>{/* case:LEAK-map-raw-strings */}
    <ul>{warrior.equipment.map((e) => <li key={e.item_id}>{e.item_id}</li>)}</ul>{/* case:LEAK-map-into-jsx-raw */}
    <p>{warrior.equipment.length && <b>{presentationOutput(textSymbol("x"))}</b>}</p>{/* case:LEAK-numeric-guard-0 */}
    <p>{warrior.experience && <b>{presentationOutput(textSymbol("x"))}</b>}</p>{/* case:LEAK-numeric-guard-experience */}
    <LeakyLabel label={warrior.id} />{/* case:LEAK-raw-to-project-comp (reported inside LeakyLabel) */}
    <Slot>{warrior.profile_id}</Slot>{/* case:LEAK-raw-into-slot */}
    <Slot>{"hard coded"}</Slot>{/* case:LEAK-literal-into-slot */}
    <WarriorProfileSummary locale={locale} identity={warrior.profile_id} stats={{}} equipment={null} rules={null} />{/* case:LEAK-raw-string-to-slot-prop */}
    <Slot {...{ children: warrior.id }} />{/* case:LEAK-spread-fills-slot-raw */}
    <span>{presentationOutput(warrior.profile_id as any)}</span>{/* case:LEAK-any-cast-laundering */}
    <input value={warrior.profile_id} onChange={() => undefined} />{/* case:LEAK-editable-input-seeded-by-id */}
    <input value={warrior.kind} onChange={() => undefined} />{/* case:LEAK-control-shows-enum */}
    <input value={warrior.name} readOnly />{/* case:LEAK-readonly-shows-raw-name */}
    {(() => { const shown = warrior.profile_id; return <i>{shown}</i>; })()}{/* case:LEAK-local-var-indirect */}
    {(() => { const shown = { [warrior.id]: warrior.profile_id }; return <i>{shown[warrior.id]}</i>; })()}{/* case:LEAK-object-value-raw */}
    <span>{"Equipment"}</span>{/* case:LEAK-hardcoded-literal */}
    <span>Equipment</span>{/* case:LEAK-hardcoded-jsx-text */}
    <input placeholder="Search" />{/* case:LEAK-hardcoded-placeholder */}
    <span data-label={warrior.id} />{/* case:LEAK-visible-data-attr-raw */}
    <span style={warrior.id ? { content: warrior.id } : undefined} />{/* case:LEAK-style-branch-content-raw */}
    {(() => { const el = document.createElement("input"); el.value = warrior.id; return null; })()}{/* case:LEAK-dom-value-write-raw */}
    {(() => { const el = document.createElement("p"); const k = "textContent"; el[k] = warrior.id; return null; })()}{/* case:LEAK-computed-dom-write-raw */}
    {(() => { const show = (key: string) => key; return <p>{(warrior.skill_access ?? []).map(show)}</p>; })()}{/* case:LEAK-map-by-reference-raw */}
    {(() => { const show = (key: string) => <b key={key}>Skill</b>; return <p>{(warrior.skill_access ?? []).map(show)}</p>; })()}{/* case:LEAK-map-by-reference-hardcoded */}
    {(() => { const presentationOutput = (v: string | undefined) => v ?? ""; return <i>{presentationOutput(warrior.profile_id)}</i>; })()}{/* case:LEAK-shadowed-output-adapter */}
    {(() => { const { id: shown } = warrior; return <i>{shown}</i>; })()}{/* case:LEAK-destructured-id-rendered */}
    <SafeLabel label={warrior.id} />{/* case:CONTROL-id-to-safe-component */}
    {(() => { const { quantity: amount } = warrior.equipment[0]; return <b>{presentationOutput(textNumber(amount ?? 0, locale))}</b>; })()}{/* case:CONTROL-destructured-number-first */}
    {(() => { const compute = ({ id: amount }: { id: string }) => amount.length; return <b>{presentationOutput(textNumber(compute(warrior), locale))}</b>; })()}{/* case:CONTROL-same-name-destructures-id-unrendered */}
    <Slot><b>{presentationOutput(textSymbol("x"))}</b></Slot>{/* case:CONTROL-jsx-into-slot */}
    <ul>{warrior.equipment.map((e) => <li key={e.item_id}>{presentationOutput(knowledgeName(knowledge, "item", e.item_id, locale))}</li>)}</ul>{/* case:CONTROL-id-as-key-only */}
    <ul>{[...warrior.equipment].sort((a, b) => a.item_id.localeCompare(b.item_id)).map((e) => <li key={e.item_id}>{presentationOutput(knowledgeName(knowledge, "item", e.item_id, locale))}</li>)}</ul>{/* case:CONTROL-sorted-by-id */}
    <p>{warrior.name && <b>{presentationOutput(textSymbol("x"))}</b>}</p>{/* case:CONTROL-string-guard */}
    <input value={warrior.name} onChange={() => undefined} />{/* case:CONTROL-rename-input-seeded-by-name */}
    {(() => { const el = document.createElement("input"); el.value = ""; return null; })()}{/* case:CONTROL-cleared-value */}
    <span style={warrior.id ? { fontWeight: "bold" } : undefined} />{/* case:CONTROL-style-branches */}
    <span data-kind={warrior.kind} />{/* case:CONTROL-hidden-data-attr */}
    {(() => { const show = (key: string) => <b key={key}>{presentationOutput(localizedLabel(key, locale))}</b>; return <p>{(warrior.skill_access ?? []).map(show)}</p>; })()}{/* case:CONTROL-map-by-reference-safe */}
    {(() => { const render = (key: string) => <b key={key}>{presentationOutput(localizedLabel(key, locale))}</b>; return <p>{(warrior.skill_access ?? []).map(render)}</p>; })()}{/* case:CONTROL-shadowed-callback-safe-first */}
    {(() => { const render = (key: string) => key; return <p>{(warrior.skill_access ?? []).map(render)}</p>; })()}{/* case:LEAK-shadowed-callback-raw-second */}
  </>;
}

function LeakyLabel({ label }: { label: string }) { return <em>{label}</em>; } // case:LEAK-raw-to-project-comp
function SafeLabel({ label }: { label: string }) { return <em>{presentationOutput(knowledgeName(undefined, "item", label, "es"))}</em>; } // case:CONTROL-id-to-safe-component
function Slot({ children }: { children: ReactNode }) { return <div>{children}</div>; } // case:CONTROL-slot-forwards-children
`;

const lines = FIXTURE.split("\n");
const caseOfLine = new Map();
lines.forEach((line, index) => { const match = /case:([\w-]+)/.exec(line); if (match) caseOfLine.set(index + 1, match[1]); });
const cases = [...new Set(caseOfLine.values())];
const findings = auditVirtualFile(APP, "src/features/campaign/__presentation_audit_corpus__.tsx", FIXTURE);
const reasonsOf = (name) => findings.filter((finding) => caseOfLine.get(finding.line) === name).map((finding) => finding.reason);

test("the fixture type-checks (a compiler error would mask what is tested)", () => {
  assert.deepEqual(findings.filter((finding) => finding.reason === "compiler-error"), []);
});

test("every finding belongs to a tagged case (scaffolding stays clean)", () => {
  assert.deepEqual(findings.filter((finding) => !caseOfLine.has(finding.line)), []);
});

for (const name of cases.filter((name) => name.startsWith("LEAK-"))) {
  test(`flags ${name}`, () => assert.ok(reasonsOf(name).length > 0, `${name} was not flagged`));
}
for (const name of cases.filter((name) => name.startsWith("CONTROL-"))) {
  test(`does not flag ${name}`, () => assert.deepEqual(reasonsOf(name), []));
}

// The HTML shell: static lang/title are acceptable only when the app keeps them in sync.
const SHELL = `<!doctype html>\n<html lang="es">\n<head><title>Gestor</title></head>\n<body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>\n</html>\n`;
const programWith = (text) => ({ getSourceFiles: () => [{ fileName: "/app/src/x.ts", isDeclarationFile: false, text }] });

test("flags a shell whose lang and title never follow the locale", () => {
  const reasons = inspectHtmlDocument(SHELL, "index.html", programWith("export {};")).findings.map((finding) => finding.reason).sort();
  assert.deepEqual(reasons, ["static-document-language", "static-document-title"]);
});

test("accepts the shell defaults when the app syncs lang and title at runtime", () => {
  const sync = "document.documentElement.lang = locale; document.title = t;";
  assert.deepEqual(inspectHtmlDocument(SHELL, "index.html", programWith(sync)).findings, []);
});

test("flags static text and visible attributes in the shell body", () => {
  const shell = SHELL.replace('<div id="root"></div>', '<div id="root"><p>Loading…</p><img alt="logo"></div>');
  const reasons = inspectHtmlDocument(shell, "index.html", programWith("document.documentElement.lang = l; document.title = t;")).findings.map((finding) => finding.reason);
  assert.deepEqual(reasons, ["static-document-text", "static-document-text"]);
});
