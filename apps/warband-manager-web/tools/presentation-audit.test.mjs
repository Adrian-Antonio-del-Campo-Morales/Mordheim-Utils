import { test } from "node:test";
import assert from "node:assert/strict";
import { inspectPresentation, inspectCssPresentation, guiReport, audit } from "./presentation-audit.mjs";
import { fileURLToPath } from "node:url";

const cut = { file: "packages/kb.ts", line: 7, expression: "doc", reason: "step-limit", path: [] };
const origin = { file: "packages/kb.ts", line: 3, expression: "row.name", path: [] };
const twoSinks = 'const View = () => <span title={data.caption}>{data.displayValue}</span>;';

test("a cut that already demonstrated an origin is reported once, marked truncated", () => {
  const trace = () => ({ origins: [origin], truncated: true, incomplete: [cut] });
  const result = inspectPresentation(twoSinks, "src/new.tsx", { strict: true, trace });
  const raw = result.findings.filter((finding) => finding.reason === "raw-text-flow");
  assert.equal(raw.length, 2);
  assert.ok(raw.every((finding) => finding.truncated === true && finding.incomplete.length === 1));
  assert.equal(result.findings.filter((finding) => finding.reason === "incomplete-text-flow").length, 0);
});

test("a cut that reached no origin at all remains an incomplete finding", () => {
  const trace = () => ({ origins: [], truncated: true, incomplete: [cut] });
  const result = inspectPresentation(twoSinks, "src/new.tsx", { strict: true, trace });
  const incomplete = result.findings.filter((finding) => finding.reason === "incomplete-text-flow");
  assert.equal(incomplete.length, 2);
  assert.ok(incomplete.every((finding) => finding.incomplete.length === 1 && !finding.truncated));
  assert.equal(result.findings.filter((finding) => finding.reason === "raw-text-flow").length, 0);
});

test("a complete trace carries no truncation mark", () => {
  const trace = () => ({ origins: [origin], truncated: false, incomplete: [] });
  const result = inspectPresentation(twoSinks, "src/new.tsx", { strict: true, trace });
  assert.equal(result.findings.filter((finding) => finding.reason === "raw-text-flow").length, 2);
  assert.ok(result.findings.every((finding) => !finding.truncated));
});

test("real GUI deep analysis blocks every unresolved text-provenance path", () => {
  const root = fileURLToPath(new URL("../", import.meta.url));
  const result = audit(root, { strict: true, deep: true });
  const incomplete = result.findings.filter((finding) => finding.reason === "incomplete-text-flow");
  // The detector must reject uncertainty, not require fixing the application's
  // outputs as part of testing the detector itself. CLI fails on any finding.
  for (const finding of incomplete) {
    assert.ok(finding.incomplete.length > 0);
    assert.ok(result.sinks.some((sink) => sink.file === finding.file && sink.line === finding.line));
  }
  // The cut is never a second finding for a sink whose origin is already known:
  // that duplication hid which outputs had no demonstrated origin at all.
  const key = (row) => `${row.file}:${row.line}:${row.expression}`;
  const raw = result.findings.filter((finding) => finding.reason === "raw-text-flow");
  assert.ok(raw.some((finding) => finding.truncated === true), "deep mode must still report truncated raw paths");
  for (const finding of incomplete) assert.ok(!raw.some((row) => key(row) === key(finding)), key(finding));
  assert.ok(result.sinks.some((sink) => sink.file === "index.html"));
});

