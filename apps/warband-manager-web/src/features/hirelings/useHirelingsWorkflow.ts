import { unavailableText } from "@adapters/knowledge-reader/presentation";
/**
 * Hook the hireling/trading workflow to the listing-capable knowledge reader.
 *
 * The hook accepts the production reader structurally and uses deterministic
 * empty/fake listings only when an isolated component test does not provide
 * one.
 */
import { useMemo } from "react";

import { FakeKnowledgeReader } from "../campaign/fake-knowledge-reader";
import type { KnowledgeReader } from "../campaign/types";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import type { CampaignUseCases } from "@domain/campaign/index";
import {
  createHirelingsWorkflow,
  type KnowledgeListings,
} from "@app/campaign/features/hirelings/hirelings-workflow";

/** Reader → listings bridge (structural; the fake and the adapter both fit). */
function asListings(reader: KnowledgeReader): KnowledgeListings {
  const candidate = reader as unknown as Partial<KnowledgeListings> & KnowledgeReader;
  if (typeof candidate.campaignRows === "function" && typeof candidate.campaignSection === "function") {
    return {
      campaignRows: (section) => candidate.campaignRows!(section),
      campaignSection: (section) => candidate.campaignSection!(section),
      resolveKbText: candidate.resolveKbText?.bind(candidate),
      recordText: candidate.recordText?.bind(candidate),
      itemName: (itemId, locale) =>
        typeof candidate.itemName === "function" ? candidate.itemName(itemId, locale) : unavailableText(locale === "es" ? "es" : "en"),
    };
  }
  // A reader without listings: empty catalogues (the UI shows empty states).
  return {
    campaignRows: () => [],
    campaignSection: () => ({}),
    itemName: (_itemId, locale) => unavailableText(locale === "es" ? "es" : "en"),
  };
}

export function useHirelingsWorkflow(source?: KnowledgeListings & Partial<KnowledgeReader>): ReturnType<typeof createHirelingsWorkflow> {
  return useMemo(() => {
    // The composition root owns the ports; the workflow reads the same
    // listing-capable reader the service dispatches against.
    const knowledge: KnowledgeReader = source && typeof source.queryKnowledge === "function" && typeof source.queryMany === "function"
      ? source as KnowledgeReader
      : new FakeKnowledgeReader();
    const useCases: CampaignUseCases = createDefaultUseCases(knowledge);
    return createHirelingsWorkflow({ listings: source ?? asListings(knowledge), useCases });
  }, [source]);
}
