/**
 * Presentation gate — the single entry point of `npm run check:presentation`
 * (and therefore of `python tools/mordheim-utils.py check-presentation`).
 *
 * Why this exists: the three checks used to be chained with `&&`, so the
 * static audit's non-zero exit (733 inherited findings) short-circuited the
 * dynamic visible-completeness layer, which then never ran. A gate must run
 * every phase unconditionally, preserve each phase's output verbatim and tell
 * apart its own infrastructure failures from findings, so a red static phase
 * can never hide the dynamic one.
 *
 * Rules honoured here: no `&&`, no `;`, no shell — the phases are spawned
 * directly (portable on Windows and POSIX) and each phase always executes.
 * Exit code: non-zero when any phase fails or infrastructure breaks.
 *
 * Phases, in report order:
 * 1. Detector self-tests (`node:test` over the four detector suites).
 * 2. Static GUI text audit (`presentation-audit.mjs --strict --deep --check`).
 * 3. Dynamic visible-completeness audit (`presentation-completeness-audit.mjs`).
 */
import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = fileURLToPath(new URL(".", import.meta.url));
export const REPO_ROOT = resolve(HERE, "..", "..");
// The phases historically ran with the web app as the working directory, and
// the detector tests read `tsconfig.json` and `src/` relative to cwd: keep that
// cwd so the pre-existing static detectors behave exactly as before.
export const APP_DIR = resolve(REPO_ROOT, "apps", "warband-manager-web");

/** The three phases of the gate; every one runs on every invocation. */
export function definePhases(root = REPO_ROOT, cwd = APP_DIR) {
  return [
    {
      id: "detector-tests",
      label: "Detector self-tests (node:test)",
      kind: "tests",
      command: process.execPath,
      args: [
        "--test",
        resolve(root, "tests", "web", "tools", "presentation-audit.test.mjs"),
        resolve(root, "tests", "web", "tools", "presentation-types.test.mjs"),
        resolve(root, "tests", "web", "tools", "presentation-flow-audit.test.mjs"),
        resolve(root, "tests", "web", "tools", "presentation-completeness-detector.test.mjs"),
      ],
      cwd,
      parse: parseDetectorTests,
    },
    {
      id: "static-audit",
      label: "Static GUI text audit (--strict --deep --check)",
      kind: "static",
      command: process.execPath,
      args: [resolve(root, "tools", "web", "presentation-audit.mjs"), "--strict", "--deep", "--check"],
      cwd,
      parse: parseStaticAudit,
    },
    {
      id: "dynamic-audit",
      label: "Dynamic visible-completeness audit",
      kind: "dynamic",
      command: process.execPath,
      args: [resolve(root, "tools", "web", "presentation-completeness-audit.mjs")],
      cwd,
      parse: parseDynamicAudit,
    },
  ];
}

// ---------------------------------------------------------------------------
// Output parsers: each phase prints one summary line. A phase that exits
// non-zero without one is treated as an infrastructure fault, not as findings.
// ---------------------------------------------------------------------------

/** Read `ℹ <label> <n>` (node:test; older versions print `# <label> <n>`). */
function tapCount(output, label) {
  const match = new RegExp(`^[ℹ#]\\s*${label}\\s+(\\d+)\\s*$`, "m").exec(output);
  return match ? Number(match[1]) : null;
}

export function parseDetectorTests(output) {
  const tests = tapCount(output, "tests");
  const failed = tapCount(output, "fail");
  if (tests === null && failed === null) return { unparsed: true, detail: "node:test produced no summary" };
  return {
    findings: failed ?? 0,
    tests: tests ?? undefined,
    failed: failed ?? undefined,
    detail: `${tests ?? "?"} tests, ${failed ?? "?"} failed`,
  };
}

export function parseStaticAudit(output) {
  const match = /(\d+)\s+presentation sinks;\s*(\d+)\s+findings requiring review/.exec(output);
  if (!match) return { unparsed: true, detail: "static audit produced no findings summary" };
  return { findings: Number(match[2]), sinks: Number(match[1]), detail: `${match[2]} static findings of ${match[1]} sinks` };
}

export function parseDynamicAudit(output) {
  const match = /Completeness audit:\s*(\d+)\s+dynamic findings/.exec(output);
  if (!match) return { unparsed: true, detail: "dynamic audit produced no findings summary" };
  return { findings: Number(match[1]), detail: `${match[1]} dynamic findings` };
}

// ---------------------------------------------------------------------------
// Execution
// ---------------------------------------------------------------------------

/**
 * Spawn one phase, streaming its stdout/stderr to this process while keeping
 * the text for parsing. Resolves to a result record; never rejects, so one
 * broken phase cannot stop the others.
 */
