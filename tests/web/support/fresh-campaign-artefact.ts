/**
 * T11/T12 test support: the produced campaign artefact.
 *
 * The versioned artefact under `outputs/web-public/knowledge` is pre-T09 and
 * publishes neither the 2A/2B bands nor the T10 campaign tables (creation
 * decisions, lifecycle/succession/advance-access clauses, mutation grants,
 * structured market restrictions). The Web product flows of T11 therefore read
 * the **freshly generated** artefact in `build/generated/knowledge-web`, which is
 * produced (never edited) by `tools/knowledge/generate_knowledge_web.py` and
 * is not committed.
 *
 * T12 regenerated the published artefact and split it: `knowledge-web.json` is
 * now the initial document and the campaign catalogue (equipment + campaign
 * sections) travels as a fragment. `readArtefactDocument` merges whatever
 * fragments the directory publishes, so this helper works with both layouts.
 *
 * When the artefact is absent the suite reports the omission instead of
 * asserting against stale data.
 */

import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { readArtefactDocument } from "../../support/kb-artefact";

const GENERATED = "build/generated/knowledge-web";

/** Absolute path of the fresh campaign artefact, or `null` when it is absent. */
export function freshArtefactPath(): string | null {
  const path = resolve(process.cwd(), "..", "..", GENERATED, "knowledge-web.json");
  return existsSync(path) ? path : null;
}

export const MISSING_ARTEFACT_NOTE =
  "The freshly generated campaign artefact (build/generated/knowledge-web) is absent: T10 campaign flows are covered by T10's suites and re-run by T12 after regenerating.";

/**
 * Merged rows of the fresh artefact exactly as the app loads them (initial rows
 * + presentation index + prose + campaign catalogue). A test that needs to
 * publish one more row — for example a band whose hero tables omit a list a
 * printed clause grants — mutates this copy instead of editing the generated
 * files on disk.
 */
export function freshArtefactRaw(): Record<string, unknown> {
  const path = freshArtefactPath();
  if (!path) throw new Error(MISSING_ARTEFACT_NOTE);
  return readArtefactDocument(path);
}

/** Reader over the fresh artefact (every family loaded). */
export function freshCampaignKnowledge(): ArtefactKnowledgeReader {
  return ArtefactKnowledgeReader.from(freshArtefactRaw());
}
