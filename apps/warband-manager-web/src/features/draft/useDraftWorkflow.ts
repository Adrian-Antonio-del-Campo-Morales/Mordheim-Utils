/**
 * P6.2: React wiring of the draft workflow.
 *
 * The draft document is *created* by the workflow (not loaded from a file),
 * so the hook holds it in state until the shell stores it via `onDocument`
 * (the P5.2 hook owns service state for file-backed campaigns). Compose and
 * commit mutate the held document through the workflow; `commit` additionally
 * hands the committed document to the shell so the campaign slice takes over.
 */

import { useCallback, useMemo, useState } from "react";

import {
  createDraftWorkflow,
  type WarbandOption,
} from "@app/campaign/features/draft/draft-workflow";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import type { CampaignDocument } from "@domain/campaign/index";
import { FakeKnowledgeReader } from "../campaign/fake-knowledge-reader";

/**
 * Band candidates for the warband picker (mordheim collection). The workflow
 * filters to ids the KB actually resolves, so unknown candidates never reach
 * the UI. P8.1 replaces this list with the generated band index.
 */
const BAND_CANDIDATES = [
  "sisters-of-sigmar",
  "reiklanders",
  "marienburgers",
  "witch-hunters",
  "possessed",
  "undead",
  "vampire-counts",
  "skaven",
  "cult-of-the-possessed",
  "witch-elves",
] as const;

export interface DraftWorkflowView {
  /** Warband options resolvable from the KB (filtered candidates). */
  options: WarbandOption[];
  /** Live composition status, or null when no draft is in progress. */
  status: ReturnType<ReturnType<typeof createDraftWorkflow>["status"]> | null;
  isDraft: boolean;
  error: string | null;
  /** Creates a draft document; it becomes the hook's working document. */
  startDraft(bandId: string, campaignName?: string): Promise<boolean>;
  /** Appends one composition row to the working draft. */
  addRow(row: {
    profile_id: string;
    kind: "hero" | "henchman";
    quantity: number;
    equipment: readonly string[];
  }): Promise<boolean>;
  /** Commits the legal draft; the shell receives State #0 via `onCommitted`. */
  commit(): Promise<boolean>;
  clearError(): void;
}

export function useDraftWorkflow(
  onCommitted: (document: CampaignDocument) => void,
): DraftWorkflowView {
  const knowledge = useMemo(() => new FakeKnowledgeReader(), []);
  const workflow = useMemo(
    () => createDraftWorkflow({ knowledge, useCases: createDefaultUseCases(knowledge) }),
    [knowledge],
  );

  const [document, setDocument] = useState<CampaignDocument | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isDraft = document?.campaign.configuration.is_draft ?? false;
  const status = useMemo(
    () => (document && isDraft ? workflow.status(document) : null),
    [workflow, document, isDraft],
  );

  const options = useMemo(
    () => workflow.resolveWarbandOptions(BAND_CANDIDATES),
    [workflow],
  );

  const startDraft = useCallback(
    async (bandId: string, campaignName?: string): Promise<boolean> => {
      const result = workflow.startDraft(bandId, campaignName);
      if (!result.ok) {
        setError(result.message);
        return false;
      }
      setDocument(result.document);
      setError(null);
      return true;
    },
    [workflow],
  );

  const addRow = useCallback(
    async (row: {
      profile_id: string;
      kind: "hero" | "henchman";
      quantity: number;
      equipment: readonly string[];
    }): Promise<boolean> => {
      if (!document) {
        setError("Start a draft first.");
        return false;
      }
      const result = workflow.addRow(document, row);
      if (!result.ok) {
        setError(result.message);
        return false;
      }
      setDocument(result.document);
      setError(null);
      return true;
    },
    [workflow, document],
  );

  const commit = useCallback(async (): Promise<boolean> => {
    if (!document) {
      setError("Start a draft first.");
      return false;
    }
    const result = workflow.commit(document);
    if (!result.ok) {
      setError(result.message);
      return false;
    }
    setDocument(result.document);
    onCommitted(result.document);
    setError(null);
    return true;
  }, [workflow, document, onCommitted]);

  return {
    options,
    status,
    isDraft,
    error,
    startDraft,
    addRow,
    commit,
    clearError: () => setError(null),
  };
}
