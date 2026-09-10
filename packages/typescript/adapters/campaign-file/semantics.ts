/**
 * Semantic domain-reference validation for parsed v4 documents — the TS
 * mirror of the desktop loader hardening in
 * `mordheim_campaign/persistence/campaigns.py` (`_validate_domain`, Agent 0
 * parity lane). The JSON Schema alone cannot express cross-field invariants
 * (inventory conservation, unique ids, live-warrior references); both
 * toolchains must enforce them identically so the shared parity vectors in
 * `tests/web/parity/vectors/malformed_save.json` agree.
 */
import type { Campaign } from "../../domain/campaign/kernel/state";

export interface SemanticViolation {
  readonly message: string;
}

function isInt(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value);
}

function nonnegative(value: unknown, label: string, errors: SemanticViolation[]): boolean {
  if (!isInt(value) || (value as number) < 0) {
    errors.push({ message: `Invalid ${label}: expected a nonnegative integer.` });
    return false;
  }
  return true;
}

function unique(values: readonly unknown[], label: string, errors: SemanticViolation[]): boolean {
  if (new Set(values).size !== values.length) {
    errors.push({ message: `Duplicate ${label} in campaign file.` });
    return false;
  }
  return true;
}

interface RosterWarrior {
  readonly id: string;
  readonly quantity?: number;
  readonly equipment?: readonly { quantity?: unknown; unit_cost?: unknown; acquisition_costs?: unknown }[];
}

function validateRoster(roster: readonly RosterWarrior[], errors: SemanticViolation[]): void {
  for (const warrior of roster) {
    if (!isInt(warrior.quantity) || (warrior.quantity as number) < 1) {
      errors.push({ message: "Warriors must have a positive model count." });
    }
    for (const equipment of warrior.equipment ?? []) {
      nonnegative(equipment.quantity, "equipment quantity", errors);
      // The desktop domain model defaults missing numerics (unit_cost 0,
      // acquisition_costs []) — mirror that instead of rejecting absent keys.
      nonnegative(equipment.unit_cost ?? 0, "equipment cost", errors);
      if (equipment.acquisition_costs !== undefined && !Array.isArray(equipment.acquisition_costs)) {
        errors.push({ message: "Invalid equipment acquisition costs." });
      } else {
        for (const cost of equipment.acquisition_costs ?? []) {
          nonnegative(cost, "equipment acquisition cost", errors);
        }
      }
    }
  }
}

interface StockItem {
  readonly id: string;
  readonly owned: number;
  readonly equipped: number;
  readonly stash: number;
  readonly value?: number;
  readonly acquisition_costs?: readonly unknown[];
}

function validateInventory(inventory: readonly StockItem[], errors: SemanticViolation[]): void {
  unique(
    inventory.map((row) => row.id),
    "inventory IDs",
    errors,
  );
  for (const stock of inventory) {
    for (const value of [stock.owned, stock.equipped, stock.stash, stock.value ?? 0]) {
      nonnegative(value, "inventory quantity or value", errors);
    }
    if (stock.owned !== stock.equipped + stock.stash) {
      errors.push({ message: "Inventory owned copies must equal equipped plus stash copies." });
    }
    for (const cost of stock.acquisition_costs ?? []) {
      nonnegative(cost, "inventory acquisition cost", errors);
    }
  }
}

export function validateCampaignSemantics(campaign: Campaign): SemanticViolation[] {
  const errors: SemanticViolation[] = [];
  const warriors = campaign.warriors as unknown as readonly RosterWarrior[];
  validateRoster(warriors, errors);
  validateInventory(campaign.inventory as unknown as readonly StockItem[], errors);
  for (const snapshot of campaign.states ?? []) {
    if (snapshot.roster) {
      validateRoster(snapshot.roster as unknown as readonly RosterWarrior[], errors);
    }
    if (snapshot.inventory) {
      validateInventory(snapshot.inventory as unknown as readonly StockItem[], errors);
    }
    unique(
      (snapshot.roster ?? []).map((row) => (row as RosterWarrior).id),
      "snapshot warrior IDs",
      errors,
    );
  }
  unique(
    (campaign.states ?? []).map((row) => row.number),
    "state numbers",
    errors,
  );
  unique(
    (campaign.battles ?? []).map((row) => (row as { number: number }).number),
    "battle numbers",
    errors,
  );
  unique(
    (campaign.post_battles ?? []).map((row) => (row as { battle_number: number }).battle_number),
    "post-battle numbers",
    errors,
  );
  unique(
    warriors.map((row) => row.id),
    "warrior IDs",
    errors,
  );

  const liveIds = new Set(warriors.map((row) => row.id));
  for (const post of campaign.post_battles ?? []) {
    if (post.complete) {
      continue;
    }
    const followupIds: string[] = [];
    for (const followup of post.pending_follow_ups ?? []) {
      const identifier = (followup as Record<string, unknown> | undefined)?.["id"];
      if (identifier === undefined || identifier === null) {
        continue; // Legacy queued exploration choices may not carry an ID.
      }
      if (typeof identifier !== "string" || identifier === "") {
        errors.push({ message: "Invalid pending follow-up identifier." });
        continue;
      }
      followupIds.push(identifier);
    }
    unique(followupIds, "pending follow-up IDs", errors);
    const advanceKeys: Array<[string, unknown]> = [];
    for (const advance of post.pending_advances ?? []) {
      const row = advance as Record<string, unknown>;
      const warriorId = row["warrior_id"];
      const threshold = row["threshold"];
      if (typeof warriorId !== "string" || (threshold !== undefined && threshold !== null && !isInt(threshold))) {
        errors.push({ message: "Invalid pending advancement reference." });
        continue;
      }
      if (!row["committed"]) {
        if (!liveIds.has(warriorId)) {
          errors.push({ message: "A pending advance references a missing warrior." });
          continue;
        }
        advanceKeys.push([warriorId, threshold]);
      }
    }
    unique(
      advanceKeys.map(([id, threshold]) => `${id}\u0000${String(threshold)}`),
      "pending advancements",
      errors,
    );
  }

  const battleNumbers = new Set((campaign.battles ?? []).map((row) => (row as { number: number }).number));
  for (const post of campaign.post_battles ?? []) {
    if (!battleNumbers.has((post as unknown as { battle_number: number }).battle_number)) {
      errors.push({ message: "A post-battle references a missing battle." });
    }
  }
  if ((campaign.post_battles ?? []).filter((post) => !post.complete).length > 1) {
    errors.push({ message: "Multiple pending post-battles are not supported." });
  }
  for (const post of campaign.post_battles ?? []) {
    const row = post as unknown as { active_step: number; completed_steps?: number[] };
    if (
      !isInt(row.active_step) ||
      row.active_step < 0 ||
      row.active_step >= 8 ||
      (row.completed_steps ?? []).some((step) => !isInt(step) || step < 0 || step >= 8)
    ) {
      errors.push({ message: "Invalid post-battle step." });
    }
  }
  if (!campaign.configuration.is_draft) {
    const stateNumbers = new Set((campaign.states ?? []).map((row) => row.number));
    if (!stateNumbers.has(campaign.current_state_number)) {
      errors.push({ message: "The current warband state is missing." });
    }
  }
  return errors;
}