export function runPhase(phase, { stream = true } = {}) {
  return new Promise((settle) => {
    const startedAt = Date.now();
    let stdout = "";
    let stderr = "";
    let done = false;
    const finish = (result) => {
      if (done) return;
      done = true;
      settle({ id: phase.id, label: phase.label, kind: phase.kind, elapsedMs: Date.now() - startedAt, ...result });
    };
    let child;
    try {
      child = spawn(phase.command, phase.args, {
        cwd: phase.cwd,
        env: { ...process.env, ...(phase.env ?? {}) },
        windowsHide: true,
      });
    } catch (error) {
      finish({ code: null, stdout, stderr, infra: true, infraReason: `spawn failed: ${error.message}`, parse: { unparsed: true, detail: "not started" } });
      return;
    }
    child.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      stdout += text;
      if (stream) process.stdout.write(text);
    });
    child.stderr.on("data", (chunk) => {
      const text = chunk.toString();
      stderr += text;
      if (stream) process.stderr.write(text);
    });
    child.on("error", (error) => {
      finish({ code: null, stdout, stderr, infra: true, infraReason: `spawn failed: ${error.message}`, parse: { unparsed: true, detail: "not started" } });
    });
    child.on("close", (code, signal) => {
      const combined = `${stdout}\n${stderr}`;
      const infra = signal !== null || code === null;
      finish({
        code,
        signal: signal ?? undefined,
        stdout,
        stderr,
        infra,
        infraReason: infra ? `terminated by ${signal ?? "unknown signal"}` : undefined,
        parse: infra ? { unparsed: true, detail: "process did not complete" } : (phase.parse ? phase.parse(combined) : {}),
      });
    });
  });
}

/**
 * Classify the phase results into the four categories the gate must
 * distinguish, plus the overall verdict.
 */
export function summarizeGate(results) {
  const infrastructure = [];
  let detectorTestsFailed = 0;
  let staticFindings = 0;
  let dynamicFindings = 0;
  for (const result of results) {
    if (result.infra) {
      infrastructure.push({ id: result.id, reason: result.infraReason ?? "process did not complete" });
      continue;
    }
    if (result.code !== 0 && result.parse?.unparsed) {
      // A non-zero exit with no report summary is the tool/infrastructure
      // breaking, not an attributed finding: it must not be counted as one.
      infrastructure.push({ id: result.id, reason: `exit ${result.code} without a report summary` });
      continue;
    }
    if (result.kind === "tests") detectorTestsFailed += result.parse?.failed ?? (result.code !== 0 ? 1 : 0);
    if (result.kind === "static") staticFindings += result.parse?.findings ?? 0;
    if (result.kind === "dynamic") dynamicFindings += result.parse?.findings ?? 0;
  }
  const failed = results.some((result) => result.infra || result.code !== 0);
  return { infrastructure, detectorTestsFailed, staticFindings, dynamicFindings, failed };
}

/** Human-readable report: per-phase status, then the four categories. */
export function buildGateSummary(results, summary = summarizeGate(results)) {
  const status = (result) => (result.infra ? "infra" : result.code === 0 ? "ok  " : "FAIL");
  const lines = [
    "",
    "─── Presentation gate ─────────────────────────────────────────────",
    `Phases executed (all unconditionally): ${results.length}`,
  ];
  for (const result of results) {
    const detail = result.parse && !result.parse.unparsed ? `— ${result.parse.detail}` : `— ${result.infraReason ?? "no summary"}`;
    lines.push(`  [${status(result)}] ${result.label} (exit ${result.code ?? "—"}) ${detail}`);
  }
  lines.push("");
  lines.push("Classification");
  if (summary.infrastructure.length === 0) {
    lines.push("  Infrastructure failures ..: none");
  } else {
    lines.push(`  Infrastructure failures ..: ${summary.infrastructure.length}`);
    for (const failure of summary.infrastructure) lines.push(`    - ${failure.id}: ${failure.reason}`);
  }
  lines.push(`  Static findings ..........: ${summary.staticFindings}`);
  lines.push(`  Dynamic findings .........: ${summary.dynamicFindings}`);
  lines.push(`  Detector tests failed ....: ${summary.detectorTestsFailed}`);
  lines.push("");
  lines.push(summary.failed ? "Result: FAIL (non-zero exit)" : "Result: PASS");
  lines.push("───────────────────────────────────────────────────────────────────");
  return lines.join("\n") + "\n";
}

/**
 * Run every phase in order, then print the report. Returns the structured
 * result so callers (and the orchestrator's own test) can assert on it.
 */
export async function runPresentationGate({ phases = definePhases(), stream = true } = {}) {
  const results = [];
  for (const phase of phases) {
    if (stream) process.stdout.write(`\n=== ${phase.label} ===\n`);
    results.push(await runPhase(phase, { stream }));
  }
  const summary = summarizeGate(results);
  if (stream) process.stdout.write(buildGateSummary(results, summary));
  return { results, summary };
}

// Run as a CLI only when invoked directly (never on import, so tests are free
// to inject synthetic phases).
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { summary } = await runPresentationGate();
  process.exitCode = summary.failed ? 1 : 0;
}
