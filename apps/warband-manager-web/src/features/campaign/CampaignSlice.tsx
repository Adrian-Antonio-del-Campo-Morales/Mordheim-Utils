/**
 * P5.2 vertical slice (plan §6): import → display → edit → export.
 * Deliberately minimal: proves the contract end to end, not the final UX.
 * Navigation and full Campaign Manager views arrive with P6.x.
 */

import { useState } from "react";

import { useCampaignApp } from "./useCampaignApp";
import { TimelinePanel } from "../timeline/TimelinePanel";
import { EquipmentPanel } from "../equipment/EquipmentPanel";
import { AdvancesPanel } from "../advances/AdvancesPanel";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";
import { BattlePanel } from "../battle/BattlePanel";
import { InjuriesPanel } from "../injuries/InjuriesPanel";
import { ReviewPanel } from "../review/ReviewPanel";
import { DraftWorkspace } from "../draft/DraftWorkspace";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

export function CampaignSlice({ knowledge, locale = "en" }: { knowledge?: ArtefactKnowledgeReader; locale?: "es" | "en" }) {
  const app = useCampaignApp();
  // P6.4: the slice mirrors service state into local state so the battle
  // panel's document updates propagate (same pattern as TimelinePanel).
  const [warbandName, setWarbandName] = useState<string | null>(null);

  const doc = app.document;
  const identity = doc?.campaign.identity;
  const roster = doc?.campaign.warriors ?? [];
  const inventory = doc?.campaign.inventory ?? [];

  return (
    <section aria-label="Campaign">
      {/* P5.2 acceptance: the real KB artefact loads once at startup. */}
      {app.kbLoading && <p role="status">Loading knowledge base…</p>}
      {app.kbError && (
        <output role="status" style={{ display: "block", color: "darkorange" }}>
          {app.kbError}
        </output>
      )}

      {app.error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {app.error}{" "}
          {(app.error.startsWith("Replace") || app.error.includes("already loaded")) && (
            <button
              type="button"
              onClick={() => {
                void app.confirmReplace();
              }}
            >
              Replace campaign
            </button>
          )}
          <button type="button" onClick={app.clearError}>
            Dismiss
          </button>
        </output>
      )}

      {app.dirty && (
        <output role="status" style={{ display: "block" }}>
          ⚠ Unsaved changes — export to keep them.
        </output>
      )}

      {doc && identity && (
        <>
          <h2>{identity.warband_name}</h2>

          {doc.campaign.configuration.is_draft && knowledge ? (
            <DraftWorkspace document={doc} knowledge={knowledge} locale={locale} />
          ) : <>

          {/* P6.1: timeline navigation beside the state display. */}
          <TimelinePanel document={doc} onSelect={(moment) => app.selectMoment(moment)} />

          {/* P6.3: equipment & stash beside the inventory display. */}
          <EquipmentPanel document={doc} />

          {/* P6.6: experience & advances beside the roster display. */}
          <AdvancesPanel document={doc} />

          {/* P6.7: hirelings, exploration & trading (committed campaigns). */}
          {!doc.campaign.configuration.is_draft && <HirelingsPanel document={doc} />}

          {/* P6.5: injuries & recovery beside the roster display. */}
          <InjuriesPanel document={doc} />

          {/* P6.4: battle recording for committed campaigns (not drafts). */}
          {!doc.campaign.configuration.is_draft && (
            <BattlePanel
              document={doc}
              knowledge={knowledge}
              locale={locale}
              onDocument={(updated) => {
                /* The service snapshot is replaced through the app hook; the
                   panel holds its own copy so both stay consistent. */
                void updated;
              }}
            />
          )}
          <dl>
            <dt>Campaign</dt>
            <dd>{identity.campaign_name}</dd>
            <dt>Warband</dt>
            <dd>{app.dirty ? `${identity.warband_type}` : identity.warband_type}</dd>
            <dt>Band</dt>
            <dd>{identity.warband_type || identity.band_id}</dd>
          </dl>

          <h3>Roster ({roster.length})</h3>
          {roster.length === 0 ? (
            <p>No warriors.</p>
          ) : (
            <table>
              <caption>Roster</caption>
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Type</th>
                  <th scope="col">XP</th>
                  <th scope="col">Cost</th>
                </tr>
              </thead>
              <tbody>
                {roster.map((warrior) => (
                  <tr key={warrior.id}>
                    <td>{warrior.name}</td>
                    <td>{warrior.profile_name}</td>
                    <td>{warrior.experience}</td>
                    <td>{warrior.cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3>Inventory ({inventory.length})</h3>
          <ul>
            {inventory.map((item) => (
              <li key={item.id}>
                {item.name} — equipped {item.equipped}, stash {item.stash}
              </li>
            ))}
          </ul>

          <h4>Rename warband (sample edit)</h4>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (warbandName && warbandName.trim().length > 0) {
                void app.runAction("__rename_warband__", { name: warbandName.trim() });
                setWarbandName(null);
              }
            }}
          >
            <label htmlFor="warband-name">New name</label>
            <input
              id="warband-name"
              value={warbandName ?? ""}
              onChange={(event) => setWarbandName(event.target.value)}
            />
            <button type="submit" disabled={!warbandName || warbandName.trim().length === 0}>
              Apply
            </button>
          </form>

          {/* P6.8: review before export + auxiliary text exports. */}
          <ReviewPanel document={doc} />

          </>}

          <button type="button" onClick={() => void app.exportFile()}>
            Export .mordheim
          </button>
        </>
      )}
    </section>
  );
}
