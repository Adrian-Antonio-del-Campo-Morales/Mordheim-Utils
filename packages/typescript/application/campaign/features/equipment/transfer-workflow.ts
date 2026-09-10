import type { CampaignDocument } from "../../../../domain/campaign/index";
import { assignEquipment } from "../../../../domain/campaign/kernel/equipment";

type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};

/** Desktop `transfer_equipped_item`, kept atomic for grouped equipment. */
export function transferEquippedItem(document:CampaignDocument,input:{item_id:string;source_id:string;target_id:string}):Result {
  if(input.source_id===input.target_id)return{ok:false,message:"Source and destination are the same warrior."};
  const source=document.campaign.warriors.find((row)=>row.id===input.source_id),target=document.campaign.warriors.find((row)=>row.id===input.target_id),inventory=document.campaign.inventory.find((row)=>row.id===input.item_id);
  const equipment=source?.equipment.find((row)=>row.item_id===input.item_id&&row.acquisition!=="fixed");
  if(!source||!target||!inventory||!equipment)return{ok:false,message:"This transferable equipment is not available."};
  const released=source.kind==="henchman"&&equipment.per_model?(source.quantity??1):1, needed=target.kind==="henchman"?(target.quantity??1):1;
  if(equipment.quantity<released)return{ok:false,message:`${source.name} does not carry a complete transferable set.`};
  if(inventory.stash+released<needed)return{ok:false,message:`${target.name} needs ${needed} copies; only ${inventory.stash+released} are available.`};
  const returned=assignEquipment(document,{warrior_id:source.id,item_id:input.item_id,quantity:released,direction:"stash"});
  if(!returned.ok)return{ok:false,message:returned.message};
  const assigned=assignEquipment(returned.state,{warrior_id:target.id,item_id:input.item_id,quantity:needed,direction:"equip"});
  return assigned.ok?{ok:true,document:assigned.state}:{ok:false,message:assigned.message};
}
