import { test } from "node:test";
import assert from "node:assert/strict";
import { resolve } from "node:path";
import ts from "typescript";
import { createPresentationFlowAudit } from "./presentation-flow-audit.mjs";

function fixture(source, helper = "export function forward(value: string) { return value; }", limits = {}) {
  const root = resolve("."), main = resolve("src/flow-main.virtual.ts"), other = resolve("src/flow-helper.virtual.ts");
  const sources = new Map([[main, source], [other, helper]]);
  const host = ts.createCompilerHost({});
  const get = host.getSourceFile.bind(host), exists = host.fileExists.bind(host);
  host.fileExists = (path) => sources.has(resolve(path)) || exists(path);
  host.getSourceFile = (path, version, ...args) => sources.has(resolve(path)) ? ts.createSourceFile(path, sources.get(resolve(path)), version, true) : get(path, version, ...args);
  const program = ts.createProgram([main, other], { target: ts.ScriptTarget.ESNext, module: ts.ModuleKind.CommonJS, strict: true }, host);
  const file = program.getSourceFile(main);
  const output = file.statements.find((node) => ts.isVariableStatement(node) && node.declarationList.declarations[0].name.getText() === "output").declarationList.declarations[0].initializer;
  return createPresentationFlowAudit(program, root, limits)(output);
}

const prefix = 'declare const kb: { name: string; id: string; effect: string; name_i18n: { es: string; en: string } };';
for (const [name, code] of [
  ["alias and template", 'const alias = kb.name; const output = `Label: ${alias}`;'],
  ["copied row", 'const row = { caption: kb.effect }; const output = row.caption;'],
  ["destructuring", 'const { name: caption } = kb; const output = caption;'],
  ["language fallback", 'const output = kb.name_i18n.es || kb.name_i18n.en || kb.id;'],
  ["humanized id", 'const output = kb.id.replaceAll("_", " ").toUpperCase();'],
  ["local function", 'function label(value: string) { return value.toUpperCase(); } const output = label(kb.name);'],
  ["imported function", 'import { forward } from "./flow-helper.virtual"; const output = forward(kb.name);'],
  ["reassignment", 'let label = ""; label = kb.name; const output = label;'],
  ["state setter", 'declare function useState(v: string): [string, (v: string) => void]; const [label, setLabel] = useState(""); setLabel(kb.name); const output = label;'],
  ["array mapping", 'const labels = [kb].map(row => row.name); const output = labels.join(", ");'],
  ["forged cast", 'declare const uiTextBrand: unique symbol; type UiText = string & { [uiTextBrand]: true }; const output = kb.name as UiText;'],
]) test(`tracks raw text through ${name}`, () => {
  const result = fixture(prefix + code);
  assert.ok(result.origins.length, JSON.stringify(result));
  assert.ok(result.origins.every((origin) => origin.file && origin.line > 0 && origin.path.length));
});

test("traces imported return source even when no raw argument exists", () => {
  const result = fixture('import { forward } from "./flow-helper.virtual"; const output = forward();', 'const row = { name: "RAW_KB_MARKER" }; export function forward() { return row.name; }');
  assert.ok(result.origins.some((origin) => origin.file.endsWith("flow-helper.virtual.ts")));
});

test("resolved opaque output stops propagation; action IDs and literals alone are not raw reads", () => {
  const result = fixture(prefix + 'declare const resolvedTextBrand: unique symbol; declare function resolve(id: string): string & { [resolvedTextBrand]: true }; const output = resolve(kb.id);');
  assert.equal(result.origins.length, 0);
  assert.equal(fixture('const output = "fixed test text";').origins.length, 0);
});

