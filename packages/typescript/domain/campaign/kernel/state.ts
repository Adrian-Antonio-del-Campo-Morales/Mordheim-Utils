/**
 * P3.4 (web-migration-parallel-plan.md §4): frozen public state model of the
 * campaign domain. Conceptually aligned with the `.mordheim` v4 contract
 * (contracts/campaign-file-v4) — the campaign/view split is deliberate:
 * persistent campaign state never mixes with reconstructible UI selection.
 *
 * Purity rules (enforced by tests/architecture tests): no React, no DOM, no
 * browser APIs, no filesystem. Stable KB ids are references; display text is
 * volatile locale snapshot and never used for identity.
 *
 * All mutation happens through the use cases (P3.5/P5.1) returning new
 * states; these types are structural and free of methods.
 */

/** Non-empty identifier string (stable KB ids and document-local ids). */
export type IdString = string;

/** Human-readable text captured from a specific locale. Not an identity. */
export type DisplayText = string;

/** Unconstrained payload preserved in place (contract policy). */
export type OpenPayload = Record<string, unknown>;

/** Map of key to signed integer (stat modifiers, per-warrior awards, ...). */
export type IntMap = Record<string, number>;

/** Result kinds of a recorded battle. */
export type BattleResult = "win" | "loss" | "draw";

/** Kind of roster row. */
export type WarriorKind = "hero" | "henchman" | "hireling";

export interface Resources {
  readonly stash_value: number;
  readonly rare_finds: number;
  readonly treasures: number;
  readonly campaign_points: number;
}

export interface DraftConfiguration {
  readonly is_draft: boolean;
  readonly starting_gold: number;
  readonly minimum_models: number;
  readonly maximum_models: number;
  readonly hero_limit: number;
}

export interface CampaignIdentity {
  /** Volatile display text. */
  readonly campaign_name: DisplayText;
  /** Volatile display text. */
  readonly warband_name: DisplayText;
  /** Volatile display text. */
  readonly warband_type: DisplayText;
  /** Stable KB id. */
  readonly band_id: IdString;
  readonly collection?: IdString;
  readonly ruleset?: IdString;
  /** Variant chosen by variant-capable warbands; null when not selected. */
  readonly mercenary_variant: IdString | null;
  readonly started?: string;
}

export interface EquipmentEntry {
  /** Stable KB id. */
  readonly item_id: IdString;
  /** Volatile display text. */
  readonly name: DisplayText;
  readonly quantity: number;
  readonly acquisition?: string;
  readonly unit_cost?: number;
  readonly per_model?: boolean;
  readonly transferable?: boolean;
  readonly special_rules?: readonly string[];
  readonly base_item_id?: IdString;
  /** Per-copy acquisition costs (oldest first); empty = unit_cost stands in. */
  readonly acquisition_costs?: readonly number[];
}

export interface Warrior {
  readonly id: IdString;
  readonly name: DisplayText;
  readonly profile_name: DisplayText;
  readonly kind: WarriorKind;
  /** Current characteristics by display key (M, WS, BS, S, T, W, I, A, Ld). */
  readonly stats: IntMap;
  readonly equipment: readonly EquipmentEntry[];
  readonly skills: readonly string[];
  readonly experience: number;
  readonly previous_experience?: number | null;
  /** Henchman group size; 1 for heroes and hirelings. */
  readonly quantity?: number;
  readonly condition?: string | null;
  readonly condition_detail?: string | null;
  readonly cost: number;
  /** Lasting characteristic injuries. */
  readonly stat_modifiers?: IntMap;
  readonly skill_access?: readonly string[];
  /** Characteristic points from advance rolls (distinct from injuries). */
  readonly stat_advances?: IntMap;
  /** Stable KB id; absent for hand-authored rows. */
  readonly profile_id?: IdString;
  readonly spell_difficulty_modifiers?: IntMap;
  readonly hireling_rating?: number;
  readonly maximum_models_modifier?: number;
  /** Array of [resource_id, amount] pairs (JSON has no tuples). */
  readonly upkeep_resources?: readonly (readonly [IdString, number])[];
  readonly games_to_miss?: number;
  readonly absence_reason?: string;
  readonly hatreds?: readonly string[];
  readonly battle_start_checks?: readonly OpenPayload[];
  /** Lasting injuries may restrict carried equipment (for example arm wounds). */
  readonly equipment_limits?: IntMap;
  readonly injury_records?: readonly OpenPayload[];
  readonly lost_eyes?: readonly string[];
  readonly special_rules?: readonly string[];
}