// No expected-failure markers: detector blind spots must fail the suite.
for (const [name, source] of [
  ["bracket writer alias", 'const emit = document["write"]; emit(raw);'],
  ["canvas writer destructuring", 'const { fillText: emit } = context; emit(raw, 0, 0);'],
  ["tooltip dataset brackets", 'node.dataset["tooltip"] = raw;'],
  ["CSS custom property assignment", 'node.style["--caption"] = raw;'],
  ["SVG animation text attribute", '<animate attributeName="aria-label" values={raw} />'],
  ["dynamic custom element", '<custom-widget caption={raw} />'],
  ["iframe srcdoc lowercase", '<iframe srcdoc={raw} />'],
  ["document writeln multiple arguments", 'document.writeln(presentationOutput(label), raw);'],
  ["prompt default", 'prompt(presentationOutput(label), raw);'],
  ["custom dataset", '<span data-caption={raw} />'],
  ["dynamic execution", 'eval(source);'],
  ["constructed execution", 'new Function(source);'],
  ["unknown native attribute", '<span futureCaption={raw} />'],
  ["external embedded content", '<iframe src={url} />'],
  ["root render", 'root.render(raw);'],
  ["portal text", 'createPortal(raw, target);'],
]) test(`requires detection of additional GUI sink: ${name}`, () => {
  const prefix = 'import { presentationOutput } from "./presentation-output";';
  assert.ok(inspectPresentation(prefix + source, "src/new.tsx", { strict: true }).findings.length > 0, source);
});

test("CSS comments, case, escapes and imports cannot bypass the audit", () => {
  for (const source of ['a { CONTENT: "raw" }', 'a { content/**/: "raw" }', String.raw`a { c\6f ntent: "raw" }`, '@import "remote.css";']) assert.ok(inspectCssPresentation(source).findings.length > 0, source);
});

for (const [name, source] of [
  ["JSX identifier", "const View = () => <span>{row.item_id}</span>"],
  ["accessible attribute", "const View = () => <input aria-label={row.id} />"],
  ["aliased identifier", "const label = row.profile_id; const View = () => <span>{label}</span>"],
  ["destructured identifier", "const { item_id: label } = row; const View = () => <span>{label}</span>"],
  ["object label alias", "const model = { label: row.item_id }; const View = () => <span>{model.label}</span>"],
  ["function parameter forwarding", "function label(value) { return value; } const View = () => <span>{label(row.item_id)}</span>"],
  ["PDF output", "page.drawText(row.tag)"],
  ["PDF cell output", "sheet.cell(0, 9, row.item_id)"],
  ["PDF multiline output", "sheet.multiCell(40, 5, row.profile_name)"],
  ["resolver name spoofing", 'function knowledgeName() { return row.item_id; } const View = () => <span>{knowledgeName()}</span>'],
  ["DOM output", "element.textContent = row.message"],
  ["DOM attribute", 'element.setAttribute("aria-label", data.caption)'],
  ["dynamic DOM attribute", 'element.setAttribute(attribute, data.caption)'],
  ["adjacent DOM text", 'element.insertAdjacentText("beforeend", data.caption)'],
  ["document writer", 'document.write(data.caption)'],
  ["CSS dataset label", 'element.dataset.disabledTooltip = data.caption'],
  ["unsafe cast", "const View = () => <span>{raw as any}</span>"],
  ["forged presentation value", "const View = () => <span>{raw as PresentationText}</span>"],
  ["forged KB value", "const View = () => <span>{raw as ResolvedKbText}</span>"],
  ["forged message before output", "const forged = raw as UiText; export { forged };"],
]) {
  test(`rejects deliberate ${name} leakage`, () => {
    assert.ok(inspectPresentation(source).findings.length > 0);
  });
}

test("removing an adapter import cannot reopen migrated modules", () => {
  for (const filename of ["src/features/campaign/KnowledgeHint.tsx", "src/features/common/NumberStepper.tsx", "src/features/export/warband-pdf.ts"]) {
    const result = inspectPresentation('const View = () => <span title={data.caption}>{data.displayValue}</span>;', filename);
    assert.equal(result.findings.filter((finding) => finding.reason === "unvalidated-output").length, 2, filename);
  }
});

test("preserves action identifiers and validates visible numeric selections", () => {
  const result = inspectPresentation('import { presentationOutput } from "./presentation-output"; const View = () => <button key={row.id} onClick={() => select(row.id)}>{presentationOutput(textNumber(amounts[row.id], locale))}</button>');
  assert.equal(result.findings.length, 0);
});

