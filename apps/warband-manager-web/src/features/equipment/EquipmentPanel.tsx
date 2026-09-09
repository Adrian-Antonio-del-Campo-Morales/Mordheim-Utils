/**
 * P6.3 (web-migration-parallel-plan.md §P6.3): equipment, stash and
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
}

export function EquipmentPanel({ document }: EquipmentPanelProps) {
  const app = useCampaignApp();
  const { campaign } = document;
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const assign = async (warriorId: string, itemId: string, quantity: number, direction: "equip" | "stash") => {
    setBusy(true);
    setLocalError(null);
    await app.runAction("assignEquipment", { warrior_id: warriorId, item_id: itemId, quantity, direction });
    setBusy(false);
  };

  const stashRows = campaign.inventory.filter((item) => item.stash > 0);
  const equippedRows = campaign.inventory.filter((item) => item.equipped > 0);

  return (
    <section aria-label="Equipment">
      <h3>Equipment</h3>

      {localError && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {localError}
        </output>
      )}

      <h4>In stash</h4>
      {stashRows.length === 0 ? (
        <p>Nothing in the stash.</p>
      ) : (
        <table>
          <caption>Stash</caption>
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col">Stash</th>
              <th scope="col">Equip to</th>
            </tr>
          </thead>
          <tbody>
            {stashRows.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.stash}</td>
                <td>
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
                      Choose warrior…
                    </option>
                    {campaign.warriors.map((warrior) => (
                      <option key={warrior.id} value={warrior.id}>
                        {warrior.name}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4>Equipped</h4>
      {equippedRows.length === 0 ? (
        <p>Nothing equipped.</p>
      ) : (
        <ul>
          {campaign.warriors.flatMap((warrior) =>
            warrior.equipment
              .filter((entry) => entry.acquisition !== "fixed")
              .map((entry) => (
                <li key={`${warrior.id}:${entry.item_id}`}>
                  {warrior.name} carries {entry.quantity} × {entry.name}{" "}
                  <button
                    type="button"
                    disabled={busy}
                    aria-label={`Return ${entry.name} carried by ${warrior.name} to stash`}
                    onClick={() => {
                      void assign(warrior.id, entry.item_id, 1, "stash");
                    }}
                  >
                    Return 1 to stash
                  </button>
                </li>
              )),
          )}
        </ul>
      )}
    </section>
  );
}
