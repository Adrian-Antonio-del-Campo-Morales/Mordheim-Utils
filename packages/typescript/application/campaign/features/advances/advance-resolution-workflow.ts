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
export function wizardLore(reader: CatalogueReader, document: CampaignDocument, warrior: Warrior): string | null {
  const magic=reader.campaignSection?.("magic"); const assignments=(magic?.["lore_assignments"]??{}) as Readonly<Record<string,unknown>>;
  const row=((assignments["rows"]??[]) as readonly Readonly<Record<string,unknown>>[]).find((item)=>item["profile_id"]===warrior.profile_id && (item["band"]==null||item["band"]===document.campaign.identity.band_id));
  return row ? String(row["lore"] ?? "") || null : null;
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
  if(row["promotion_setup_pending"]) return {ok:false,message:"Choose two Hero skill lists before rolling this advance."};
  if(!Number.isInteger(input.roll_total)||input.roll_total<2||input.roll_total>12) return {ok:false,message:"Advance roll must be between 2 and 12."};
  if(row["reroll_exclude_promotion"] && input.roll_total>=10) {
    const reset={...row,roll_total:null,subroll:null,advance_options:[],roll_history:[...((row["roll_history"] as string[]|undefined)??[]),`Rolled ${input.roll_total}: the remaining Henchmen must reroll results 10-12.`]};
    return {ok:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?reset:item))};
  }
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
  if(input.kind==="generate_spell" || input.kind==="duplicate_spell") {
    if(!offered.some((item)=>item["kind"]==="generate_spell") || !input.skill_id) return {ok:false,message:"A spell is not offered by this advance."};
    const loreId=wizardLore(reader,document,warrior); const lore=loreId?reader.queryKnowledge({id:{kind:"lore_id",value:loreId}}):null;
    const spell=lore?.ok ? ((lore.record.data["spells"]??[]) as readonly Readonly<Record<string,unknown>>[]).find((item)=>item["id"]===input.skill_id) : null;
    if(!spell) return {ok:false,message:"That spell is not in this warrior's lore."};
    const name=String(spell["name"]??input.skill_id); const duplicate=warrior.skills.includes(name);
    if(input.kind==="generate_spell"&&duplicate) return {ok:false,message:"The warrior already knows that spell; commit it as a duplicate."};
    if(input.kind==="duplicate_spell"&&!duplicate) return {ok:false,message:"The warrior does not know that spell yet."};
    const changed=input.kind==="generate_spell" ? {...warrior,skills:[...warrior.skills,name]} : {...warrior,spell_difficulty_modifiers:{...(warrior.spell_difficulty_modifiers??{}),[input.skill_id]:(warrior.spell_difficulty_modifiers?.[input.skill_id]??0)-1}};
    const label=input.kind==="generate_spell"?`Spell: ${name}`:`Duplicated spell: ${name} (difficulty -1)`; const post=document.campaign.post_battles.find((item)=>!item.complete)!; const committed={...row,committed:true,applied_label:label};
    return {ok:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?committed:item),document.campaign.warriors.map((item)=>item.id===warrior.id?changed:item))};
  }
  return {ok:false,message:"This desktop advance option is not implemented yet."};
}

function nextWarriorId(document: CampaignDocument, base: string): string {
  const ids=new Set(document.campaign.warriors.map((row)=>row.id)); let candidate=`${base}#promoted`; let index=2;
  while(ids.has(candidate)) candidate=`${base}#promoted-${index++}`;
  return candidate;
}

