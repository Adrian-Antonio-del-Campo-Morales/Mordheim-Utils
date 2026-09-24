import { presentationOutput } from "../campaign/presentation-output";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
/**
 * Draft and initial composition UI. Shown beside/instead of the
 * campaign slice when the user starts a new warband: warband selection,
 * roster composition with live limits, and the commit gate to State #0.
 *
 * Accessibility: labelled selects/inputs, `role=alert` error surface,
 * `role=status` for the composition limits, buttons with visible text.
 */

import { useState } from "react";

import { useDraftWorkflow } from "./useDraftWorkflow";
import type { CampaignDocument } from "@domain/campaign/index";

export interface DraftPanelProps {
  /** Receives the committed document (State #0) for the campaign slice. */
  onCommitted: (document: CampaignDocument) => void;
}

export function DraftPanel({ onCommitted }: DraftPanelProps) {
  const locale = useLocale();
  const workflow = useDraftWorkflow(onCommitted);
  const [bandId, setBandId] = useState<string>("");
  const [campaignName, setCampaignName] = useState("");

  const status = workflow.status;
  const canCommit = status !== null && status.legal;

  return (
    <section aria-label={presentationOutput(translate({ key: "draft.landmark" }, locale))}>
      <h2>{presentationOutput(translate({ key: "draft.title" }, locale))}</h2>

      {status === null && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (bandId) void workflow.startDraft(bandId, campaignName.trim() || undefined);
          }}
        >
          <label htmlFor="warband-select">{presentationOutput(translate({ key: "draft.band" }, locale))}</label>
          <select
            id="warband-select"
            value={bandId}
            onChange={(event) => setBandId(event.target.value)}
          >
            <option value="">{presentationOutput(translate({ key: "draft.select" }, locale))}</option>
            {[...workflow.options].sort((a,b)=>a.name.localeCompare(b.name)).map((option) => (
              <option key={option.band_id} value={option.band_id}>
                {presentationOutput(option.name)}
              </option>
            ))}
          </select>

          <label htmlFor="campaign-name">{presentationOutput(translate({ key: "draft.campaign" }, locale))}</label>
          <input
            id="campaign-name"
            type="text"
            value={campaignName}
            onChange={(event) => setCampaignName(event.target.value)}
            placeholder={presentationOutput(translate({ key: "draft.placeholder" }, locale))}
          />

          <button type="submit" disabled={!bandId} data-disabled-reason={!bandId ? presentationOutput(translate({ key: "draft.select-first" }, locale)) : undefined}>
            {presentationOutput(translate({ key: "draft.start" }, locale))}
          </button>
        </form>
      )}

      {status !== null && (
        <>
          <output role="status" style={{ display: "block" }}>
            {presentationOutput(translate({ key: "draft.status", args: { count: status.models, limit: status.maximum_models, cap: status.minimum_models, amount: status.heroes, total: status.hero_limit, gold: status.treasury } }, locale))}
          </output>

          {!status.legal && (
            <output role="status" style={{ display: "block" }}>
              {presentationOutput(translate({ key: "draft.illegal" }, locale))}
            </output>
          )}

          <button
            type="button"
            disabled={!canCommit}
            data-disabled-reason={!canCommit ? presentationOutput(translate({ key: "draft.illegal" }, locale)) : undefined}
            onClick={() => void workflow.commit()}
          >
            {presentationOutput(translate({ key: "draft.commit" }, locale))}
          </button>
        </>
      )}

      {workflow.error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {presentationOutput(workflow.error)}
          <button type="button" onClick={workflow.clearError}>
            {presentationOutput(translate({ key: "ui.0c99ad9060fa" }, locale))}
          </button>
        </output>
      )}
    </section>
  );
}