test("type-level plumbing is traced but does not consume the work budget", () => {
  const kb = 'declare const kb: { name: string }; ';
  const wrapped = `${kb}const output = ${"(".repeat(20)}((kb.name as unknown) as string)${")".repeat(20)}!;`;
  const tight = fixture(wrapped, undefined, { maxSteps: 4, maxDepth: 24 });
  assert.equal(tight.truncated, false, JSON.stringify(tight));
  assert.ok(tight.origins.some((origin) => origin.expression === "kb.name"));
  // The same budget still truncates a chain of data hops: the exemption covers
  // type-level plumbing only, not the backwards slice itself.
  const chain = Array.from({ length: 20 }, (_, i) => `const v${i} = ${i ? `v${i - 1}` : "kb.name"};`).join("");
  assert.equal(fixture(`${kb}${chain}const output = v19;`, undefined, { maxSteps: 4, maxDepth: 24 }).truncated, true);
});

test("type annotations and type arguments are neither traversed nor charged", () => {
  const typed = fixture('const output = new Map<string, { name: string; id: string }>();', undefined, { maxSteps: 4, maxDepth: 24 });
  assert.equal(typed.truncated, false, JSON.stringify(typed));
  assert.equal(typed.origins.length, 0);
  // A field name inside an annotation is a type, never a raw read.
  const annotated = fixture('declare const kb: { name: string }; const output: { name: string; id: string; effect: string } = kb;', undefined, { maxSteps: 4, maxDepth: 24 });
  assert.equal(annotated.truncated, false, JSON.stringify(annotated));
  assert.equal(annotated.origins.length, 0);
});

test("cycles terminate and bounded analysis declares incomplete paths", () => {
  assert.equal(fixture('let a = ""; let b = a; a = b; const output = a;').truncated, false);
  const chain = Array.from({ length: 40 }, (_, i) => `const v${i} = ${i ? `v${i - 1}` : 'kb.name'};`).join("\n");
  assert.equal(fixture(prefix + chain + 'const output = v39;').truncated, true);
  const deep = fixture(prefix + chain + 'const output = v39;', undefined, { maxSteps: 2500, maxDepth: 80 });
  assert.equal(deep.truncated, false);
  assert.ok(deep.origins.some((origin) => origin.expression === "kb.name"));
  const limited = fixture(prefix + chain + 'const output = v39;');
  assert.ok(limited.incomplete.every((row) => row.file && row.line > 0 && row.reason === "depth-limit"));
});

// These are detection requirements, not expected failures. Keep failures visible
// until the analyzer is explicitly authorized to implement the missing paths.
for (const [name, code] of [
  ["object mutation through an alias", 'const model = { caption: "" }; const alias = model; alias.caption = kb.name; const output = model.caption;'],
  ["Object.assign mutation", 'const model = { caption: "" }; Object.assign(model, { caption: kb.name }); const output = model.caption;'],
  ["Reflect.set mutation", 'const model = { caption: "" }; Reflect.set(model, "caption", kb.effect); const output = model.caption;'],
  ["array push followed by join", 'const labels: string[] = []; labels.push(kb.name); const output = labels.join(", ");'],
  ["Map write then read", 'const labels = new Map<string, string>(); labels.set("caption", kb.name); const output = labels.get("caption");'],
  ["callback side effect", 'let caption = ""; [kb].forEach(row => { caption = row.name; }); const output = caption;'],
  ["useMemo return", 'declare function useMemo<T>(fn: () => T, deps: unknown[]): T; const caption = useMemo(() => kb.effect, [kb]); const output = caption;'],
  ["useRef current mutation", 'declare function useRef<T>(value: T): { current: T }; const ref = useRef(""); ref.current = kb.name; const output = ref.current;'],
  ["renamed useState import", 'import { useState as state } from "./flow-helper.virtual"; const [caption, update] = state(""); update(kb.name); const output = caption;'],
  ["getter reads KB", 'const model = { get caption() { return kb.effect; } }; const output = model.caption;'],
  ["bound function return", 'function name() { return kb.name; } const bound = name.bind(null); const output = bound();'],
  ["JSON capture round trip", 'const saved = JSON.stringify({ caption: kb.name }); const output = JSON.parse(saved).caption;'],
]) test(`requires raw provenance detection through ${name}`, () => {
  const result = fixture(prefix + code, 'export declare function useState(value: string): [string, (value: string) => void];');
  assert.ok(result.origins.length > 0, `Raw KB text reached output but no origin was reported: ${code}\n${JSON.stringify(result)}`);
});
