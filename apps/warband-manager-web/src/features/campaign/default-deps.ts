/**
 * P5.2 composition: builds the real application service with injected ports.
 *
 * The knowledge reader is a **fake** until P4.3's adapter is integrated here
 * (its artefact needs wiring into the browser bundle); the file port is now
 * the **real P3.2 adapter**. Both swaps stay one-line changes in this file.
 */

import { createCampaignAppService } from "./types";
import type { CampaignAppService } from "./types";
import type { CampaignFilePort, KnowledgeReader } from "./types";

import { CampaignFileV4Adapter } from "@adapters/campaign-file/index";
import { FakeKnowledgeReader } from "./fake-knowledge-reader";

export function createDefaultDeps(): CampaignAppService {
  const files: CampaignFilePort = new CampaignFileV4Adapter();
  const knowledge: KnowledgeReader = new FakeKnowledgeReader();
  return createCampaignAppService({ files, knowledge });
}
