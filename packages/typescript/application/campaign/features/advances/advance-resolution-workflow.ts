import type { CampaignDocument, KnowledgeReader, OpenPayload, Warrior } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

interface CatalogueReader extends KnowledgeReader {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
  list?(kind: "profile" | "skill" | "warband_group" | "racial_maximum"): readonly Readonly<Record<string, unknown>>[];
}
type Result = { ok: true; document: CampaignDocument; needs_subroll?: boolean } | { ok: false; message: string };
const CHARACTERISTICS: Record<string, string> = { movement:"M", weapon_skill:"WS", ballistic_skill:"BS", strength:"S", toughness:"T", wounds:"W", initiative:"I", attacks:"A", leadership:"Ld" };
const BAND_RACE: Record<string,string> = { "warband-group.human":"human", "warband-group.chaos-human":"human", "warband-group.human-mercenary":"human", "warband-group.elf":"elf", "warband-group.high-elf":"elf", "warband-group.dark-elf":"elf", "warband-group.dwarf":"dwarf", "warband-group.chaos-dwarf":"dwarf", "warband-group.skaven":"skaven", "warband-group.ogre":"ogre", "warband-group.goblin":"goblin", "warband-group.orc":"orc", "warband-group.halfling":"halfling", "warband-group.beastmen":"other_beastmen", "warband-group.undead":"human" };

function context(document: CampaignDocument, warriorId: string, threshold: number | null) {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const warrior = document.campaign.warriors.find((row) => row.id === warriorId);
  const row = post?.pending_advances?.find((item) => String(item["warrior_id"]) === warriorId && (threshold === null || Number(item["threshold"]) === threshold));
  return { post, warrior, row };
}
function inRange(branch: Readonly<Record<string, unknown>>, roll: number) {
  const when=(branch["when"] ?? {}) as Readonly<Record<string,unknown>>;
  return roll >= Number(when["min"] ?? 0) && roll <= Number(when["max"] ?? Infinity);
}
function outcome(reader: CatalogueReader, table: string, total: number, subroll?: number) {
  const doc=reader.campaignSection?.("experience-and-advances");
  const tables=(doc?.["advancement_tables"] ?? []) as readonly Readonly<Record<string,unknown>>[];
  const found=tables.find((item) => item["applies_to"] === (table === "hero" ? "hero" : "henchman_group"));
  const resolution=(found?.["resolution"] ?? {}) as Readonly<Record<string,unknown>>;
  const branch=((resolution["branches"] ?? []) as readonly Readonly<Record<string,unknown>>[]).find((item) => inRange(item,total));
  let result=(branch?.["result"] ?? {}) as Readonly<Record<string,unknown>>;
  if (result["type"] === "roll_table" && subroll !== undefined) result=((((result["branches"] ?? []) as readonly Readonly<Record<string,unknown>>[]).find((item) => inRange(item,subroll)))?.["result"] ?? {}) as Readonly<Record<string,unknown>>;
  return result;
}
function isWizard(reader: CatalogueReader, document: CampaignDocument, warrior: Warrior): boolean {
  const magic=reader.campaignSection?.("magic"); const assignments=(magic?.["lore_assignments"]??{}) as Readonly<Record<string,unknown>>;
  return ((assignments["rows"]??[]) as readonly Readonly<Record<string,unknown>>[]).some((row)=>row["profile_id"]===warrior.profile_id && (row["band"]==null||row["band"]===document.campaign.identity.band_id));
}
function options(result: Readonly<Record<string,unknown>>, wizard: boolean): OpenPayload[] {
  const rows=result["type"] === "choose_one" ? (result["options"] ?? []) as readonly Readonly<Record<string,unknown>>[] : [result];
  return rows.filter((item)=>item["type"]!=="generate_spell"||wizard).map((item) => ({ kind:String(item["type"] ?? "external_resolution"), characteristic:CHARACTERISTICS[String(item["characteristic"] ?? "")] ?? null, amount:Number(item["amount"] ?? 1) }));
}
function update(document: CampaignDocument, battleNumber: number, pending: readonly OpenPayload[], warriors=document.campaign.warriors): CampaignDocument {
  return withCampaign(document,{...document.campaign,warriors,post_battles:document.campaign.post_battles.map((post)=>post.battle_number===battleNumber?{...post,pending_advances:pending}:post)});
}
function maximum(reader: CatalogueReader, document: CampaignDocument, key: string): number | null {
  const long=Object.entries(CHARACTERISTICS).find(([,short])=>short===key)?.[0]; if(!long) return null;
  const group=reader.list?.("warband_group").find((row)=>Array.isArray(row["band_ids"]) && (row["band_ids"] as string[]).includes(document.campaign.identity.band_id));
  const race=BAND_RACE[String(group?.["id"] ?? "")]; if(!race) return null;
  const row=reader.list?.("racial_maximum").find((item)=>item["profile"]===race);
  return row ? Number((row["characteristics"] as Record<string,unknown>)?.[long] ?? NaN) : null;
}
function applyCharacteristic(document: CampaignDocument, reader: CatalogueReader, warrior: Warrior, row: OpenPayload, option: OpenPayload): Result {
  const key=String(option["characteristic"] ?? ""); const current=Number(warrior.stats[key] ?? 0);
  const profile=warrior.profile_id ? reader.queryKnowledge({id:{kind:"profile_id",value:warrior.profile_id}}) : null;
  const base=profile?.ok ? Number((profile.record.data["characteristics"] as Record<string,unknown>)?.[key] ?? NaN) : NaN;
  const cap=warrior.kind==="henchman" && Number.isFinite(base) ? base+1 : maximum(reader,document,key);
  if(cap !== null && Number.isFinite(cap) && current>=cap) {
    const reset={...row,roll_total:null,subroll:null,advance_options:[],roll_history:[...((row["roll_history"] as string[] | undefined)??[]),`Result rejected: ${key} is at its advance cap (${cap}).`]};
    const post=document.campaign.post_battles.find((item)=>!item.complete)!;
    return {ok:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?reset:item))};
  }
  const amount=Number(option["amount"] ?? 1); const changed={...warrior,stats:{...warrior.stats,[key]:current+amount},stat_advances:{...(warrior.stat_advances??{}),[key]:(warrior.stat_advances?.[key]??0)+amount}};
  const committed={...row,committed:true,applied_label:`+${amount} ${key}`}; const post=document.campaign.post_battles.find((item)=>!item.complete)!;
  return {ok:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?committed:item),document.campaign.warriors.map((item)=>item.id===warrior.id?changed:item))};
}

