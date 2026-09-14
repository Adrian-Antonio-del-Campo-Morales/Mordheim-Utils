/**
 * React wiring for the isolated draft workflow component.
 *
 * The draft document is created by the workflow and held in local state until
 * commit hands it to the caller. The production shell uses the generated KB
 * artefact and the service-backed `DraftWorkspace`; this hook remains useful
 * for focused component tests.
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
 * This hook is retained for isolated draft-component tests; the production
 * shell uses the generated artefact and the service-backed DraftWorkspace.
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