test("new files cannot evade the mandatory boundary by omitting imports", () => {
  const result = inspectPresentation('const View = () => <span title={data.caption}>{data.displayValue}Untranslated</span>;', "src/new-page.tsx");
  assert.equal(result.findings.filter((finding) => finding.reason === "unvalidated-output").length, 3);
});

test("bootstrap mirrors only the audited disabled reason on the same control", () => {
  assert.equal(inspectPresentation('control.setAttribute("aria-description", control.dataset.disabledReason); control.dataset.disabledTooltip = control.dataset.disabledReason;', "src/main.tsx").findings.length, 0);
  for (const source of ['control.setAttribute("aria-description", control.dataset.raw);', 'control.dataset.disabledTooltip = "raw";', 'other.setAttribute("aria-description", control.dataset.disabledReason);']) {
    assert.ok(inspectPresentation(source, "src/main.tsx").findings.length > 0);
  }
});

test("inventories text, accessibility, document and DOM output", () => {
  const result = inspectPresentation('const View = () => <span title={translate(message, locale)}>Text{knowledgeName(kb, "item", row.id, locale)}</span>; page.drawText(text); element.textContent = text;');
  assert.deepEqual(new Set(result.sinks.map((sink) => sink.kind)), new Set(["jsx-text", "jsx-expression", "attribute", "document-or-dialog", "dom-write"]));
});

test("closed output modules reject every bypass irrespective of identifier spelling", () => {
  const source = 'import { presentationOutput as output } from "./presentation-output"; const View = () => <span title={data.caption}>{data.displayValue}</span>;';
  const result = inspectPresentation(source);
  assert.equal(result.findings.filter((finding) => finding.reason === "unvalidated-output").length, 2);
  assert.equal(inspectPresentation('import { presentationOutput as output } from "./presentation-output"; const View = () => <span title={output(label)}>{output(label)}</span>;').findings.length, 0);
});

test("CSS content rejects raw words and unvalidated attributes", () => {
  const result = inspectCssPresentation('.a { justify-content: center; content: "internal_label"; } .b::after { content: attr(data-raw); } .c { content: attr(data-label); } .d { content: "✓"; }');
  assert.equal(result.sinks.length, 4);
  assert.equal(result.findings.length, 2);
  assert.ok(result.findings.every((row) => row.reason === "unvalidated-css-content"));
});

test("generated React containers still validate every textual leaf", () => {
  const prefix = 'import { presentationOutput } from "./presentation-output";';
  const good = prefix + 'const V = () => <div>{(() => <span>{presentationOutput(label)}</span>)()}{Array.from({length: 2}, () => <b>{presentationOutput(label)}</b>)}</div>;';
  assert.equal(inspectPresentation(good).findings.length, 0);
  for (const bad of ['<div>{(() => raw)()}</div>', '<div>{Array.from({length: 2}, () => raw)}</div>', '<div>{Array.from({length: 2}, () => <b>{raw}</b>)}</div>']) {
    assert.ok(inspectPresentation(prefix + 'const V = () => ' + bad).findings.some((row) => row.reason === "unvalidated-output"));
  }
});

