/**
 * TS mirror of the shared malformed-save parity vectors. Applies the same JSON-pointer mutations to the same base fixture
 * as tests/python/web/parity/vectors_python_test.py and expects the adapter to
 * agree with each vector's `expected` outcome.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { parseCampaignFileDetailed } from "@adapters/campaign-file/index";

const ROOT = resolve(__dirname, "../..");
const VECTORS_PATH = resolve(ROOT, "tests/fixtures/parity/vectors/malformed_save.json");
const FIXTURES = resolve(ROOT, "contracts/campaign-file-v5/fixtures");

interface Mutation {
  op: string;
  value?: unknown;
  warrior_id?: string;
}

interface Vector {
  id: string;
  base: string;
  pointer: string;
  value: unknown;
  expected: "reject" | "accept";
  mutation?: Mutation;
}

interface VectorFile {
  vectors: Vector[];
}

const file: VectorFile = JSON.parse(readFileSync(VECTORS_PATH, "utf-8"));
const vectors = file.vectors;

function baseDocument(base: string): Record<string, unknown> {
  const doc = JSON.parse(readFileSync(resolve(FIXTURES, base), "utf-8")) as Record<string, unknown>;
  delete doc.view;
  return doc;
}

function setPointer(doc: Record<string, unknown>, pointer: string, value: unknown): void {
  const parts = pointer.split("/").slice(1).map((p) => p.replace(/~1/g, "/").replace(/~0/g, "~"));
  let node: unknown = doc;
  for (const part of parts.slice(0, -1)) {
    node = Array.isArray(node) ? node[Number(part)] : (node as Record<string, unknown>)[part];
  }
  const last = parts[parts.length - 1];
  if (Array.isArray(node)) {
    node[Number(last)] = value;
  } else {
    (node as Record<string, unknown>)[last] = value;
  }
}

function applyMutation(doc: Record<string, unknown>, vector: Vector): Record<string, unknown> {
  const op = vector.mutation?.op ?? "set";
  const campaign = doc.campaign as Record<string, unknown>;
  if (op === "set") {
    setPointer(doc, vector.pointer, vector.value);
    return doc;
  }
  if (op === "set_with_state") {
    const warriors = JSON.parse(JSON.stringify(campaign.warriors)) as Array<{
      equipment?: Array<{ quantity: unknown }>;
    }>;
    for (const w of warriors) {
      for (const eq of w.equipment ?? []) {
        eq.quantity = vector.value;
      }
    }
    campaign.states = [{ number: 0, roster: warriors }];
    return doc;
  }
  if (op === "set_nonfinite") {
    campaign.starting_gold = Number.NaN; // JSON.stringify -> null; schema rejects
    return doc;
  }
  // post-battle pending-reference mutations: the incomplete row is LAST
  const pending = (campaign.post_battles as Array<Record<string, unknown>>).slice(-1)[0];
  if (op === "duplicate_followup") {
    pending.pending_follow_ups = [
      { id: "same", step: 0, type: "prisoner", warrior_id: vector.mutation!.warrior_id },
      { id: "same", step: 0, type: "prisoner", warrior_id: vector.mutation!.warrior_id },
    ];
    return doc;
  }
  if (op === "orphan_advance") {
    pending.pending_advances = [
      { warrior_id: "absent-warrior", threshold: 20, table: "hero", committed: false },
    ];
    return doc;
  }
  if (op === "duplicate_advance") {
    const advance = {
      warrior_id: vector.mutation!.warrior_id,
      threshold: 20,
      table: "hero",
      committed: false,
    };
    pending.pending_advances = [advance, { ...advance }];
    return doc;
  }
  if (op === "completed_advance_for_lost_warrior") {
    pending.pending_advances = [
      { warrior_id: "lost-warrior", threshold: 20, table: "hero", committed: true },
    ];
    return doc;
  }
  throw new Error(`unknown mutation op: ${op}`);
}

describe("shared malformed-save parity vectors (TS mirror)", () => {
  it("exposes the same vector ids the Python runner consumes", () => {
    expect(vectors.length).toBe(29);
  });

  for (const vector of vectors) {
    it(`parity: ${vector.id}`, () => {
      const doc = applyMutation(baseDocument(vector.base), vector);
      const result = parseCampaignFileDetailed(JSON.stringify(doc));
      if (vector.expected === "reject") {
        expect(result.ok, `${vector.id} should be rejected`).toBe(false);
      } else {
        expect(result.ok, `${vector.id} should be accepted`).toBe(true);
      }
    });
  }
});
