import type { Warrior } from "../../../../domain/campaign/index";

export type ScenarioAward = Readonly<{
  id: string;
  label: string;
  amount: number;
  trigger: string;
  manual: boolean;
  selection: "single" | "multiple" | "distributed";
  amountDice?: readonly [number, number];
}>;

type Row = Readonly<Record<string, unknown>>;
type CampaignKnowledge = Readonly<{ campaignSection?(section: string): Readonly<Record<string, unknown>> }>;

function rows(value: unknown): readonly Row[] { return Array.isArray(value) ? value.filter((row): row is Row => !!row && typeof row === "object") : []; }

function localizedText(value: unknown, locale: "es" | "en", fallback: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const translated = value as Readonly<Record<string, unknown>>;
    const text = translated[locale] ?? translated["en"];
    if (typeof text === "string") return text;
  }
  return typeof fallback === "string" ? fallback : "Manual award";
}

function selection(row: Row): ScenarioAward["selection"] {
  const declared = String(row["selection"] ?? "").toLowerCase();
  if (declared === "single" || declared === "multiple" || declared === "distributed") return declared;
  const effect = String(row["effect"] ?? "").toLowerCase();
  const multiple = /\b(any|each|every|all units|all surviving|leader and heroes|surviving heroes or henchman|a hero or henchman carrying|a fighter earns|a hero earns \+1 experience for each|if a hero or henchman group survives)\b/.test(effect);
  return /distributed|freely distributed/.test(effect) ? "distributed" : multiple ? "multiple" : "single";
}

function amountDice(value: unknown): readonly [number, number] | undefined {
  const match = /^(\d*)d(\d+)$/i.exec(String(value ?? "").trim());
  return match ? [Number(match[1] || 1), Number(match[2])] : undefined;
}

function amount(row: Row, fallback: unknown): number {
  const declared = Number(row["amount"] ?? fallback);
  if (Number.isFinite(declared)) return Math.max(0, declared);
  return Math.max(0, Number(/\+(\d+)\s+(?:experience|experiencia)\b/i.exec(String(row["effect"] ?? ""))?.[1] ?? 0));
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
    const effect = localizedText(locale === "es" ? entry["effect_i18n"] : entry["effect"], locale, entry["effect"]);
    const dice = !source ? amountDice(entry["amount_dice"]) : undefined;
    return [{ id: ref || `${scenarioId}:manual:${index}`, label: source ? String(source["id"] ?? ref).split(".").at(-1)?.replaceAll("-", " ") ?? ref : effect, amount: amount(source ?? entry, source ? undefined : entry["amount"]), trigger: String(source?.["trigger"] ?? "manual"), manual: !source, selection: source ? "single" : selection(entry), ...(dice ? { amountDice: dice } : {}) }];
  });
}

export function calculatedAwards(rows: readonly ScenarioAward[], warriors: readonly Warrior[], result: string, enemyOoa: Readonly<Record<string, number>>, manual: Readonly<Record<string, Readonly<Record<string, number>>>>): Readonly<Record<string, number>> {
  const totals: Record<string, number> = {};
  const heroes = warriors.filter((warrior) => warrior.kind === "hero");
  const leader = heroes.find((warrior) => [...warrior.skills, ...(warrior.special_rules ?? [])].some((rule) => /--leader(?:$|\.)|^shared-rule\.leader(?:-\d+)?$|^leader$/i.test(String(rule)))) ?? heroes[0];
  const add = (id: string, amount: number) => { totals[id] = (totals[id] ?? 0) + Math.max(0, Math.trunc(amount)); };
  for (const row of rows) {
    if (row.manual) { for (const [id, amount] of Object.entries(manual[row.id] ?? {})) add(id, amount); continue; }
    if (row.trigger === "survived_battle") warriors.forEach((warrior) => add(warrior.id, row.amount));
    if (row.trigger === "warband_won_battle" && result === "win" && leader) add(leader.id, row.amount);
    if (row.trigger === "enemy_put_out_of_action") warriors.filter((warrior) => warrior.kind === "hero").forEach((warrior) => add(warrior.id, row.amount * (enemyOoa[warrior.id] ?? 0)));
  }
  return totals;
}

export type ScenarioResourceReward = Readonly<{ id: string; resource: "gold_crowns" | "wyrdstone_fragments"; rule: string }>;
export type ScenarioExplorationReward = Readonly<{ id: string; extra_dice: number; reroll_all: boolean; rule: string }>;

/** Structured resource rows from desktop ScenarioRewards.additional. */
export function scenarioResourceRewards(knowledge: CampaignKnowledge | undefined, scenarioId: string): readonly ScenarioResourceReward[] {
  const document = knowledge?.campaignSection?.("scenario-rewards") ?? {};
  const scenario = rows(document["scenarios"]).find((row) => String(row["scenario_id"] ?? "") === scenarioId);
  return rows(scenario?.["rewards"]).flatMap((row) => row["kind"] === "resource" && (row["resource"] === "gold_crowns" || row["resource"] === "wyrdstone_fragments") ? [{ id: String(row["id"] ?? ""), resource: row["resource"], rule: String(row["rule"] ?? "") }] : []);
}

export function scenarioExplorationRewards(knowledge: CampaignKnowledge | undefined, scenarioId: string): readonly ScenarioExplorationReward[] {
  const document = knowledge?.campaignSection?.("scenario-rewards") ?? {};
  const scenario = rows(document["scenarios"]).find((row) => String(row["scenario_id"] ?? "") === scenarioId);
  return rows(scenario?.["rewards"]).flatMap((row) => row["kind"] === "exploration" ? [{ id: String(row["id"] ?? ""), extra_dice: Math.max(0, Number(row["extra_dice"] ?? 0)), reroll_all: Boolean(row["reroll_all"]), rule: String(row["rule"] ?? "") }] : []);
}

export type ScenarioLootReward = Readonly<{ id:string; label:string; rule?:string; kind:"item"|"resource"|"special"; item_id?:string; resource?:string; special_id?:string; availability?:Row; when?:Row; quantity_dice?:Row }>;
export function scenarioLootRewards(knowledge: CampaignKnowledge | undefined, scenarioId: string): readonly ScenarioLootReward[] {
  const document=knowledge?.campaignSection?.("scenario-rewards")??{}; const scenario=rows(document["scenarios"]).find((row)=>String(row["scenario_id"]??"")===scenarioId);
  return rows(scenario?.["rewards"]).flatMap((reward)=>rows(reward["contents"]).flatMap((content)=>{const grant=content["grant"] as Row|undefined,kind=String(grant?.["kind"]??"");return ["item","resource","special"].includes(kind)?[{id:String(content["id"]??""),label:String(content["label"]??content["id"]??"Reward"),rule:String(reward["rule"]??""),kind:kind as ScenarioLootReward["kind"],...(typeof grant?.["item_id"]==="string"?{item_id:grant["item_id"]}:{}),...(typeof grant?.["resource"]==="string"?{resource:grant["resource"]}:{}),...(typeof grant?.["special_id"]==="string"?{special_id:grant["special_id"]}:{}),...(content["availability"]&&typeof content["availability"]==="object"?{availability:content["availability"] as Row}:{}),...(content["when"]&&typeof content["when"]==="object"?{when:content["when"] as Row}:{}),...(content["quantity_dice"]&&typeof content["quantity_dice"]==="object"?{quantity_dice:content["quantity_dice"] as Row}:{})}]:[];}));
}
