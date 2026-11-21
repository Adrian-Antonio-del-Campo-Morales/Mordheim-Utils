/**
 * Test support: the produced campaign artefact.
 *
 * The Web product flows read the generated artefact in
 * `outputs/web-public/knowledge`, which is produced (never edited) by
 * `tools/knowledge/generate_knowledge_web.py` — the same path CI generates
 * into before running this suite.
 *
 * The generator splits the published artefact: `knowledge-web.json` is
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
import { readArtefactDocument } from "../../../knowledge/support/kb-artefact";

const GENERATED = "outputs/web-public/knowledge";

/** Absolute path of the fresh campaign artefact, or `null` when it is absent. */
export function freshArtefactPath(): string | null {
  const path = resolve(process.cwd(), "..", "..", GENERATED, "knowledge-web.json");
  return existsSync(path) ? path : null;
}

export const MISSING_ARTEFACT_NOTE =
  "The generated campaign artefact (outputs/web-public/knowledge) is absent: campaign flows are covered by their suites and re-run after regenerating.";

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
