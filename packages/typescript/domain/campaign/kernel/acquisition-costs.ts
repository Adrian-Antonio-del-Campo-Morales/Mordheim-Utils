/**
 * Per-copy acquisition-cost accounting — the TS mirror of the desktop
 * `acquisition_costs` ledger (Python `models.py`): `EquipmentEntryVM.copy_costs`,
 * `InventoryItemVM.add_stock/remove_stock`, and `WarbandStateVM.stash_acquisition_costs`.
 *
 * Empty/absent ledger = legacy state: the item's `unit_cost`/`value` stands in
 * for every copy.
 *
 * Purity: pure functions over plain arrays; no document coupling.
 */

import type { Campaign, EquipmentEntry, InventoryItem } from "./usecases";

/** Effective per-copy costs of an equipment entry (desktop `copy_costs`). */
export function copyCosts(entry: EquipmentEntry): readonly number[] {
  return entry.acquisition_costs !== undefined && entry.acquisition_costs.length === entry.quantity
    ? entry.acquisition_costs
    : new Array<number>(entry.quantity).fill(entry.unit_cost ?? 0);
}

/** Total acquisition cost of an equipment entry (desktop `total_cost` on the ledger). */
export function entryAcquisitionCost(entry: EquipmentEntry): number {
  return copyCosts(entry).reduce((total, cost) => total + cost, 0);
}

/** Normalise a stock ledger so its length matches `owned` (desktop fallback). */
function normalise(stock: InventoryItem): number[] {
  const value = stock.value ?? 0;
  return stock.acquisition_costs !== undefined && stock.acquisition_costs.length === stock.owned
    ? [...stock.acquisition_costs]
    : new Array<number>(stock.owned).fill(value);
}

/** Desktop `InventoryItemVM.add_stock`: append per-copy costs, return the next ledger. */
export function addStock(stock: InventoryItem, quantity: number, unitCost: number): readonly number[] {
  const ledger = normalise(stock);
  for (let index = 0; index < quantity; index += 1) ledger.push(unitCost);
  return ledger;
}

/** Desktop `InventoryItemVM.remove_stock`: pop one cost (matching `unitCost` when present), return its refund. */
export function removeStockRefund(ledger: number[], unitCost?: number): number {
  const index = unitCost !== undefined && ledger.includes(unitCost) ? ledger.indexOf(unitCost) : 0;
  const [refund] = ledger.splice(index, 1);
  return refund;
}

/**
 * Desktop `WarbandStateVM.stash_acquisition_costs`: per-copy costs of the
 * stash copies, net of the copies equipped from this stock (equipped copies
 * were paid when they left the stash).
 */
export function stashAcquisitionCosts(campaign: Campaign, stock: InventoryItem): readonly number[] {
  if (stock.acquisition_costs === undefined || stock.acquisition_costs.length !== stock.owned) {
    return new Array<number>(stock.stash).fill(stock.value ?? 0);
  }
  const costs = [...stock.acquisition_costs];
  for (const warrior of campaign.warriors) {
    for (const equipment of warrior.equipment) {
      if (
        equipment.item_id !== stock.id ||
        equipment.transferable === false ||
        (campaign.configuration.is_draft && equipment.acquisition === "fixed")
      ) {
        continue;
      }
      for (const cost of copyCosts(equipment)) {
        if (!costs.length) break;
        const index = costs.includes(cost) ? costs.indexOf(cost) : 0;
        costs.splice(index, 1);
      }
    }
  }
  return costs;
}
