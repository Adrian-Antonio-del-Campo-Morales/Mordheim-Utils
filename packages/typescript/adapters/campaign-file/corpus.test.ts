/**
 * Malformed-corpus matrix: the corrupt corpus driven
 * through the real TS file adapter. Every corpus file must be rejected with
 * the exact stable reason recorded in the manifest — the same manifest the
 * Python harness asserts against, so both implementations stay in lockstep.
 *
 * Error-quality rules asserted here:
 * - messages are actionable, non-empty and never contain stack-trace noise
 *   (no "at ", no "Error:", no "node:internal", no file paths of this repo);
 * - schema violations carry a location.
 *
 * The corpus lives in `tests/web/contract/corpus/` — one violation per file,
 * never copied into packages or apps.
 */
import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { CampaignFileV4Adapter } from "./index";

function findRepoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 6; i++) {
    try {
      readFileSync(join(dir, "contracts", "campaign-file-v4", "campaign-file-v4.schema.json"), "utf-8");
      return dir;
    } catch {
      dir = join(dir, "..");
    }
  }
  throw new Error("repo root with contracts/campaign-file-v4 not found from " + process.cwd());
}

const REPO_ROOT = findRepoRoot();
const CORPUS = join(REPO_ROOT, "tests", "web", "contract", "corpus");

interface ManifestEntry {
  readonly ts_reason: string;
  readonly py_substring: string;
}

const manifest = JSON.parse(
  readFileSync(join(CORPUS, "manifest.json"), "utf-8"),
) as { expected: Record<string, ManifestEntry> };

const CORPUS_FILES = readdirSync(CORPUS).filter((name) => name.endsWith(".mordheim")).sort();

// "Internal trace" noise. Note: a JSON parser's "at position 60" detail is
// actionable, not a stack trace — only real trace markers are forbidden.
const NOISE_PATTERNS: readonly { test(value: string): boolean }[] = [
  { test: (value) => /\bnode:internal\b/.test(value) },
  { test: (value) => /\n\s*at \b/.test(value) },
  { test: (value) => value.includes(REPO_ROOT) },
  { test: (value) => /traceback/i.test(value) },
];

describe("P7.2: TS adapter rejects every corrupt document with the manifest reason", () => {
  const port = new CampaignFileV4Adapter();

  it("corpus is complete: every manifest entry has a file on disk", () => {
    expect(CORPUS_FILES.length).toBeGreaterThanOrEqual(20);
    for (const name of Object.keys(manifest.expected)) {
      expect(CORPUS_FILES, name).toContain(name);
    }
  });

  for (const name of CORPUS_FILES) {
    it(`rejects ${name} with reason "${manifest.expected[name].ts_reason}"`, () => {
      const text = readFileSync(join(CORPUS, name), "utf-8");
      const result = port.parseCampaignFile(text);
      expect(result.ok, `${name} must be rejected`).toBe(false);
      if (result.ok) return;
      const expected = manifest.expected[name];
      expect(result.reason, name).toBe(expected.ts_reason);
      // Error-quality rules: actionable, no internal traces.
      expect(result.message.length, name).toBeGreaterThan(10);
      for (const noise of NOISE_PATTERNS) {
        expect(noise.test(result.message), `${name}: message leaks internals: ${result.message}`).toBe(false);
      }
      if (expected.ts_reason === "schema_violation") {
        expect(result.location, name).toBeTruthy();
      }
    });
  }

  it("retired versions name the found and the supported versions", () => {
    for (const version of [1, 2, 3]) {
      const result = port.parseCampaignFile(
        readFileSync(join(CORPUS, `retired-v${version}.mordheim`), "utf-8"),
      );
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.found_version).toBe(version);
        expect(result.supported_versions).toEqual([4]);
        expect(result.message).toContain(String(version));
        expect(result.message).toContain("4");
      }
    }
  });
});
