/**
 * Web architecture and bundle guardrails — the checks the per-layer purity test
 * (`tests/tooling/architecture/purity.test.ts`) does not cover:
 *
 *  1. the UI never loads YAML directly (knowledge arrives as the generated
 *     JSON artefact — the P4.x bundling decision);
 *  2. campaigns never touch browser storage (no localStorage / IndexedDB /
 *     sessionStorage anywhere — campaigns stay in memory);
 *  3. the file adapter holds no business rules (no mordheim_campaign import,
 *     no rule keywords in campaign-file adapter sources);
 *  4. the built bundle excludes Combat Lab, NumPy, Cython and Tkinter
 *     (permanent product boundary). That post-build check belongs to the
 *     application package (`tests/applications/warband_manager/packaging/`).
 *
 * Source scans read files with node:fs and check *source text* — the app
 * ships no server code, so this keeps the guardrails in the same suite the
 * shell already runs.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

/** Walk up from cwd to the repository root. */
function repoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 8; i += 1) {
    if (existsSync(join(dir, "apps", "warband-manager-web", "package.json"))) return dir;
    dir = join(dir, "..");
  }
  throw new Error("Repository root not found.");
}

const ROOT = repoRoot();
const SRC = join(ROOT, "apps", "warband-manager-web", "src");
const ADAPTER = join(ROOT, "packages", "typescript", "adapters", "campaign-file");

function walk(dir: string, extensions: readonly string[]): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...walk(full, extensions));
    } else if (extensions.some((ext) => full.endsWith(ext))) {
      out.push(full);
    }
  }
  return out;
}

function violationsIn(files: readonly string[], patterns: readonly [RegExp, string][]): string[] {
  const violations: string[] = [];
  for (const file of files) {
    const text = readFileSync(file, "utf8");
    for (const [pattern, label] of patterns) {
      if (pattern.test(text)) {
        violations.push(`${file}: ${label}`);
      }
    }
  }
  return violations;
}

describe("Architecture: UI and adapter boundaries", () => {
  it("UI sources never load YAML directly", () => {
    const violations = violationsIn(
      walk(SRC, [".ts", ".tsx"]).filter((file) => !file.endsWith(".test.ts") && !file.endsWith(".test.tsx")),
      [
        [/\bfrom\s+["']yaml["']/, "yaml package import"],
        [/\bjsyaml\b/, "js-yaml usage"],
        [/\brequire\s*\(\s*["']yaml/, "yaml require()"],
      ],
    );
    expect(violations).toEqual([]);
  });

  it("no source uses browser storage for campaigns (in-memory session policy)", () => {
    const files = [
      ...walk(SRC, [".ts", ".tsx"]),
      ...walk(join(ROOT, "packages", "typescript", "domain"), [".ts"]),
      ...walk(join(ROOT, "packages", "typescript", "application"), [".ts"]),
      ...walk(join(ROOT, "packages", "typescript", "adapters"), [".ts"]),
    ].filter((file) => !file.includes(".test.") && !file.includes("node_modules"));
    const violations = violationsIn(files, [
      [/\blocalStorage\b/, "localStorage usage"],
      [/\bsessionStorage\b/, "sessionStorage usage"],
      [/\bindexedDB\b/, "indexedDB usage"],
    ]);
    expect(violations).toEqual([]);
  });

  it("the campaign-file adapter holds no business rules or python bindings", () => {
    const violations = violationsIn(
      walk(ADAPTER, [".ts"]).filter((file) => !file.includes(".test.")),
      [
        [/mordheim_campaign/, "python package import"],
        [/\bimport\s+cv2\b|\bfrom\s+cv2\b/, "cv2 import"],
        [/Combat\s*Lab/i, "Combat Lab reference"],
        [/\bnumpy\b/, "numpy import"],
        [/\btkinter\b/, "tkinter import"],
      ],
    );
    expect(violations).toEqual([]);
  });
});
