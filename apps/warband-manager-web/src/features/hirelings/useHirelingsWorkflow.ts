/**
 * P6.7: hooks the hirelings/trading workflow into the app.
 *
 * The workflow needs a listing-capable knowledge source plus the use cases.
 * `useCampaignApp()` hides the service internals by design, so this hook
 * rebuilds the workflow from `createDefaultDeps()` — the same composition
 * root the shell uses — and keeps it stable for the component's lifetime.
 * When the real P4.3 adapter lands in `default-deps.ts`, this hook picks it
 * up with no further change (the adapter implements the same listings
 * surface).
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
      itemName: (itemId, locale) =>
        typeof candidate.itemName === "function" ? candidate.itemName(itemId, locale) : itemId,
    };
  }
  // A reader without listings: empty catalogues (the UI shows empty states).
  return {
    campaignRows: () => [],
    campaignSection: () => ({}),
    itemName: (itemId) => itemId,
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