export function resolveAdvanceRoll(document: CampaignDocument, reader: CatalogueReader, input: {warrior_id:string;threshold:number|null;roll_total:number;subroll?:number}): Result {
  const {post,warrior,row}=context(document,input.warrior_id,input.threshold); if(!post||!warrior||!row) return {ok:false,message:"No matching pending advance."};
  if(row["committed"]) return {ok:false,message:"This advance is already committed."};
  if(!Number.isInteger(input.roll_total)||input.roll_total<2||input.roll_total>12) return {ok:false,message:"Advance roll must be between 2 and 12."};
  const result=outcome(reader,String(row["table"]??"hero"),input.roll_total,input.subroll);
  if(result["type"]==="roll_table" && input.subroll===undefined) {
    const changed={...row,roll_total:input.roll_total,subroll:null,advance_options:[]};
    return {ok:true,needs_subroll:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?changed:item))};
  }
  if(input.subroll!==undefined && (!Number.isInteger(input.subroll)||input.subroll<1||input.subroll>6)) return {ok:false,message:"Advance sub-roll must be between 1 and 6."};
  const offered=options(result,isWizard(reader,document,warrior)); const changed={...row,roll_total:input.roll_total,subroll:input.subroll??null,advance_options:offered,promotion_offer:offered.some((item)=>item["kind"]==="promote_henchman")};
  const staged=update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?changed:item));
  if(offered.length===1 && offered[0]["kind"]==="characteristic_increase") return applyCharacteristic(staged,reader,warrior,changed,offered[0]);
  return {ok:true,document:staged};
}

export function commitAdvanceChoice(document: CampaignDocument, reader: CatalogueReader, input:{warrior_id:string;threshold:number|null;kind:string;characteristic?:string;skill_id?:string}): Result {
  const {row,warrior}=context(document,input.warrior_id,input.threshold); if(!row||!warrior) return {ok:false,message:"No matching pending advance."};
  const offered=(row["advance_options"]??[]) as OpenPayload[];
  if(input.kind==="characteristic_increase") { const option=offered.find((item)=>item["kind"]===input.kind&&item["characteristic"]===input.characteristic); return option?applyCharacteristic(document,reader,warrior,row,option):{ok:false,message:"That characteristic is not offered."}; }
  if(input.kind==="choose_skill") {
    const skill=input.skill_id ? reader.queryKnowledge({id:{kind:"skill_id",value:input.skill_id}}):null; if(!skill?.ok||!offered.some((item)=>item["kind"]==="choose_skill")) return {ok:false,message:"That skill is not offered."};
    const category=String(skill.record.data["category"]??""); if(warrior.skill_access?.length&&!warrior.skill_access.includes(category)) return {ok:false,message:"That skill is outside this Hero's skill tables."};
    const name=String(skill.record.names["en"]??input.skill_id); if(warrior.skills.includes(name)) return {ok:false,message:"The warrior already knows that skill."};
    const post=document.campaign.post_battles.find((item)=>!item.complete)!; const committed={...row,committed:true,applied_label:`Skill: ${name}`};
    return {ok:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?committed:item),document.campaign.warriors.map((item)=>item.id===warrior.id?{...item,skills:[...item.skills,name]}:item))};
  }
  return {ok:false,message:"This desktop advance option is not implemented yet."};
}