export function promoteHenchman(document: CampaignDocument, input:{warrior_id:string;threshold:number|null;member_name?:string}): Result {
  const {post,warrior,row}=context(document,input.warrior_id,input.threshold); if(!post||!warrior||!row) return {ok:false,message:"No matching pending promotion."};
  const offered=((row["advance_options"]??[]) as OpenPayload[]).some((item)=>item["kind"]==="promote_henchman");
  if(!offered||warrior.kind!=="henchman") return {ok:false,message:"The Lad's Got Talent is not offered for this warrior."};
  const heroes=document.campaign.warriors.reduce((total,item)=>total+(item.kind==="hero"?(item.quantity??1):0),0);
  if(heroes>=document.campaign.configuration.hero_limit) {
    const reset={...row,roll_total:null,subroll:null,advance_options:[],promotion_offer:false,roll_history:[...((row["roll_history"] as string[]|undefined)??[]),`Hero maximum reached (${document.campaign.configuration.hero_limit}); reroll this advance.`]};
    return {ok:true,document:update(document,post.battle_number,post.pending_advances!.map((item)=>item===row?reset:item))};
  }
  const quantity=warrior.quantity??1; const nonUniform=warrior.equipment.filter((item)=>item.per_model&&item.quantity%quantity!==0);
  if(nonUniform.length) return {ok:false,message:`Normalize group equipment first: ${nonUniform.map((item)=>item.name).join(", ")}.`};
  const heroEquipment=warrior.equipment.filter((item)=>item.per_model&&item.quantity>0).map((item)=>({...item,quantity:item.quantity/quantity,per_model:false}));
  const groupEquipment=warrior.equipment.map((item)=>item.per_model?{...item,quantity:item.quantity-item.quantity/quantity}:item).filter((item)=>item.quantity>0);
  const heroId=nextWarriorId(document,warrior.profile_id??warrior.id); const hero: Warrior={...warrior,id:heroId,name:String(input.member_name??"").trim()||`${warrior.profile_name} Champion`,kind:"hero",quantity:1,equipment:heroEquipment,skills:[],skill_access:[],previous_experience:warrior.previous_experience,stat_advances:{...(warrior.stat_advances??{})}};
  const remaining=quantity-1; const warriors=remaining>0
    ? document.campaign.warriors.map((item)=>item.id===warrior.id?{...item,quantity:remaining,equipment:groupEquipment,name:item.name.endsWith(" group")?item.name:`${item.profile_name} group`}:item).concat(hero)
    : document.campaign.warriors.filter((item)=>item.id!==warrior.id).concat(hero);
  let pending=(post.pending_advances??[]).filter((item)=>remaining>0||item!==row);
  if(remaining>0) pending=pending.map((item)=>item===row?{...item,roll_total:null,subroll:null,advance_options:[],promotion_offer:false,reroll_exclude_promotion:true,roll_history:[...((item["roll_history"] as string[]|undefined)??[]),"Rolled 10-12: one member became a Hero; remaining group rerolls."]}:item);
  pending=[...pending,{warrior_id:hero.id,warrior_name:hero.name,table:"hero",threshold:null,roll_total:null,subroll:null,committed:false,applied_label:"",promotion_immediate:true,promotion_setup_pending:true,promotion_tables:[]}];
  return {ok:true,document:update(document,post.battle_number,pending,warriors)};
}

export function promotionHeroTables(document: CampaignDocument, reader: CatalogueReader): readonly string[] {
  const tables=new Set<string>();
  for(const profile of reader.list?.("profile")??[]) if(profile["band_id"]===document.campaign.identity.band_id&&profile["type"]==="hero") for(const table of (profile["skill_access"]??[]) as string[]) tables.add(table);
  return [...tables];
}

export function setPromotionSkillTables(document: CampaignDocument, reader: CatalogueReader, input:{warrior_id:string;tables:readonly string[]}): Result {
  const {post,warrior,row}=context(document,input.warrior_id,null); if(!post||!warrior||!row||!row["promotion_setup_pending"]) return {ok:false,message:"No pending promotion setup."};
  const selected=[...new Set(input.tables)]; const available=new Set(promotionHeroTables(document,reader));
  if(selected.length!==2||selected.some((item)=>!available.has(item))) return {ok:false,message:"Choose exactly two available Hero skill lists."};
  const changed={...warrior,skill_access:selected}; const pending=post.pending_advances!.map((item)=>item===row?{...item,promotion_tables:selected,promotion_setup_pending:false}:item);
  return {ok:true,document:update(document,post.battle_number,pending,document.campaign.warriors.map((item)=>item.id===warrior.id?changed:item))};
}
