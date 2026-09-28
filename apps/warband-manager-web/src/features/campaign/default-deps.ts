/**
 * Composition root for the browser campaign service.
 *
 * Production fetches the generated KB artefact once at startup and uses the
 * real v5 file adapter. The synchronous fake remains test-only fallback data
 * while that fetch is pending or when the static asset cannot be loaded.
 */

import { createCampaignAppService } from "./types";
import type { CampaignAppService } from "./types";
import type { CampaignFilePort, KnowledgeReader } from "./types";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { FakeKnowledgeReader } from "./fake-knowledge-reader";

/** Public URL of the KB artefact (Vite serves `public/` at the base path). */
export const KNOWLEDGE_ARTEFACT_URL = "knowledge/knowledge-web.json";

function filePort(): CampaignFilePort {
  return new CampaignFileV5Adapter();
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

/**
 * T12 fase D — load the deferred campaign catalogue (equipment + campaign
 * sections) on demand. The initial document publishes neither, so every flow
 * that builds or equips a warband, prices a market, moves equipment, prices the
 * campaign inventory, resolves an item/campaign name or writes the PDF calls
 * this first. The reader coalesces concurrent calls and never downloads twice,
 * so calling it on every flow entry is the intended usage.
 */
export async function ensureCampaignCatalogue(
  knowledge: ArtefactKnowledgeReader,
): Promise<void> {
  await Promise.all([
    knowledge.ensureCatalogue("items"),
    knowledge.ensureCatalogue("campaign"),
  ]);
}

/**
 * Explicit whole-artefact load for tools and diagnostics: same URL + digest
 * mechanism, every family loaded before it returns. The product never uses it —
 * the browser loads the catalogue lazily.
 */
export async function loadFullKnowledge(
  url: string = KNOWLEDGE_ARTEFACT_URL,
): Promise<ArtefactKnowledgeReader> {
  return ArtefactKnowledgeReader.fromFullUrl(url);
}
