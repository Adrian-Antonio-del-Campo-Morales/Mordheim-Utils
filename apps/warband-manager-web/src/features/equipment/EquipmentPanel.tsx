import { textSymbol } from "../campaign/presentation-values";
import { textNumber } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, warriorPersonalName } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
/**
 * Campaign equipment, stash and reassignment presentation.
 *
 * Renders the inventory read model (equipped/stash split per row) and the
 * per-warrior equipment entries; assign/withdraw actions dispatch through
 * the campaign app service (`assignEquipment` action) — rejections surface
 * via the shell's error seam, never thrown.
 *
 * Pure view over the CampaignAppView seam; read model helpers live in the
 * application feature so this file only exports components (react-refresh).
 */
import { useState } from "react";

import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "../campaign/displayText";
import { KnowledgeHint } from "../campaign/KnowledgeHint";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";

interface EquipmentPanelProps {
  readonly document: CampaignDocument;
  readonly readOnly?: boolean;
  readonly locale?: "es" | "en";
  readonly knowledge?: ArtefactKnowledgeReader;
  readonly showTitle?: boolean;
  readonly trading?: boolean;
}

export function EquipmentPanel({ document, readOnly = false, locale: requestedLocale, knowledge, showTitle = true, trading = false }: EquipmentPanelProps) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const { campaign } = document;
  const [busy, setBusy] = useState(false);
  const [assignmentFailed, setAssignmentFailed] = useState(false);
  const localError = assignmentFailed ? app.error ?? translate({ key: "ui.fb0f326e5025" }, locale) : app.error;

  const assign = async (warriorId: string, itemId: string, quantity: number, direction: "equip" | "stash") => {
    setBusy(true);
    setAssignmentFailed(false);
    const ok = await app.runAction("assignEquipment", { warrior_id: warriorId, item_id: itemId, quantity, direction });
    if (!ok) {
      setAssignmentFailed(true);
    }
    setBusy(false);
  };
  const stashRows = campaign.inventory.filter((item) => item.stash > 0);
  const equippedRows = campaign.inventory.filter((item) => item.equipped > 0);
  const t = ({ title: translate({ key: "ui.9cd4c565ba6e" }, locale), stash: translate({ key: "ui.aff6f9349f4c" }, locale), emptyStash: translate({ key: "ui.83d7069e2b7a" }, locale), item: translate({ key: "ui.cf471eb26f03" }, locale), equip: translate({ key: "ui.144e71befe17" }, locale), choose: translate({ key: "ui.0900dc1cdafd" }, locale), equipped: translate({ key: "ui.e9177dcd5b0f" }, locale), emptyEquipped: translate({ key: "ui.cd3e9336e064" }, locale), return: translate({ key: "ui.66b471913d95" }, locale), returnSet: translate({ key: "ui.5646a95e12f1" }, locale) });

  return (
    <section aria-label={presentationOutput(t.title)} className="equipment-panel">
      {showTitle && <h3>{presentationOutput(t.title)}</h3>}

      {localError && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {presentationOutput(localError)}
        </output>
      )}

      <div className="inventory-columns"><div><h4>{presentationOutput(t.equipped)}</h4>
      {equippedRows.length === 0 ? (
        <p>{presentationOutput(t.emptyEquipped)}</p>
      ) : (
        <ul className="equipped-list">
          {campaign.warriors.map((warrior) => {
            const entries = warrior.equipment.filter((entry) => entry.acquisition !== "fixed");
            if (entries.length === 0) return null;
            return <li className="equipped-warrior-group" key={warrior.id}>
              <strong>{presentationOutput(warriorPersonalName(warrior, locale))}</strong>
              <ul>
                {entries.map((entry) => <li key={`${warrior.id}:${entry.item_id}`}>
                  <span><KnowledgeHint knowledge={knowledge} kind="item" id={entry.item_id} locale={locale}>{presentationOutput(textNumber(entry.quantity, locale))}  {presentationOutput(textSymbol("×"))} {presentationOutput(knowledgeName(knowledge, "item", entry.item_id, locale))}</KnowledgeHint></span>
                  {!readOnly && <span className="equipment-actions"><button type="button" aria-label={presentationOutput(textJoin([translate({ key: "ui.19101959b5ff" }, locale), knowledgeName(knowledge, "item", entry.item_id, locale), translate({ key: "ui.890b66b4037c" }, locale), warriorPersonalName(warrior, locale), translate({ key: "ui.3ad5e1d5c266" }, locale)], " "))} disabled={busy || entry.transferable === false} data-disabled-reason={(busy ? (translate({ key: "disabled.b35ff70c09" }, locale)) : entry.transferable === false ? (translate({ key: "disabled.30b5aaf0ed" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.b35ff70c09" }, locale)) : entry.transferable === false ? (translate({ key: "disabled.30b5aaf0ed" }, locale)) : undefined)!)} onClick={() => void assign(warrior.id, entry.item_id, 1, "stash")}>{presentationOutput(warrior.kind === "henchman" ? t.returnSet : t.return)}</button></span>}
                </li>)}
              </ul>
            </li>;
          })}
        </ul>
      )}</div><div><h4>{presentationOutput(t.stash)}</h4>
      {stashRows.length === 0 ? (
        <p>{presentationOutput(t.emptyStash)}</p>
      ) : (
        <table className="mobile-cards">
          <caption>{presentationOutput(t.stash)}</caption>
          <thead>
            <tr>
              <th scope="col">{presentationOutput(t.item)}</th>
              <th scope="col">{presentationOutput(t.stash)}</th>
              {!readOnly && <th scope="col">{presentationOutput(t.equip)}</th>}
            </tr>
          </thead>
          <tbody>
            {stashRows.map((item) => (
              <tr key={item.id}>
                <td data-label={presentationOutput(t.item)}><KnowledgeHint knowledge={knowledge} kind="item" id={item.id} locale={locale}>{presentationOutput(knowledgeName(knowledge, "item", item.id, locale))}</KnowledgeHint></td>
                <td data-label={presentationOutput(t.stash)}>{presentationOutput(textNumber(item.stash, locale))}</td>
                {!readOnly && <td data-label={presentationOutput(t.equip)}>
                  <select
                    aria-label={presentationOutput(textJoin([translate({ key: "ui.d4133eac7bf6" }, locale), knowledgeName(knowledge, "item", item.id, locale), translate({ key: "ui.3a78c2453718" }, locale)], " "))}
                    defaultValue=""
                    disabled={busy}
                    data-disabled-reason={(busy ? (translate({ key: "disabled.b35ff70c09" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.b35ff70c09" }, locale)) : undefined)!)}
                    onChange={(event) => {
                      const warriorId = event.target.value;
                      if (warriorId) {
                        void assign(warriorId, item.id, 1, "equip");
                        event.target.value = "";
                      }
                    }}
                  >
                    <option value="" disabled>
                      {presentationOutput(t.choose)}
                    </option>
                    {[...campaign.warriors].sort((a,b)=>a.name.localeCompare(b.name,locale)).map((warrior) => (
                      <option key={warrior.id} value={warrior.id}>
                        {presentationOutput(warriorPersonalName(warrior, locale))}
                      </option>
                    ))}
                  </select>
                </td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}</div></div>
      {trading && knowledge && <HirelingsPanel document={document} listings={knowledge} locale={locale} mode="trading" showTradingTitle={false} />}
    </section>
  );
}
