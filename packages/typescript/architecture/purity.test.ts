import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * P3.4 guardrail (plan §2.4 permanent exclusions + §13 DoD): the domain and
 * application layers must stay free of UI, browser and storage dependencies.
 * Verified by scanning every source file's import statements.
 *
 * The regexes deliberately skip `.test.ts` files (tests may import vitest)
 * and only scan real sources in domain/ and application/.
 */

const ROOT = fileURLToPath(new URL("..", import.meta.url));

const LAYERS = ["domain", "application"];

const FORBIDDEN: readonly [RegExp, string][] = [
  [/\bfrom\s+["']react["']/, "react import"],
  [/\bfrom\s+["']react-dom/, "react-dom import"],
  [/\bfrom\s+["']@testing-library/, "testing-library import"],
  [/\bfrom\s+["']vite/, "vite import"],
  [/\bfrom\s+["']vitest["']/, "vitest import"],
  [/\bfrom\s+["']jsdom/, "jsdom import"],
  [/\bfrom\s+["']yaml/, "yaml import"],
  [/\blocalStorage\b/, "localStorage usage"],
  [/\bindexedDB\b/, "indexedDB usage"],
  [/\bwindow\./, "window usage"],
  [/\bdocument\.getElementById\b/, "document usage"],
  [/\bdocument\.createElement\b/, "document usage"],
  [/\bdocument\.querySelector/, "document usage"],
  [/\brequire\(/, "require() usage"],
];

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...walk(full));
    } else if (full.endsWith(".ts") && !full.endsWith(".test.ts")) {
      out.push(full);
    }
  }
  return out;
}

describe("P3.4 architecture: domain/application purity", () => {
  it("no source file in domain/ or application/ imports UI, browser or storage", () => {
    const violations: string[] = [];
    for (const layer of LAYERS) {
      const files = walk(join(ROOT, layer));
      expect(files.length, `layer ${layer} has source files`).toBeGreaterThan(0);
      for (const file of files) {
        const text = readFileSync(file, "utf8");
        for (const [pattern, label] of FORBIDDEN) {
          if (pattern.test(text)) {
            violations.push(`${file}: ${label}`);
          }
        }
      }
    }
    expect(violations).toEqual([]);
  });

  it("domain never imports from application (dependency direction)", () => {
    const violations: string[] = [];
    for (const file of walk(join(ROOT, "domain"))) {
      const text = readFileSync(file, "utf8");
      if (/\bfrom\s+["'].*application/.test(text)) {
        violations.push(file);
      }
    }
    expect(violations).toEqual([]);
  });
});
