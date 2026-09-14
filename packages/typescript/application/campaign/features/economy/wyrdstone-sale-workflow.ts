import type { CampaignDocument, KnowledgeReader } from "../../../../domain/campaign/index";
import { currentState, withCampaign } from "../../../../domain/campaign/kernel/document";

interface CatalogueReader extends KnowledgeReader { campaignSection?(section:string):Readonly<Record<string,unknown>> }
export interface WyrdstoneSaleQuote { readonly quantity:number; readonly warband_size:number; readonly available:number; readonly profit:number }
type Result={ok:true;document:CampaignDocument;quote:WyrdstoneSaleQuote}|{ok:false;message:string};

function table(reader:CatalogueReader) {
  const document=reader.campaignSection?.("exploration-and-income"); const income=(document?.["income"]??{}) as Readonly<Record<string,unknown>>;
  return (income["wyrdstone_sale"]??{}) as Readonly<Record<string,unknown>>;
}
function range(value:number,bounds:unknown):boolean { const row=(bounds??{}) as Readonly<Record<string,unknown>>; return value>=Number(row["min"]??0)&&(row["max"]==null||value<=Number(row["max"])); }
export function quoteWyrdstoneSale(document:CampaignDocument,reader:CatalogueReader,quantity:number):WyrdstoneSaleQuote {
  const post=document.campaign.post_battles.find((row)=>!row.complete); const base=currentState(document); const available=Math.max(0,(base?.wyrdstone??0)+(post?.wyrdstone_delta??0)-(post?.wyrdstone_sold??0));
  const warbandSize=document.campaign.warriors.reduce((total,row)=>row.kind==="hireling"?total:total+(row.quantity??1),0); const cells=(table(reader)["cells"]??[]) as readonly Readonly<Record<string,unknown>>[];
  const cell=cells.find((row)=>{const when=(row["when"]??{}) as Readonly<Record<string,unknown>>;return range(quantity,when["fragments_sold"])&&range(warbandSize,when["warband_size"]);});
  return{quantity,warband_size:warbandSize,available,profit:Number(cell?.["profit_gc"]??0)};
}
export function sellWyrdstone(document:CampaignDocument,reader:CatalogueReader,quantity:number):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return{ok:false,message:"No pending post-battle sale."};
  if(post.sale_resolved)return{ok:false,message:"Wyrdstone can only be sold once per post-battle sequence."};
  if((post.pending_follow_ups??[]).some((row)=>row["type"]==="exploration_followup"))return{ok:false,message:"Complete the exploration special result before selling wyrdstone."};
  if(!Number.isInteger(quantity)||quantity<0)return{ok:false,message:"Wyrdstone quantity must be a non-negative whole number."}; const quote=quoteWyrdstoneSale(document,reader,quantity);
  if(quantity>quote.available)return{ok:false,message:`Only ${quote.available} shard(s) are available.`};
  const changed={...post,wyrdstone_sold:(post.wyrdstone_sold??0)+quantity,gold_delta:(post.gold_delta??0)+quote.profit,sale_resolved:true,event_log:[...(post.event_log??[]),{step:4,type:"sell_wyrdstone",quantity,gold:quote.profit}]};
  return{ok:true,quote,document:withCampaign(document,{...document.campaign,post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}