export interface InventoryItem {
  /** Stable KB item id. */
  readonly id: IdString;
  /** Volatile display text. */
  readonly name: DisplayText;
  readonly category: string;
  readonly owned: number;
  readonly equipped: number;
  readonly stash: number;
  readonly value?: number;
  /** Per-copy acquisition costs (oldest first); empty = value stands in. */
  readonly acquisition_costs?: readonly number[];
  readonly rarity?: string | null;
  readonly special_rules?: readonly string[];
  readonly base_item_id?: IdString;
}

export interface Battle {
  readonly number: number;
  readonly date: string;
  readonly scenario: string;
  readonly opponent: DisplayText;
  readonly opponent_band_id?: IdString;
  readonly result: BattleResult | string;
  readonly gold_delta: number;
  readonly wyrdstone: number;
  readonly xp_delta: number;
  readonly casualties: number;
  readonly advances: number;
  readonly rating_before: number;
  readonly rating_after: number;
  readonly models_before: number;
  readonly models_after: number;
  readonly notes?: string;
  readonly opponent_rating?: number | null;
  /**
   * Warrior ids Out of Action at battle end; null = not recorded (legacy).
   * Recovery resolves their injury rolls.
   */
  readonly out_of_action_ids: readonly IdString[] | null;
  /** Roster snapshot at battle time (opaque, preserve-in-place). */
  readonly participants?: readonly OpenPayload[];
  readonly per_group_casualties?: IntMap;
  /** Per-warrior XP award; empty = uniform xp_delta for every survivor. */
  readonly xp_awards?: IntMap;
  readonly scenario_results?: Record<string, unknown>;
  readonly absentees?: readonly OpenPayload[];
}

export interface TimelineState {
  /** Newest = highest number. Immutable once committed. */
  readonly number: number;
  readonly date: string;
  readonly gold: number;
  readonly wyrdstone: number;
  readonly rating: number;
  readonly models: number;
  readonly max_models: number;
  readonly heroes: number;
  readonly henchmen: number;
  readonly experience: number;
  readonly label?: string;
  readonly roster?: readonly Warrior[];
  readonly inventory?: readonly InventoryItem[];
}

export interface PostBattle {
  readonly battle_number: number;
  readonly complete: boolean;
  readonly active_step: number;
  /** Sorted step indices. */
  readonly completed_steps: readonly number[];
  readonly review_open: boolean;
  readonly gold_delta?: number;
  readonly wyrdstone_delta?: number;
  readonly wyrdstone_sold?: number;
  readonly sale_resolved?: boolean;
  readonly veteran_pool?: number;
  readonly experience_applied?: boolean;
  readonly pending_advances?: readonly OpenPayload[];
  /** Step-local working data keyed by step index. */
  readonly step_state?: Record<string, OpenPayload>;
  /** Search assignments and results keyed by hero id. */
  readonly searches?: Record<string, OpenPayload>;
  /** Acknowledgements keyed by step. */
  readonly acknowledgements?: Record<string, unknown>;
  readonly event_log?: readonly OpenPayload[];
  readonly equipment_obligations?: readonly OpenPayload[];
  readonly pending_follow_ups?: readonly OpenPayload[];
}

export interface SpecialRuleEffect {
  /** Preserve-in-place payload with source/text/expiry conventions. */
  readonly [key: string]: unknown;
}

/** The persistent campaign state (what the v4 file's `campaign` section holds). */
export interface Campaign {
  readonly identity: CampaignIdentity;
  readonly configuration: DraftConfiguration;
  readonly resources: Resources;
  /** Newest committed timeline state number; 0 for a draft. */
  readonly current_state_number: number;
  readonly warriors: readonly Warrior[];
  readonly battles: readonly Battle[];
  readonly states: readonly TimelineState[];
  readonly post_battles: readonly PostBattle[];
  readonly inventory: readonly InventoryItem[];
  readonly special_rules: readonly SpecialRuleEffect[];
  readonly unique_reward_ids?: readonly IdString[];
  readonly manual_log: readonly OpenPayload[];
}

/** Timeline node selection, e.g. `draft:0` | `state:3` | `battle:2` | `post:2`. */
export type MomentSelection = `draft:0` | `state:${number}` | `battle:${number}` | `post:${number}`;

/**
 * Reconstructible UI selection state. Readers may ignore or reset any part;
 * never persisted inside Campaign itself.
 */
export interface ViewState {
  readonly active_view?: string;
  readonly campaign_mode?: string;
  readonly selected_moment?: MomentSelection | string;
  readonly state_section?: string;
  readonly battle_section?: string;
  readonly inventory_mode?: string;
  readonly draft_warrior_tab?: string;
  /** Partially entered record-battle draft; cleared on record or cancel. */
  readonly pending_battle_draft?: Record<string, unknown>;
}

/** A whole campaign document in memory: state + volatile view selection. */
export interface CampaignDocument {
  readonly campaign: Campaign;
  readonly view: ViewState;
}
