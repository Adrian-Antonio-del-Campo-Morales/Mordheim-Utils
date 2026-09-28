/**
 * T11 test support: the produced campaign artefact.
 *
 * The versioned artefact under `outputs/web-public/knowledge` is pre-T09 and
 * publishes neither the 2A/2B bands nor the T10 campaign tables (creation
 * decisions, lifecycle/succession/advance-access clauses, mutation grants,
 * structured market restrictions). The Web product flows of T11 therefore read
 * the **freshly generated** artefact in `build/generated/knowledge-web`, which
 * is produced (never edited) by `tools/knowledge/generate_knowledge_web.py` and
 * is not committed.
 *
 * When that artefact is absent the suite reports the omission instead of
 * asserting against stale data: T12 regenerates the published artefact and these
 * flows run against it there.
 */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

const GENERATED = "build/generated/knowledge-web";

function read(directory: string, file: string): unknown {
  return JSON.parse(readFileSync(resolve(process.cwd(), "..", "..", directory, file), "utf-8"));
}

/** Absolute path of the fresh campaign artefact, or `null` when it is absent. */
export function freshArtefactPath(): string | null {
  const path = resolve(process.cwd(), "..", "..", GENERATED, "knowledge-web.json");
  return existsSync(path) ? path : null;
}

export const MISSING_ARTEFACT_NOTE =
  "The freshly generated campaign artefact (build/generated/knowledge-web) is absent: T10 campaign flows are covered by T10's suites and re-run by T12 after regenerating.";

/**
 * Merged rows of the fresh artefact exactly as the app loads them (main rows +
 * presentation index + prose). A test that needs to publish one more row — for
 * example a band whose hero tables omit a list a printed clause grants — mutates
 * this copy instead of editing the generated files on disk.
 */
export function freshArtefactRaw(): Record<string, unknown> {
  const rulesProse = read(GENERATED, "rules-prose.json") as Record<string, unknown>;
  return {
    ...(read(GENERATED, "knowledge-web.json") as Record<string, unknown>),
    ...(read(GENERATED, "display-text.json") as Record<string, unknown>),
    rules_prose: rulesProse,
  };
}

/** Reader over the fresh artefact (main rows + presentation index + prose). */
export function freshCampaignKnowledge(): ArtefactKnowledgeReader {
  return ArtefactKnowledgeReader.from(freshArtefactRaw());
}
