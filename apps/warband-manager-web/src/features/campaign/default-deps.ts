/**
 * P5.2 composition: builds the real application service with injected ports.
 *
 * Both ports are now **real**: the P3.2 v4 file adapter and the P4.3 KB
 * adapter (P5.2 final acceptance, per the KB bundling decision in
 * `docs/decisions/web-migration.md`). The artefact is a static asset under
 * `public/knowledge/knowledge-web.json` (staged by CI before the build,
 * gitignored in the repo) fetched once at startup.
 *
 * Two constructors:
 * - `createDefaultDepsAsync()` — the production path; fetches and validates
 *   the artefact, surfacing typed `KnowledgeReaderError`s to the caller so
 *   the shell can render a KB loading/failure state.
 * - `createDefaultDeps()` — synchronous fallback that keeps the
 *   artefact-shaped fake. Used by tests and by components that render
 *   before the async swap resolves; it implements the same listings surface
 *   so feature workflows behave identically.
 */

import { createCampaignAppService } from "./types";
import type { CampaignAppService } from "./types";
import type { CampaignFilePort, KnowledgeReader } from "./types";

import { CampaignFileV4Adapter } from "@adapters/campaign-file/index";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { FakeKnowledgeReader } from "./fake-knowledge-reader";

/** Public URL of the KB artefact (Vite serves `public/` at the base path). */
export const KNOWLEDGE_ARTEFACT_URL = "knowledge/knowledge-web.json";

function filePort(): CampaignFilePort {
  return new CampaignFileV4Adapter();
}

export function createService(knowledge: KnowledgeReader): CampaignAppService {
  return createCampaignAppService({ files: filePort(), knowledge });
}

/**
 * Production composition: real file port + real KB reader fetched from the
 * static artefact. Rejects with `KnowledgeReaderError` on network, HTTP,
 * JSON or schema failure — callers map that to the error panel.
 */
export async function createDefaultDepsAsync(
  url: string = KNOWLEDGE_ARTEFACT_URL,
): Promise<CampaignAppService> {
  const knowledge = await ArtefactKnowledgeReader.fromUrl(url);
  return createService(knowledge);
}

/** Synchronous fallback (tests; pre-swap render). Fake reader, real files. */
export function createDefaultDeps(): CampaignAppService {
  const knowledge: KnowledgeReader = new FakeKnowledgeReader();
  return createService(knowledge);
}

export async function loadKnowledge(
  url: string = KNOWLEDGE_ARTEFACT_URL,
): Promise<ArtefactKnowledgeReader> {
  return ArtefactKnowledgeReader.fromUrl(url);
}
