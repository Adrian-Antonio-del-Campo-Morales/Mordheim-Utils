/**
 * Web migration equipment surface: equipment, stash and
 * assignments UI.
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

interface EquipmentPanelProps {
  readonly document: CampaignDocument;
  readonly readOnly?: boolean;
  readonly locale?: "es" | "en";
}

export function EquipmentPanel({ document, readOnly = false, locale = "en" }: EquipmentPanelProps) {
  const app = useCampaignApp();
  const { campaign } = document;
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [transferTargets, setTransferTargets] = useState<Record<string, string>>({});

  const assign = async (warriorId: string, itemId: string, quantity: number, direction: "equip" | "stash") => {
    setBusy(true);
    setLocalError(null);
    await app.runAction("assignEquipment", { warrior_id: warriorId, item_id: itemId, quantity, direction });
    setBusy(false);
  };
  const transfer = async (sourceId: string, targetId: string, itemId: string) => { setBusy(true); await app.runAction("transferEquippedItem", { source_id: sourceId, target_id: targetId, item_id: itemId }); setBusy(false); };

  const stashRows = campaign.inventory.filter((item) => item.stash > 0);
  const equippedRows = campaign.inventory.filter((item) => item.equipped > 0);
  const t = locale === "es" ? { title:"Equipo",stash:"En reserva",emptyStash:"No hay nada en la reserva.",item:"Objeto",equip:"Equipar a",choose:"Elige guerrero…",equipped:"Equipado",emptyEquipped:"No hay nada equipado.",carries:"lleva",return:"Devolver 1 a la reserva",returnSet:"Devolver juego a la reserva",transfer:"Transferir" } : { title:"Equipment",stash:"In stash",emptyStash:"Nothing in the stash.",item:"Item",equip:"Equip to",choose:"Choose warrior…",equipped:"Equipped",emptyEquipped:"Nothing equipped.",carries:"carries",return:"Return 1 to stash",returnSet:"Return set to stash",transfer:"Transfer" };

  return (
    <section aria-label="Equipment">
      <h3>{t.title}</h3>

      {localError && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {localError}
        </output>
      )}

      <h4>{t.stash}</h4>
      {stashRows.length === 0 ? (
        <p>{t.emptyStash}</p>
      ) : (
        <table>
          <caption>Stash</caption>
          <thead>
            <tr>
              <th scope="col">{t.item}</th>
              <th scope="col">Stash</th>
              {!readOnly && <th scope="col">{t.equip}</th>}
            </tr>
          </thead>
          <tbody>
            {stashRows.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.stash}</td>
                {!readOnly && <td>
                  <select
                    aria-label={`Assign ${item.name} to warrior`}
                    defaultValue=""
                    disabled={busy}
                    onChange={(event) => {
                      const warriorId = event.target.value;
                      if (warriorId) {
                        void assign(warriorId, item.id, 1, "equip");
                        event.target.value = "";
                      }
                    }}
                  >
                    <option value="" disabled>
                      {t.choose}
                    </option>
                    {campaign.warriors.map((warrior) => (
                      <option key={warrior.id} value={warrior.id}>
                        {warrior.name}
                      </option>
                    ))}
                  </select>
                </td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4>{t.equipped}</h4>
      {equippedRows.length === 0 ? (
        <p>{t.emptyEquipped}</p>
      ) : (
        <ul>
          {campaign.warriors.flatMap((warrior) =>
            warrior.equipment
              .filter((entry) => entry.acquisition !== "fixed")
              .map((entry) => (
                <li key={`${warrior.id}:${entry.item_id}`}>
                  {warrior.name} {t.carries} {entry.quantity} × {entry.name}{" "}
                  {!readOnly && <button
                    type="button"
                    disabled={busy}
                    aria-label={`Return ${entry.name} carried by ${warrior.name} to stash`}
                    onClick={() => {
                      void assign(warrior.id, entry.item_id, 1, "stash");
                    }}
                  >
                    {warrior.kind === "henchman" && entry.per_model ? t.returnSet : t.return}
                  </button>} {!readOnly && <><select aria-label={`Transfer ${entry.name} from ${warrior.name}`} value={transferTargets[`${warrior.id}:${entry.item_id}`] ?? ""} onChange={(event) => setTransferTargets((current) => ({ ...current, [`${warrior.id}:${entry.item_id}`]: event.target.value }))}><option value="">{t.choose}</option>{campaign.warriors.filter((target) => target.id !== warrior.id).map((target) => <option key={target.id} value={target.id}>{target.name}</option>)}</select><button disabled={busy || !(transferTargets[`${warrior.id}:${entry.item_id}`])} onClick={() => void transfer(warrior.id, transferTargets[`${warrior.id}:${entry.item_id}`], entry.item_id)}>{t.transfer}</button></>}
                </li>
              )),
          )}
        </ul>
      )}
    </section>
  );
}
