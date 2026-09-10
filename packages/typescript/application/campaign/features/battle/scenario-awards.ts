import type { Warrior } from "../../../../domain/campaign/index";

export type ScenarioAward = Readonly<{
  id: string;
  label: string;
  amount: number;
  trigger: string;
  manual: boolean;
  selection: "single" | "multiple" | "distributed";
}>;

type Row = Readonly<Record<string, unknown>>;
type CampaignKnowledge = Readonly<{ campaignSection?(section: string): Readonly<Record<string, unknown>> }>;

function rows(value: unknown): readonly Row[] { return Array.isArray(value) ? value.filter((row): row is Row => !!row && typeof row === "object") : []; }

function selection(row: Row): ScenarioAward["selection"] {
  const declared = String(row["selection"] ?? "").toLowerCase();
  if (declared === "single" || declared === "multiple" || declared === "distributed") return declared;
  const effect = String(row["effect"] ?? "").toLowerCase();
  return /distributed|freely distributed/.test(effect) ? "distributed" : /\b(any|each|every|all)\b/.test(effect) ? "multiple" : "single";
}

/** Desktop ScenarioRewards port over generated web KB documents. */
export function scenarioAwards(knowledge: CampaignKnowledge | undefined, scenarioId: string, locale: "es" | "en"): readonly ScenarioAward[] {
  const scenarioDocument = knowledge?.campaignSection?.("scenarios") ?? {};
  const experienceDocument = knowledge?.campaignSection?.("experience-and-advances") ?? {};
  const scenarios = rows(scenarioDocument["scenarios"]);
  const scenario = scenarios.find((row) => String(row["id"] ?? "") === scenarioId);
  const awards = rows(experienceDocument["awards"]);
  return rows((scenario?.["progression"] as Row | undefined)?.["experience"]).flatMap((entry, index) => {
    const ref = String(entry["ref"] ?? ""); const source = ref ? awards.find((row) => String(row["id"] ?? "") === ref) : undefined;
    if (ref && !source) return [];
    const effect = String(entry[locale === "es" ? "effect_i18n" : "effect"] ?? entry["effect"] ?? "Manual award");
    return [{ id: ref || `${scenarioId}:manual:${index}`, label: source ? String(source["id"] ?? ref).split(".").at(-1)?.replaceAll("-", " ") ?? ref : effect, amount: Math.max(0, Number(source?.["amount"] ?? entry["amount"] ?? 0) || 0), trigger: String(source?.["trigger"] ?? "manual"), manual: !source, selection: source ? "single" : selection(entry) }];
  });
}

export function calculatedAwards(rows: readonly ScenarioAward[], warriors: readonly Warrior[], result: string, enemyOoa: Readonly<Record<string, number>>, manual: Readonly<Record<string, Readonly<Record<string, number>>>>): Readonly<Record<string, number>> {
  const totals: Record<string, number> = {}; const leader = warriors.find((warrior) => warrior.kind === "hero");
  const add = (id: string, amount: number) => { totals[id] = (totals[id] ?? 0) + Math.max(0, Math.trunc(amount)); };
  for (const row of rows) {
    if (row.manual) { for (const [id, amount] of Object.entries(manual[row.id] ?? {})) add(id, amount); continue; }
    if (row.trigger === "survived_battle") warriors.forEach((warrior) => add(warrior.id, row.amount));
    if (row.trigger === "warband_won_battle" && result === "win" && leader) add(leader.id, row.amount);
    if (row.trigger === "enemy_put_out_of_action") warriors.filter((warrior) => warrior.kind === "hero").forEach((warrior) => add(warrior.id, row.amount * (enemyOoa[warrior.id] ?? 0));
  }
  return totals;
}

export type ScenarioResourceReward = Readonly<{ id: string; resource: "gold_crowns" | "wyrdstone_fragments"; rule: string }>;

/** Structured resource rows from desktop ScenarioRewards.additional. */
export function scenarioResourceRewards(knowledge: CampaignKnowledge | undefined, scenarioId: string): readonly ScenarioResourceReward[] {
  const document = knowledge?.campaignSection?.("scenario-rewards") ?? {};
  const scenario = rows(document["scenarios"]).find((row) => String(row["scenario_id"] ?? "") === scenarioId);
  return rows(scenario?.["rewards"]).flatMap((row) => row["kind"] === "resource" && (row["resource"] === "gold_crowns" || row["resource"] === "wyrdstone_fragments") ? [{ id: String(row["id"] ?? ""), resource: row["resource"], rule: String(row["rule"] ?? "") }] : []);
}

export type ScenarioLootReward = Readonly<{ id:string; label:string; kind:"item"|"resource"|"special"; item_id?:string; resource?:string; special_id?:string; availability?:Row; when?:Row; quantity_dice?:Row }>;
export function scenarioLootRewards(knowledge: CampaignKnowledge | undefined, scenarioId: string): readonly ScenarioLootReward[] {
  const document=knowledge?.campaignSection?.("scenario-rewards")??{}; const scenario=rows(document["scenarios"]).find((row)=>String(row["scenario_id"]??"")===scenarioId);
  return rows(scenario?.["rewards"]).flatMap((reward)=>rows(reward["contents"]).flatMap((content)=>{const grant=content["grant"] as Row|undefined,kind=String(grant?.["kind"]??"");return ["item","resource","special"].includes(kind)?[{id:String(content["id"]??""),label:String(content["label"]??content["id"]??"Reward"),kind:kind as ScenarioLootReward["kind"],...(typeof grant?.["item_id"]==="string"?{item_id:grant["item_id"]}:{}),...(typeof grant?.["resource"]==="string"?{resource:grant["resource"]}:{}),...(typeof grant?.["special_id"]==="string"?{special_id:grant["special_id"]}:{}),...(content["availability"]&&typeof content["availability"]==="object"?{availability:content["availability"] as Row}:{}),...(content["when"]&&typeof content["when"]==="object"?{when:content["when"] as Row}:{}),...(content["quantity_dice"]&&typeof content["quantity_dice"]==="object"?{quantity_dice:content["quantity_dice"] as Row}:{})}]:[];}));
}
