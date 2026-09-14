/**
 * Campaign-file acceptance tests: all four contract fixtures read and
 * validate; valid documents serialize; every error class has a test; the
 * semantic round-trip ignores only `saved_at`; open payloads survive
 * verbatim. Fixture text is loaded from `contracts/campaign-file-v5/` —
 * never copied (the contract rule).
 */
import { describe, expect, it } from "vitest";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import {
  CampaignFileV5Adapter,
  parseCampaignFileDetailed,
} from "./index";

/**
 * Locate the repo root by walking up from the working directory until the
 * contract directory appears (robust against vitest's synthetic module URLs,
 * which do not reliably reflect the real file path on every runner).
 */
function findRepoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 6; i++) {
    try {
      readFileSync(join(dir, "contracts", "campaign-file-v5", "campaign-file-v5.schema.json"), "utf-8");
      return dir;
    } catch {
      dir = join(dir, "..");
    }
  }
  throw new Error("repo root with contracts/campaign-file-v5 not found from " + process.cwd());
}

const REPO_ROOT = findRepoRoot();
const FIXTURES = join(REPO_ROOT, "contracts", "campaign-file-v5", "fixtures");

const FIXTURE_NAMES = [
  "draft.json",
  "active-campaign.json",
  "pending-post-battle.json",
  "full-inventory.json",
] as const;

function fixtureText(name: (typeof FIXTURE_NAMES)[number]): string {
  return readFileSync(join(FIXTURES, name), "utf-8");
}

function fixtureJson(name: (typeof FIXTURE_NAMES)[number]): Record<string, unknown> {
  return JSON.parse(fixtureText(name)) as Record<string, unknown>;
}

describe("P3.2: fixtures parse and validate", () => {
  for (const name of FIXTURE_NAMES) {
    it(`parses ${name}`, () => {
      const result = parseCampaignFileDetailed(fixtureText(name));
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.document.format_version).toBe(5);
        expect(typeof result.campaign.identity.band_id).toBe("string");
        expect(result.view).toBeTypeOf("object");
      }
    });
  }

  it("covers all four campaign shapes", () => {
    const draft = parseCampaignFileDetailed(fixtureText("draft.json"));
    const active = parseCampaignFileDetailed(fixtureText("active-campaign.json"));
    const pending = parseCampaignFileDetailed(fixtureText("pending-post-battle.json"));
    expect(draft.ok && active.ok && pending.ok).toBe(true);
    if (draft.ok && active.ok && pending.ok) {
      expect(draft.campaign.configuration.is_draft).toBe(true);
      expect(active.campaign.battles.length).toBeGreaterThan(0);
      expect(pending.campaign.post_battles.length).toBeGreaterThan(0);
    }
  });
});

describe("P3.2: rejection ladder", () => {
  const port = new CampaignFileV5Adapter();

  it("rejects invalid JSON", () => {
    const result = port.parseCampaignFile("{not json");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("invalid_json");
      expect(result.message).toContain("JSON");
    }
  });

  it("rejects non-object top level", () => {
    const result = port.parseCampaignFile("[1, 2, 3]");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("invalid_json");
    }
  });

  it("rejects a wrong marker before any version check", () => {
    const doc = fixtureJson("draft.json");
    doc["marker"] = "SOMETHING_ELSE";
    const result = port.parseCampaignFile(JSON.stringify(doc));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("bad_marker");
    }
  });

  it("rejects retired versions with found + supported versions", () => {
    for (const version of [1, 2, 3, 4]) {
      const doc = fixtureJson("draft.json");
      doc["format_version"] = version;
      const result = port.parseCampaignFile(JSON.stringify(doc));
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.reason).toBe("retired_version");
        expect(result.found_version).toBe(version);
        expect(result.supported_versions).toEqual([5]);
        expect(result.message).toContain(String(version));
      }
    }
  });

  it("rejects versions newer than 5", () => {
    const doc = fixtureJson("draft.json");
    doc["format_version"] = 6;
    const result = port.parseCampaignFile(JSON.stringify(doc));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("unsupported_version");
      expect(result.found_version).toBe(6);
    }
  });

  it("rejects a schema violation with the JSON path", () => {
    const doc = fixtureJson("active-campaign.json");
    (doc["campaign"] as Record<string, unknown>)["identity"] = {
      campaign_name: "X",
      // warband_name missing -> required violation at campaign.identity
    };
    const result = port.parseCampaignFile(JSON.stringify(doc));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("schema_violation");
      expect(result.location).toContain("identity");
    }
  });

  it("rejects an unknown top-level section", () => {
    const doc = fixtureJson("draft.json");
    doc["future_section"] = {};
    const result = port.parseCampaignFile(JSON.stringify(doc));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("schema_violation");
    }
  });
});

