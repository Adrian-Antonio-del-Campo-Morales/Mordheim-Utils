/**
 * TS-side gate for the desktop→web test traceability manifest (Agent 0,
 * parity lane). The Python gate (tests/web/parity/python_manifest_test.py)
 * owns regeneration identity (it can rerun pytest); this mirror verifies
 * structural invariants so both toolchains consume the same contract.
 */
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = resolve(__dirname, "../..");
const MANIFEST = resolve(ROOT, "tests/web/parity/campaign-test-manifest.json");

interface ManifestRow {
  source_file: string;
  source_test: string;
  behavior_id: string;
  desktop_category: string;
  web_disposition: "M" | "A" | "U" | "I" | "S" | "X";
  web_target: string | null;
  owner: string;
  status: string;
  parity_vector: string | null;
  exclusion_reason: string | null;
  evidence: string | null;
  follow_up: string | null;
}

interface Manifest {
  plan: string;
  deterministic: boolean;
  sources: string[];
  counts: Record<string, number>;
  total: number;
  rows: ManifestRow[];
}

const VALID_STATUSES = new Set(["implemented", "partial", "blocked", "excluded", "pending"]);

const manifest: Manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));

describe("campaign test manifest (traceability matrix)", () => {
  it("exists and declares its scope", () => {
    expect(manifest.plan).toBe("campaign-web-parity");
    expect(manifest.deterministic).toBe(true);
    expect(manifest.rows.length).toBeGreaterThan(0);
  });

  it("counts and total match the rows", () => {
    const counts: Record<string, number> = {};
    for (const row of manifest.rows) {
      counts[row.web_disposition] = (counts[row.web_disposition] ?? 0) + 1;
    }
    expect(manifest.counts).toEqual(counts);
    expect(manifest.total).toBe(manifest.rows.length);
  });

  it("every row is complete", () => {
    for (const row of manifest.rows) {
      expect(row.source_file, JSON.stringify(row).slice(0, 120)).toBeTruthy();
      expect(row.source_test).toBeTruthy();
      expect(row.behavior_id).toBeTruthy();
      expect(row.owner).toBeTruthy();
      expect(VALID_STATUSES.has(row.status), row.source_test).toBe(true);
      expect(row.status, row.source_test).not.toBe("pending");
      if (row.web_disposition !== "X") {
        expect(row.web_target, `${row.source_test} has no web_target`).toBeTruthy();
        expect(existsSync(resolve(ROOT, row.web_target!)), row.web_target!).toBe(true);
        expect(row.status).not.toBe("excluded");
      } else {
        expect(row.status).toBe("excluded");
      }
      if (row.status === "implemented") {
        expect(row.evidence, row.source_test).toBeTruthy();
        expect(row.follow_up, row.source_test).toBeNull();
      }
      if (row.status === "partial" || row.status === "blocked") {
        expect(row.evidence, row.source_test).toBeTruthy();
        expect(row.follow_up, row.source_test).toBeTruthy();
      }
    }
  });

  it("every exclusion carries a documented reason", () => {
    for (const row of manifest.rows) {
      if (row.web_disposition === "X") {
        expect(row.exclusion_reason, row.source_test).toBeTruthy();
      } else {
        expect(row.exclusion_reason).toBeNull();
      }
    }
  });

  it("no duplicate source rows", () => {
    const keys = manifest.rows.map((r) => `${r.source_file}::${r.source_test}`);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("rows are sorted (determinism) and sources exist", () => {
    const sorted = [...manifest.rows].sort(
      (a, b) =>
        (a.source_file < b.source_file ? -1 : a.source_file > b.source_file ? 1 : 0) ||
        (a.source_test < b.source_test ? -1 : a.source_test > b.source_test ? 1 : 0),
    );
    expect(manifest.rows).toEqual(sorted);
    for (const source of manifest.sources) {
      expect(existsSync(resolve(ROOT, source)), source).toBe(true);
    }
  });
});
