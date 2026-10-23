/**
 * Built-bundle guardrails for the Warband Manager product.
 *
 * These two checks were split out of the web architecture suite: they inspect
 * `dist/` after a build, so they belong to the application's packaging scope.
 * They skip when `dist/` is absent, exactly as before the move.
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
const DIST = join(ROOT, "apps", "warband-manager-web", "dist");

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

describe("Bundle guardrails (post-build)", () => {
  const distExists = existsSync(DIST);

  it.skipIf(!distExists)("the built bundle excludes desktop-only tech", () => {
    const bundles = walk(DIST, [".js", ".css", ".html"]);
    expect(bundles.length, "dist has bundle files").toBeGreaterThan(0);
    // Scanning minified output: look for the *tokens* these techs must
    // contribute, not just their package names (which could appear in a
    // comment-less string by coincidence).
    const violations = violationsIn(bundles, [
      [/\bnumpy\b|\bnp\.array\b|\bndarray\b/, "numpy in bundle"],
      [/\bCython\b/, "Cython in bundle"],
      [/\btkinter\b|\bTclTk\b/, "tkinter in bundle"],
      [/\bCombatLab\b|\bcombat_lab\b/, "Combat Lab in bundle"],
    ]);
    expect(violations).toEqual([]);
  });

  it.skipIf(!distExists)("no .mordheim campaign file ships in dist", () => {
    const all = walk(DIST, [".mordheim"]);
    expect(all).toEqual([]);
  });
});