for (const [name, source, reason] of [
  ["visible input value", '<input value={record.profile_name} />', "unclassified-control-value"],
  ["textarea default", '<textarea defaultValue={record.message} />', "unclassified-control-value"],
  ["submit label", '<input type="submit" value="Save" />', "unclassified-control-value"],
  ["dynamic input type", '<input type={kind} value={value} />', "unclassified-control-value"],
  ["spread labels", '<span {...props} />', "unclassified-spread"],
  ["indirect component data", '<Grid rows={rows} />', "unclassified-component-prop"],
  ["render callback", '<Grid renderCell={() => raw} />', "unclassified-component-prop"],
  ["raw HTML", '<div dangerouslySetInnerHTML={{ __html: raw }} />', "unclassified-html"],
  ["React factory", 'React.createElement("span", {}, raw)', "unclassified-dynamic-element"],
  ["computed writer", 'node[method](raw)', "unclassified-computed-call"],
  ["computed assignment", 'node[property] = raw', "unclassified-computed-write"],
  ["indirect insertion", 'element.append(raw)', "unclassified-dom-insertion"],
  ["canvas", 'context.fillText(raw, 0, 0)', "unvalidated-output"],
  ["text node", 'document.createTextNode(raw)', "unvalidated-output"],
  ["children property", '<span children={raw} />', "unvalidated-output"],
  ["numeric render guard", '<span>{count && <b />}</span>', "unclassified-render-guard"],
  ["iframe document", '<iframe srcDoc={html} />', "unclassified-html"],
  ["inline generated content", '<span style={{content: raw}} />', "unclassified-style-content"],
  ["spread style", '<span style={{...style}} />', "unclassified-style"],
  ["dynamic style", '<span style={style} />', "unclassified-style"],
  ["namespaced accessible attribute", 'node.setAttributeNS(null, "aria-label", raw)', "unvalidated-output"],
  ["braille label", '<span aria-braillelabel={raw} />', "unvalidated-output"],
  ["role description", '<span aria-roledescription={raw} />', "unvalidated-output"],
  ["bound writer", 'const write = document.write.bind(document); write(raw)', "unclassified-aliased-writer"],
  ["writer alias chain", 'const first = document.write; const second = first; second(raw)', "unclassified-aliased-writer"],
  ["destructured writer", 'const { write: emit } = document; emit(raw)', "unclassified-aliased-writer"],
  ["writer apply", 'document.write.apply(document, [raw])', "unclassified-aliased-writer"],
  ["object assign", 'Object.assign(node, {textContent: raw})', "unclassified-indirect-write"],
  ["reflect write", 'Reflect.set(node, "textContent", raw)', "unclassified-indirect-write"],
  ["HTML fragment", 'range.createContextualFragment(raw)', "unclassified-html"],
  ["HTML parser", 'parser.parseFromString(raw, "text/html")', "unclassified-html"],
  ["HTML setter", 'node.setHTMLUnsafe(raw)', "unclassified-html"],
  ["stylesheet rule", 'sheet.insertRule(rule)', "unclassified-style"],
  ["CSSOM content", 'node.style.content = raw', "unclassified-style-content"],
]) {
  test(`strict GUI audit detects ${name}`, () => {
    assert.ok(inspectPresentation(source, "src/new.tsx", { strict: true }).findings.some((finding) => finding.reason === reason));
  });
}

test("strict audit separates selection identity from text shown by controls", () => {
  const source = 'import { presentationOutput } from "./presentation-output"; const V = () => <><select value={id}><option value={id}>{presentationOutput(label)}</option></select><input type="checkbox" value={id}/><input value={presentationOutput(label)}/></>;';
  const result = inspectPresentation(source, "src/new.tsx", { strict: true });
  assert.equal(result.findings.length, 0, JSON.stringify(result.findings));
  assert.equal(result.sinks.filter((sink) => sink.classification === "non-display-identity").length, 3);
  assert.ok(result.sinks.some((sink) => sink.kind === "control-value"));
});

test("strict audit reports element and source location; Markdown cannot inject markup", () => {
  const result = inspectPresentation('\nconst V = () => <input value={raw} />;', "src/new.tsx", { strict: true });
  const finding = result.findings.find((row) => row.reason === "unclassified-control-value");
  assert.equal(finding.element, "input");
  assert.equal(finding.line, 2);
  const report = guiReport({ sinks: [], findings: [{ file: "x", line: 1, expression: '<script>|\nraw', reason: "unclassified" }] });
  assert.ok(report.includes('&lt;script&gt;\\| raw'));
  assert.ok(!report.includes('<script>'));
  const truncated = guiReport({ sinks: [], findings: [{ file: "x", line: 1, expression: "e", reason: "raw-text-flow", origins: [{ file: "kb.ts", line: 2, expression: "row.name", path: [] }], truncated: true }] });
  assert.ok(truncated.includes("recorrido truncado"));
  assert.ok(!guiReport({ sinks: [], findings: [{ file: "x", line: 1, expression: "e", reason: "raw-text-flow", origins: [] }] }).includes("recorrido truncado"));
});