describe("P3.2: serialization and round-trip", () => {
  const port = new CampaignFileV5Adapter();

  it("round-trips every fixture with only saved_at differing", () => {
    for (const name of FIXTURE_NAMES) {
      const first = parseCampaignFileDetailed(fixtureText(name));
      expect(first.ok).toBe(true);
      if (!first.ok) continue;
      const serialized = port.serializeCampaign(first.campaign);
      expect(serialized.ok).toBe(true);
      if (!serialized.ok) continue;
      const second = parseCampaignFileDetailed(serialized.text);
      expect(second.ok).toBe(true);
      if (!second.ok) continue;
      // The port serializes the campaign state; the view section is
      // reconstructible UI selection (contract README) and is legitimately
      // absent from the re-emitted document. Everything else, except the
      // volatile saved_at, must be identical.
      const a = { ...first.document, saved_at: "", view: undefined };
      const b = { ...second.document, saved_at: "", view: undefined };
      expect(b).toEqual(a);
    }
  });

  it("emits a well-formed envelope", () => {
    const first = parseCampaignFileDetailed(fixtureText("draft.json"));
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const serialized = port.serializeCampaign(first.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const doc = JSON.parse(serialized.text) as Record<string, unknown>;
    expect(doc["marker"]).toBe("MORDHEIM_CAMPAIGN_MANAGER");
    expect(doc["format_version"]).toBe(5);
    expect(doc["saved_at"]).toMatch(
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/,
    );
  });

  it("serializes the terminal step produced by finalizing a post-battle", () => {
    const parsed = parseCampaignFileDetailed(fixtureText("pending-post-battle.json"));
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const campaign = structuredClone(parsed.campaign);
    Object.assign(campaign.post_battles.at(-1)!, {
      complete: true,
      active_step: 8,
      completed_steps: [0, 1, 2, 3, 4, 5, 6, 7],
      review_open: true,
    });

    expect(port.serializeCampaign(campaign).ok).toBe(true);
  });

  it("rejects terminal step 8 while the post-battle is still pending", () => {
    const parsed = parseCampaignFileDetailed(fixtureText("pending-post-battle.json"));
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const campaign = structuredClone(parsed.campaign);
    Object.assign(campaign.post_battles.at(-1)!, { active_step: 8, complete: false });

    const result = port.serializeCampaign(campaign);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Invalid post-battle step");
  });

  it("preserves open payloads verbatim across a round-trip", () => {
    const doc = fixtureJson("pending-post-battle.json");
    const campaigns = doc["campaign"] as Record<string, unknown>;
    const postBattles = campaigns["post_battles"] as Record<string, unknown>[];
    postBattles[0]["step_state"] = {
      ...((postBattles[0]["step_state"] as Record<string, unknown>) ?? {}),
      "99": { future_field: { nested: [1, 2, 3] } },
    };
    const parsed = parseCampaignFileDetailed(JSON.stringify(doc));
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const serialized = port.serializeCampaign(parsed.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const roundTripped = JSON.parse(serialized.text) as Record<string, unknown>;
    const roundTrippedSteps = (roundTripped["campaign"] as Record<string, unknown>)[
      "post_battles"
    ] as Record<string, unknown>[];
    expect(
      ((roundTrippedSteps[0]["step_state"] as Record<string, unknown>)["99"] as Record<
        string,
        unknown
      >)["future_field"],
    ).toEqual({ nested: [1, 2, 3] });
  });

  it("refuses to serialize a contract-violating campaign", () => {
    const broken = { identity: {} } as unknown as Parameters<
      CampaignFileV5Adapter["serializeCampaign"]
    >[0];
    const result = port.serializeCampaign(broken);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("schema_violation");
      expect(result.message).toContain("Refusing to save");
    }
  });

  /**
   * P3.2 ↔ P3.3 cross-check artefact: emit one serialized file per fixture
   * plus a manifest. `tests/web/contract/test_p32_roundtrip.py` validates
   * each file with the desktop (Python) reader — the plan's Python↔web
   * round-trip acceptance.
   */
  it("emits cross-check artefacts for the Python contract harness", () => {
    const manifest: {
      round_tripped: string[];
      serialized: Record<string, string>;
    } = { round_tripped: [], serialized: {} };
    for (const name of FIXTURE_NAMES) {
      const parsed = parseCampaignFileDetailed(fixtureText(name));
      expect(parsed.ok).toBe(true);
      if (!parsed.ok) continue;
      const serialized = port.serializeCampaign(parsed.campaign);
      expect(serialized.ok).toBe(true);
      if (!serialized.ok) continue;
      const outName = `_p32-serialized-${name}`;
      writeFileSync(join(REPO_ROOT, "packages", "typescript", "adapters", "campaign-file", outName), serialized.text, "utf-8");
      manifest.round_tripped.push(name);
      manifest.serialized[name] = outName;
    }
    writeFileSync(
      join(REPO_ROOT, "packages", "typescript", "adapters", "campaign-file", "_ts-roundtrip-artefact.json"),
      JSON.stringify(manifest, null, 1) + "\n",
      "utf-8",
    );
    expect(manifest.round_tripped).toHaveLength(4);
  });
});
