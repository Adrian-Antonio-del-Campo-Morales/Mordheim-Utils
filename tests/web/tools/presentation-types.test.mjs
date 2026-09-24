import { test } from "node:test";
import assert from "node:assert/strict";
import ts from "typescript";
import { resolve } from "node:path";
import { inspectPresentationTypes } from "../../../tools/web/presentation-type-audit.mjs";

test("KB provenance survives module boundaries and rejects unvalidated strings", () => {
  const filename = resolve("presentation-type-contract.virtual.ts");
  const source = `
    import { PresentationIndex, unavailableText, type ResolvedKbText } from "@adapters/knowledge-reader/presentation";
    import { translate } from "@src/features/campaign/i18n-core";
    import { presentationOutput } from "@src/features/campaign/presentation-output";
    import { textJoin, textNumber, warriorPersonalName } from "@src/features/campaign/presentation-values";
    declare function output(text: ResolvedKbText): void;
    declare const raw: string;
    output(raw);
    const forwarded = { label: raw };
    output(forwarded.label);
    output({ text: raw });
    output(unavailableText("es"));
    const result = new PresentationIndex([]).resolve({ kind: "item", id: "x" }, "name", "es");
    if (result.ok) output(result.text);
    translate({ key: "advance.skill", args: { name: raw } }, "es");
    translate({ key: "advance.duplicate-spell", args: { name: unavailableText("es") } }, "es");
    presentationOutput(raw);
    textJoin([raw]);
    warriorPersonalName(raw, "es");
    presentationOutput(textJoin([textNumber(3, "es"), unavailableText("es")]));
    presentationOutput(translate({ key: "advance.skill", args: { name: unavailableText("es") } }, "es"));
  `;
  const configPath = resolve("tsconfig.json");
  const config = ts.readConfigFile(configPath, ts.sys.readFile);
  const { options } = ts.parseJsonConfigFileContent(config.config, ts.sys, resolve("."));
  const host = ts.createCompilerHost(options);
  const originalGetSourceFile = host.getSourceFile.bind(host);
  host.getSourceFile = (path, languageVersion, onError, createNew) => resolve(path) === filename
    ? ts.createSourceFile(path, source, languageVersion, true)
    : originalGetSourceFile(path, languageVersion, onError, createNew);
  const program = ts.createProgram([filename], options, host);
  const diagnostics = ts.getPreEmitDiagnostics(program);
  assert.equal(diagnostics.length, 8, diagnostics.map((row) => ts.flattenDiagnosticMessageText(row.messageText, "\n")).join("\n"));
  assert.ok(diagnostics.every((row) => row.file && resolve(row.file.fileName) === filename && [2322, 2345, 2353].includes(row.code)), diagnostics.map((row) => `${row.code}: ${row.file?.fileName}`).join("\n"));
});

test("resolved type audit rejects aliases, typeof and nested forged labels", () => {
  const filename = resolve("src/presentation-forgery.virtual.ts");
  const source = `
    import { translate, type UiText as RenamedText } from "./features/campaign/i18n-core";
    type Alias = RenamedText;
    declare const raw: string;
    const real = translate({ key: "knowledge.unavailable" }, "es");
    export const first = raw as Alias;
    export const second = raw as typeof real;
    export const third = { label: raw } as { label: Alias };
    export const safe = { label: real } as const;
  `;
  const config = ts.readConfigFile(resolve("tsconfig.json"), ts.sys.readFile);
  const { options } = ts.parseJsonConfigFileContent(config.config, ts.sys, resolve("."));
  const host = ts.createCompilerHost(options), getSourceFile = host.getSourceFile.bind(host);
  host.getSourceFile = (path, version, ...rest) => resolve(path) === filename ? ts.createSourceFile(path, source, version, true) : getSourceFile(path, version, ...rest);
  const program = ts.createProgram([filename], options, host);
  assert.equal(ts.getPreEmitDiagnostics(program).length, 0);
  const findings = inspectPresentationTypes(program, program.getSourceFile(filename), resolve("."));
  assert.equal(findings.length, 3, JSON.stringify(findings));
  assert.ok(findings.every((finding) => finding.reason === "presentation-type-forgery"));
});
