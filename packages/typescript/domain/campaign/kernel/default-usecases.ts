/**
 * P3.5: rewire the application-facing default use cases to the real kernel
 * behaviour. Replaces the P5.1 `notPorted` stubs; the frozen
 * `CampaignUseCases` surface is unchanged.
 *
 * `createDefaultUseCases` accepts an optional `KnowledgeReader` so the
 * KB-dependent use cases that the frozen surface calls without a reader
 * (`composeDraft`) still resolve profiles through the port — P5.1's service
 * constructs this factory with `deps.knowledge`.
 */

import type {
  CampaignDocument,
  CampaignUseCases,
  IdString,
  KnowledgeReader,
  MomentSelection,
  UseCaseResult,
} from "../index";
import type { AdvanceChoiceInput, DraftCompositionInput, OpenPayloadInput, RecordBattleInput } from "./usecases";
import { rejected } from "./rejections";
import { withView, validateStructure } from "./document";
import { composeDraft, createDraft } from "./create-draft";
import { commitInitialWarband } from "./commit-warband";
import { recordBattle } from "./record-battle";
import { resolvePostBattleStep } from "./post-battle-steps";
import { assignEquipment } from "./equipment";
import type { AssignEquipmentInput } from "./equipment";
import { applyAdvance, hireHireling } from "./hirelings";
import { buyTradingItem, sellStashItem } from "./trading";
import type { BuyTradingItemInput, SellStashItemInput } from "./trading";
import { selectedWarbandVariant, warbandVariants } from "../band-variants";

export type { BuyTradingItemInput, SellStashItemInput };

export type { AssignEquipmentInput };

/** Neutral reader used when no port is injected: every lookup misses. */
const nullReader: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => nullReader.queryKnowledge(q)),
};

export function createDefaultUseCases(knowledge: KnowledgeReader = nullReader): CampaignUseCases {
  return {
    createDraft: (bandId: IdString, reader: KnowledgeReader): UseCaseResult =>
      createDraft(bandId, reader),

    composeDraft: (document: CampaignDocument, input: DraftCompositionInput): UseCaseResult =>
      composeDraft(document, input, knowledge),

    commitInitialWarband: (document: CampaignDocument, reader: KnowledgeReader): UseCaseResult => {
      const variants = warbandVariants(reader, document.campaign.identity.band_id);
      if (variants.length && !selectedWarbandVariant(reader, document.campaign.identity.band_id, document.campaign.identity.mercenary_variant)) {
        return rejected("invalid_input", "Choose a valid warband variant before committing the initial warband.");
      }
      return commitInitialWarband(document);
    },

    selectMoment: (document: CampaignDocument, moment: MomentSelection): UseCaseResult => ({
      ok: true,
      state: withView(document, { selected_moment: moment }),
    }),

    recordBattle: (
      document: CampaignDocument,
      input: RecordBattleInput,
      reader: KnowledgeReader,
    ): UseCaseResult => recordBattle(document, input, reader),

    resolvePostBattleStep: (
      document: CampaignDocument,
      battleNumber: number,
      input: OpenPayloadInput,
    ): UseCaseResult => resolvePostBattleStep(document, battleNumber, input),

    applyAdvance: (document: CampaignDocument, input: AdvanceChoiceInput): UseCaseResult =>
      applyAdvance(document, input),

    assignEquipment: (
      document: CampaignDocument,
      input: AssignEquipmentInput,
    ): UseCaseResult => assignEquipment(document, input),

    hireHireling: (
      document: CampaignDocument,
      input: { profile_id: IdString },
      reader: KnowledgeReader,
    ): UseCaseResult => hireHireling(document, input, reader),

    buyTradingItem: (document: CampaignDocument, input: BuyTradingItemInput): UseCaseResult =>
      buyTradingItem(document, input),

    sellStashItem: (document: CampaignDocument, input: SellStashItemInput): UseCaseResult =>
      sellStashItem(document, input),

    validateForExport: (document: CampaignDocument): UseCaseResult => validateStructure(document),
  };
}

// Re-exported so feature blocks share one constructor (P6.x convention).
export { rejected };
