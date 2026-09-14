/**
 * Equipment workflow: equipment, stash and
 * assignments — the application feature block over the kernel's
 * `assignEquipment` use case.
 *
 * What this adds beyond the kernel:
 * - **Listing**: the inventory with its equipped/stash split plus, per
 *   warrior, the resolved equipment entries — the read model the UI renders;
 * - **Workflow**: assign/withdraw orchestration with undo-friendly service
 *   integration (the application service snapshots history around `run`).
 *
 * The kernel remains the only place that mutates documents; this module
 * composes queries and dispatches. Purity: plain Node, no React/DOM.
 */
import type { CampaignDocument, IdString, UseCaseResult } from "../../../../domain/campaign/kernel/usecases";
import type { AssignEquipmentInput } from "../../../../domain/campaign/kernel/equipment";
import type { CampaignUseCases, InventoryItem, Warrior } from "../../../../domain/campaign/kernel/usecases";

/** One inventory row with its split, for the UI list. */
export interface InventoryRow {
  readonly id: IdString;
  readonly name: string;
  readonly category: string;
  readonly owned: number;
  readonly equipped: number;
  readonly stash: number;
  readonly value?: number;
  /** False for fixed rows — the UI disables assign buttons. */
  readonly transferable: boolean;
}

/** Per-warrior equipment summary for the UI. */
export interface WarriorEquipment {
  readonly warrior_id: IdString;
  readonly warrior_name: string;
  readonly entries: readonly {
    readonly item_id: IdString;
    readonly name: string;
    readonly quantity: number;
    readonly fixed: boolean;
  }[];
}

export interface EquipmentOverview {
  readonly rows: readonly InventoryRow[];
  readonly warriors: readonly WarriorEquipment[];
}

/** Read model for the inventory panel. */
export function equipmentOverview(document: CampaignDocument): EquipmentOverview {
  const rows: InventoryRow[] = document.campaign.inventory.map((item: InventoryItem) => ({
    id: item.id,
    name: item.name,
    category: item.category,
    owned: item.owned,
    equipped: item.equipped,
    stash: item.stash,
    ...(item.value !== undefined ? { value: item.value } : {}),
    transferable: item.equipped === 0 || hasTransferableEquipped(document, item.id),
  }));
  const warriors = document.campaign.warriors.map((warrior: Warrior) => ({
    warrior_id: warrior.id,
    warrior_name: warrior.name,
    entries: warrior.equipment.map((entry) => ({
      item_id: entry.item_id,
      name: entry.name,
      quantity: entry.quantity ?? 1,
      fixed: entry.acquisition === "fixed",
    })),
  }));
  return { rows, warriors };
}

/** A row is withdrawable when at least one warrior carries a non-fixed entry. */
function hasTransferableEquipped(document: CampaignDocument, itemId: IdString): boolean {
  return document.campaign.warriors.some((warrior) =>
    warrior.equipment.some(
      (entry) => entry.item_id === itemId && entry.acquisition !== "fixed",
    ),
  );
}

/** Assign stash → warrior (or withdraw with direction "stash"). */
export function assignToWarrior(
  useCases: CampaignUseCases,
  document: CampaignDocument,
  input: AssignEquipmentInput,
): UseCaseResult {
  return useCases.assignEquipment(document, input);
}

/** Withdraw `quantity` of `itemId` from a warrior back into the stash. */
export function withdrawFromWarrior(
  useCases: CampaignUseCases,
  document: CampaignDocument,
  warriorId: IdString,
  itemId: IdString,
  quantity: number,
): UseCaseResult {
  return useCases.assignEquipment(document, {
    warrior_id: warriorId,
    item_id: itemId,
    quantity,
    direction: "stash",
  });
}
