/**
 * P6.2 (plan §7): draft & initial composition UI. Shown beside/instead of the
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
  const workflow = useDraftWorkflow(onCommitted);
  const [bandId, setBandId] = useState<string>(workflow.options[0]?.band_id ?? "");
  const [campaignName, setCampaignName] = useState("");

  const status = workflow.status;
  const canCommit = status !== null && status.legal;

  return (
    <section aria-label="Draft">
      <h2>New warband draft</h2>

      {status === null && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (bandId) void workflow.startDraft(bandId, campaignName.trim() || undefined);
          }}
        >
          <label htmlFor="warband-select">Warband</label>
          <select
            id="warband-select"
            value={bandId}
            onChange={(event) => setBandId(event.target.value)}
          >
            {workflow.options.map((option) => (
              <option key={option.band_id} value={option.band_id}>
                {option.name}
              </option>
            ))}
          </select>

          <label htmlFor="campaign-name">Campaign name</label>
          <input
            id="campaign-name"
            type="text"
            value={campaignName}
            onChange={(event) => setCampaignName(event.target.value)}
            placeholder="New Mordheim Campaign"
          />

          <button type="submit" disabled={!bandId}>
            Start draft
          </button>
        </form>
      )}

      {status !== null && (
        <>
          <output role="status" style={{ display: "block" }}>
            Models {status.models}/{status.maximum_models} (min{" "}
            {status.minimum_models}) · Heroes {status.heroes}/{status.hero_limit}{" "}
            · Treasury {status.treasury} gold
          </output>

          {!status.legal && (
            <output role="status" style={{ display: "block" }}>
              The draft is not legal yet: it needs at least {status.minimum_models}{" "}
              models, one hero, and a non-negative treasury.
            </output>
          )}

          <button
            type="button"
            disabled={!canCommit}
            onClick={() => void workflow.commit()}
          >
            Commit initial warband (State #0)
          </button>
        </>
      )}

      {workflow.error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {workflow.error}{" "}
          <button type="button" onClick={workflow.clearError}>
            Dismiss
          </button>
        </output>
      )}
    </section>
  );
}
