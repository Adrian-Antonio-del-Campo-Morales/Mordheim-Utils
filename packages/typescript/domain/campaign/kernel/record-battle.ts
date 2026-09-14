/**
 * P3.5: record a battle — the pure port of the Python
 * `domain/battle_service.record_battle` core (validation, snapshot numbers,
 * battle node, pending post-battle with hireling-upkeep follow-ups).
 *
 * Records the battle facts and applies the supported scenario rewards before
 * opening the pending post-battle sequence. The application service adds the
 * pre-battle availability checks and keeps all state transitions pure.
 *
 * Purity: no React, no DOM, no filesystem. Dates use ISO (locale-volatile
 * display formatting belongs to the UI).
 */

import type { IdString, InventoryItem, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import type {
  Battle,
  Campaign,
  CampaignDocument,
  PostBattle,
  RecordBattleInput,
  UseCaseResult,
} from "./usecases";
import { rejected } from "./rejections";
import {
  cloneDocument,
  currentState,
  findWarrior,
  memberCount,
  nextBattleNumber,
  pendingPostBattle,
  rating,
  withCampaign,
} from "./document";

/** Normalizes a result input to the contract's canonical value. */
export function normalizeResult(result: string): "win" | "loss" | "draw" | null {
  const key = result.trim().toLowerCase();
  if (key === "win" || key === "victory") return "win";
  if (key === "loss" || key === "defeat") return "loss";
  if (key === "draw") return "draw";
  return null;
}

/** Applies normalized desktop scenario loot before the post-battle sequence starts. */
function recordedRewards(input: RecordBattleInput, knowledge: KnowledgeReader, inventory: readonly InventoryItem[], battleNumber: number, campaign: Campaign) {
  let gold = 0, wyrdstone = 0; let items = [...inventory]; const notes: OpenPayload[] = []; const followUps: OpenPayload[] = []; const addedRules: OpenPayload[] = [];
  let scenarioExploration: OpenPayload | undefined;
  const addItem = (id: string, name: string, category: string, quantity: number, rule = "") => {
    const found = items.find((item) => item.id === id);
    items = found
      ? items.map((item) => item.id === id ? { ...item, owned: item.owned + quantity, stash: item.stash + quantity, ...(rule && !(item.special_rules ?? []).includes(rule) ? { special_rules: [...(item.special_rules ?? []), rule] } : {}) } : item)
      : [...items, { id, name, category, owned: quantity, equipped: 0, stash: quantity, value: 0, ...(rule ? { special_rules: [rule] } : {}) }];
  };
  const rewards = input.scenario_results?.["additional_rewards"];
  if (!Array.isArray(rewards)) return { gold, wyrdstone, inventory: items, notes, followUps, addedRules, scenarioExploration };
  for (const value of rewards) {
    if (!value || typeof value !== "object") continue;
    const reward = value as OpenPayload; const quantity = Math.max(0, Math.trunc(Number(reward["quantity"] ?? 0)));
    if (!quantity) continue;
    if (reward["kind"] === "resource") {
      if (reward["resource"] === "gold_crowns") gold += quantity;
      if (reward["resource"] === "wyrdstone_fragments") wyrdstone += quantity;
      continue;
    }
    if (reward["kind"] === "exploration") {
      scenarioExploration = { extra_dice: Math.max(0, Math.trunc(Number(reward["extra_dice"] ?? 0))), reroll_all: Boolean(reward["reroll_all"]) };
      notes.push({ step: 2, type: "scenario_reward", description: String(reward["rule"] ?? "Scenario exploration rule enabled.") });
      continue;
    }
    if (reward["kind"] === "special") {
      const special=String(reward["special_id"]??"");
      const label=String(reward["label"]??special), rule=String(reward["rule"]??label).trim();
      if (["nothing", "failure", "illusions"].some((token) => special.includes(token))) notes.push({step:2,type:"scenario_reward",description:label});
      else if(/magical-artefact/.test(special)) for(let index=0;index<quantity;index+=1) followUps.push({id:`scenario:${battleNumber}:${special}:${index+1}`,step:2,type:"exploration_followup",queue:[{type:"magical_artefact_table"}],messages:[label]});
      else if(special==="scenario.assault-on-the-rock.reward") {
        const forbidden = ["sisters-of-sigmar", "witch-hunters"].includes(campaign.identity.band_id) || campaign.warriors.some((warrior) => [warrior.name, warrior.profile_name, ...warrior.skills, ...(warrior.special_rules ?? [])].join(" ").toLowerCase().includes("priest of morr"));
        if (forbidden) notes.push({step:2,type:"scenario_reward",description:"Tome of Magic cannot be used by this warband."});
        else followUps.push({id:`scenario:${battleNumber}:tome-of-magic`,step:2,type:"scenario_spell_reward",mandatory:true,description:"Choose a Hero and exactly two spells granted by the Tome of Magic."});
      }
      else if(special==="scenario.the-item-lost.reward") followUps.push({id:`scenario:${battleNumber}:wand-of-phyrros`,step:2,type:"exploration_followup",mandatory:true,messages:[],queue:[{type:"grant_special_item",recipient:"hero",item_id:"scenario_reward.wand_of_phyrros",name:"Wand of Phyrros",text:rule}]});
      else if(special==="scenario.encampment-raid.reward") followUps.push({id:`scenario:${battleNumber}:encampment`,step:2,type:"scenario_encampment",mandatory:true,description:"Choose whether to destroy or occupy the captured camp; add captured stash items in Equipment."});
      else if(special==="scenario.the-night-of-the-headless-one.reward") addItem("scenario_reward.skull_of_the_headless_one","Skull of the Headless One","Scenario Reward",quantity,rule);
      else if(["worthless-inventories", "straggler-", "encampment-raid"].some((token)=>special.includes(token))) addedRules.push({source:`scenario:${battleNumber}`,text:rule,expires_after_battles:null,consume_when_opponent_contains:[]});
      else {
        const canonical: Record<string,string>={"dispel-scroll":"dispelling_scroll","holy-or-unholy-relic":"holy_relic"};
        const id=canonical[special]??`scenario_reward.${special||"special"}`;
        const known=knowledge.queryKnowledge({id:{kind:"item_id",value:id}}); const name=known.ok?String(known.record.names["en"]??label):label;
        addItem(id,name,"Scenario Reward",quantity,rule);
      }
      continue;
    }
    if (reward["kind"] !== "item") continue;
    const id = String(reward["item_id"] ?? ""); if (!id) continue;
    const known = knowledge.queryKnowledge({ id: { kind: "item_id", value: id } });
    const name = known.ok ? String(known.record.names["en"] ?? id) : String(reward["label"] ?? id);
    const category = known.ok ? String(known.record.data["kind"] ?? "Scenario Reward") : "Scenario Reward";
    addItem(id,name,category,quantity);
    notes.push({ step: 2, type: "scenario_reward", description: `Scenario: +${quantity} ${name}.`, item_id: id, quantity });
  }
  return { gold, wyrdstone, inventory: items, notes, followUps, addedRules, scenarioExploration };
}

/**
 * Records a battle: validates the table facts, snapshots the warband numbers,
 * appends the battle node and opens its pending post-battle with
 * hireling-upkeep follow-ups.
 */
export function recordBattle(
  document: CampaignDocument,
  input: RecordBattleInput,
  knowledge: KnowledgeReader,
): UseCaseResult {
  const { campaign } = document;
  if (campaign.configuration.is_draft) {
    return rejected(
      "not_permitted_in_draft",
      "Commit the initial warband before recording battles.",
    );
  }
  if (pendingPostBattle(document) !== null) {
    const pending = pendingPostBattle(document);
    return rejected(
      "conflict",
      `Post-battle #${pending?.battle_number} is still pending; commit it before recording the next battle.`,
    );
  }
  const scenario = knowledge.queryKnowledge({
    id: { kind: "scenario_id", value: input.scenario },
  });
  if (!scenario.ok) {
    return rejected("not_found", `Unknown scenario: ${input.scenario}.`);
  }
  const result = normalizeResult(input.result);
  if (result === null) {
    return rejected("invalid_input", "Result must be win, loss or draw.");
  }
  if (!input.opponent.trim()) {
    return rejected("invalid_input", "An opponent is required.");
  }
  if (input.gold_delta < 0 || input.wyrdstone < 0 || input.xp_delta < 0 || input.casualties < 0) {
    return rejected("invalid_input", "Battle numbers must be non-negative.");
  }
  const outOfAction = input.out_of_action_ids ?? [];
  if (input.opponent_rating != null && (!Number.isInteger(input.opponent_rating) || input.opponent_rating < 0)) {
    return rejected("invalid_input", "Opponent rating must be a non-negative whole number.");
  }
  const submittedIds = new Set<IdString>(outOfAction);
  for (const id of submittedIds) {
    const warrior = findWarrior(document, id);
    if (!warrior) continue;
    if (warrior.games_to_miss && warrior.games_to_miss > 0) {
      return rejected(
        "not_available",
        `Unavailable warriors cannot receive battle results: ${warrior.name}.`,
      );
    }
    const casualtiesForWarrior = outOfAction.filter((item) => item === id).length;
    if (casualtiesForWarrior > (warrior.quantity ?? 1)) {
      return rejected("limit_violated", `${warrior.name} cannot have more Out of Action results than deployed models.`);
    }
    if (input.participants && !input.participants.includes(id)) {
      return rejected("not_available", `Out of Action warrior was not deployed: ${warrior.name}.`);
    }
  }

  const number = nextBattleNumber(document);
  const rewards = recordedRewards(input, knowledge, campaign.inventory, number, campaign);
  const base = currentState(document);
  const baseRating = base?.rating ?? rating(campaign.warriors);
  const baseModels = base?.models ?? memberCount(campaign.warriors);
  const date = new Date().toISOString().slice(0, 10);

  const casualties = outOfAction.length;
  const perGroupCasualties = outOfAction.reduce<Record<string, number>>((counts, id) => ({ ...counts, [id]: (counts[id] ?? 0) + 1 }), {});
  const battle: Battle = {
    number,
    date,
    scenario: input.scenario,
    opponent: input.opponent,
    ...(input.opponent_rating != null ? { opponent_rating: input.opponent_rating } : {}),
    ...(input.opponent_band_id ? { opponent_band_id: input.opponent_band_id } : {}),
    result,
    gold_delta: Math.trunc(input.gold_delta) + rewards.gold,
    wyrdstone: Math.max(0, Math.trunc(input.wyrdstone)) + rewards.wyrdstone,
    xp_delta: Math.max(0, Math.trunc(input.xp_delta)),
    casualties,
    advances: 0,
    rating_before: baseRating,
    rating_after: baseRating,
    models_before: baseModels,
    models_after: baseModels,
    ...(input.xp_awards ? { xp_awards: input.xp_awards } : {}),
    ...(input.scenario_results ? { scenario_results: input.scenario_results } : {}),
    ...(input.notes ? { notes: input.notes } : {}),
    out_of_action_ids: [...outOfAction],
    ...(Object.keys(perGroupCasualties).length ? { per_group_casualties: perGroupCasualties } : {}),
    ...(input.participants
      ? {
          participants: input.participants.map((id) => {
            const warrior = findWarrior(document, id);
            return {
              id,
              name: warrior?.name ?? id,
              kind: warrior?.kind ?? "hero",
              quantity: warrior?.quantity ?? 1,
              profile_name: warrior?.profile_name ?? id,
              condition: warrior?.condition ?? "",
            } as OpenPayload;
          }),
        }
      : {}),
    ...(input.absentees?.length ? { absentees: input.absentees } : {}),
  };

  const postBattle: PostBattle = {
    battle_number: number,
    complete: false,
    active_step: 0,
    completed_steps: [],
    review_open: false,
    // Desktop `record_battle` seeds the pending post-battle with the
    // battle's resource deltas so the resolution steps start from them.
    gold_delta: Math.max(0, Math.trunc(input.gold_delta)) + rewards.gold,
    wyrdstone_delta: Math.max(0, Math.trunc(input.wyrdstone)) + rewards.wyrdstone,
    ...(rewards.scenarioExploration ? { step_state: { scenario_exploration: rewards.scenarioExploration } } : {}),
    ...(rewards.notes.length ? { event_log: rewards.notes } : {}),
    // Hireling upkeep follow-ups (Python `record_battle` tail).
    ...(campaign.warriors.some((w) => w.kind === "hireling" && w.upkeep_resources?.length)
      ? {
          pending_follow_ups: [...campaign.warriors
            .filter((w) => w.kind === "hireling" && w.upkeep_resources?.length)
            .map((w) => ({
              id: `upkeep:${number}:${w.id}`,
              step: 6,
              type: "hireling_upkeep",
              warrior_id: w.id,
              costs: w.upkeep_resources?.map(([key, value]) => [key, value] as [string, number]),
              description: `Pay ${w.name}'s upkeep or dismiss the Hired Sword.`,
            })),...rewards.followUps],
        }
      : rewards.followUps.length ? { pending_follow_ups: rewards.followUps } : {}),
  };

  const opponentKey = `${input.opponent_band_id ?? ""} ${input.opponent}`.toLowerCase();
  const specialRules = [...campaign.special_rules, ...rewards.addedRules].flatMap((rule) => {
    const rawTriggers = rule["consume_when_opponent_contains"];
    const triggers = Array.isArray(rawTriggers) ? rawTriggers.map((value: unknown) => String(value).toLowerCase()) : [];
    const applies = triggers.length === 0 || triggers.some((value) => opponentKey.includes(value));
    if (rule.expires_after_battles == null || !applies) return [rule];
    const remaining = Number(rule.expires_after_battles) - 1;
    return remaining > 0 ? [{ ...rule, expires_after_battles: remaining }] : [];
  });

  const nextCampaign: Campaign = {
    ...campaign,
    battles: [...campaign.battles, battle],
    post_battles: [...campaign.post_battles, postBattle],
    special_rules: specialRules,
    inventory: rewards.inventory,
  };
  return { ok: true, state: withCampaign(document, nextCampaign) };
}

/**
 * The snapshot helpers a full post-battle engine (P6.5) will need; kept here
 * so the mutable-state discipline stays in one module.
 */
export function snapshotForNextState(document: CampaignDocument): CampaignDocument {
  return cloneDocument(document);
}
