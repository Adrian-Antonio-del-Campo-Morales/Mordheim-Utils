/**
 * Self-tests of the presentation gate orchestrator.
 *
 * The gate replaced a `&&` chain whose short-circuit hid the dynamic
 * completeness layer behind the static audit's non-zero exit. The central test
 * here is that regression: with the static phase exiting 1, the dynamic phase
 * still runs and its findings appear in the result and the summary.
 *
 * Phases are injected as real child processes (`node -e`) so the assertions
 * exercise genuine spawning, streaming and parsing — not mocks.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  runPresentationGate,
  summarizeGate,
  buildGateSummary,
  parseDetectorTests,
  parseStaticAudit,
  parseDynamicAudit,
} from "../../../tools/web/presentation-gate.mjs";

/** A phase backed by a real `node -e` child process. */
function phase({ id, label = id, kind, parse, script }) {
  return { id, label, kind, command: process.execPath, args: ["-e", script], cwd: process.cwd(), parse };
}

const TESTS_GREEN = phase({
  id: "detector-tests",
  kind: "tests",
  parse: parseDetectorTests,
  script: "console.log('\\u2139 tests 131');console.log('\\u2139 pass 131');console.log('\\u2139 fail 0');",
});
const STATIC_RED = phase({
  id: "static-audit",
  kind: "static",
  parse: parseStaticAudit,
  script: "console.log('2107 presentation sinks; 733 findings requiring review. outputs/web-presentation/gui-text-audit-deep.json');process.exit(1);",
});
const DYNAMIC_RED = phase({
  id: "dynamic-audit",
  kind: "dynamic",
  parse: parseDynamicAudit,
  script: "console.log('DYNAMIC_PHASE_RAN');console.log('Completeness audit: 9356 dynamic findings (generic-fallback=7500). outputs/web-presentation/gui-text-completeness.json');process.exit(1);",
});

test("runs the dynamic audit even when the static audit exits 1", async () => {
  const { results, summary } = await runPresentationGate({ phases: [TESTS_GREEN, STATIC_RED, DYNAMIC_RED], stream: false });

  // Every phase ran, in order, and none was short-circuited.
  assert.deepEqual(results.map((result) => result.id), ["detector-tests", "static-audit", "dynamic-audit"]);
  assert.equal(results[0].code, 0);
  assert.equal(results[1].code, 1, "static phase must exit 1 in this scenario");

  // The dynamic phase still executed and its findings are preserved.
  const dynamic = results[2];
  assert.match(dynamic.stdout, /DYNAMIC_PHASE_RAN/);
  assert.match(dynamic.stdout, /Completeness audit: 9356 dynamic findings/);
  assert.equal(dynamic.parse.findings, 9356);

  // The summary keeps the four categories apart and fails the gate.
  assert.deepEqual(summary.infrastructure, []);
  assert.equal(summary.staticFindings, 733);
  assert.equal(summary.dynamicFindings, 9356);
  assert.equal(summary.detectorTestsFailed, 0);
  assert.equal(summary.failed, true);
});

test("stored output of each phase is preserved verbatim", async () => {
  const { results } = await runPresentationGate({ phases: [TESTS_GREEN, STATIC_RED, DYNAMIC_RED], stream: false });
  assert.match(results[1].stdout, /2107 presentation sinks; 733 findings requiring review/);
  assert.match(results[2].stdout, /9356 dynamic findings/);
});

test("summary text distinguishes infrastructure, static, dynamic and detector-test failures", async () => {
  const { results, summary } = await runPresentationGate({ phases: [TESTS_GREEN, STATIC_RED, DYNAMIC_RED], stream: false });
  const text = buildGateSummary(results, summary);
  assert.match(text, /Infrastructure failures/);
  assert.match(text, /Static findings\s*\.+: 733/);
  assert.match(text, /Dynamic findings\s*\.+: 9356/);
  assert.match(text, /Detector tests failed\s*\.+: 0/);
  assert.match(text, /Result: FAIL/);
});

test("flags failed detector tests as detector-test failures, not infrastructure", async () => {
  const failing = phase({
    id: "detector-tests",
    kind: "tests",
    parse: parseDetectorTests,
    script: "console.log('\\u2139 tests 15');console.log('\\u2139 pass 13');console.log('\\u2139 fail 2');process.exit(1);",
  });
  const { summary } = await runPresentationGate({ phases: [failing], stream: false });
  assert.equal(summary.detectorTestsFailed, 2);
  assert.deepEqual(summary.infrastructure, []);
  assert.equal(summary.failed, true);
});

test("classifies a missing executable as an infrastructure failure", async () => {
  const broken = { id: "static-audit", label: "broken", kind: "static", command: "definitely-not-a-real-binary-xyz-12345", args: [], cwd: process.cwd(), parse: parseStaticAudit };
  const { summary } = await runPresentationGate({ phases: [broken], stream: false });
  assert.equal(summary.infrastructure.length, 1);
  assert.equal(summary.infrastructure[0].id, "static-audit");
  assert.equal(summary.staticFindings, 0);
  assert.equal(summary.failed, true);
});

test("classifies a non-zero exit without a summary as infrastructure, not findings", async () => {
  const crash = phase({ id: "static-audit", kind: "static", parse: parseStaticAudit, script: "console.error('boom');process.exit(1);" });
  const { summary } = await runPresentationGate({ phases: [crash], stream: false });
  assert.equal(summary.infrastructure.length, 1);
  assert.match(summary.infrastructure[0].reason, /without a report summary/);
  assert.equal(summary.staticFindings, 0);
  assert.equal(summary.failed, true);
});

test("reports PASS when every phase is green", async () => {
  const staticGreen = phase({ id: "static-audit", kind: "static", parse: parseStaticAudit, script: "console.log('2107 presentation sinks; 0 findings requiring review. x.json');" });
  const dynamicGreen = phase({ id: "dynamic-audit", kind: "dynamic", parse: parseDynamicAudit, script: "console.log('Completeness audit: 0 dynamic findings (raw-text=0). y.json');" });
  const { results, summary } = await runPresentationGate({ phases: [TESTS_GREEN, staticGreen, dynamicGreen], stream: false });
  assert.equal(summary.failed, false);
  assert.equal(summary.staticFindings, 0);
  assert.equal(summary.dynamicFindings, 0);
  assert.match(buildGateSummary(results, summary), /Result: PASS/);
});

test("parses the real summary lines of the three phases", () => {
  assert.deepEqual(parseDetectorTests("ℹ tests 131\nℹ pass 131\nℹ fail 0\n"), { findings: 0, tests: 131, failed: 0, detail: "131 tests, 0 failed" });
  assert.equal(parseStaticAudit("2107 presentation sinks; 733 findings requiring review. out.json").findings, 733);
  assert.equal(parseDynamicAudit("Completeness audit: 9356 dynamic findings (raw-text=0). out.json").findings, 9356);
  assert.equal(parseStaticAudit("unexpected").unparsed, true);
  assert.equal(parseDynamicAudit("unexpected").unparsed, true);
});

test("summarizeGate is stable with an empty phase list", () => {
  const summary = summarizeGate([]);
  assert.deepEqual(summary, { infrastructure: [], detectorTestsFailed: 0, staticFindings: 0, dynamicFindings: 0, failed: false });
});
