import { useMemo, useState } from "react";
import { ArtefactKnowledgeReader, resolveName } from "@adapters/knowledge-reader/index";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";

export function DraftWorkspace({ document, knowledge, locale }: { document: CampaignDocument; knowledge: ArtefactKnowledgeReader; locale: "es" | "en" }) {
  const app = useCampaignApp();
  const [profileId, setProfileId] = useState(""); const [quantity, setQuantity] = useState(1); const [name, setName] = useState("");
  const profiles = useMemo(() => knowledge.list("profile").filter((row) => row.band_id === document.campaign.identity.band_id), [knowledge, document.campaign.identity.band_id]);
  const selected = profiles.find((row) => String(row.id) === profileId) ?? profiles[0];
  const models = document.campaign.warriors.reduce((sum, warrior) => sum + (warrior.quantity ?? 1), 0);
  const heroes = document.campaign.warriors.reduce((sum, warrior) => sum + (warrior.kind === "hero" ? warrior.quantity ?? 1 : 0), 0);
  const spent = document.campaign.warriors.reduce((sum, warrior) => sum + warrior.cost * (warrior.quantity ?? 1), 0) + document.campaign.inventory.reduce((sum, item) => sum + item.owned * (item.value ?? 0), 0);
  const treasury = document.campaign.configuration.starting_gold - spent;
  const legal = models >= document.campaign.configuration.minimum_models && models <= document.campaign.configuration.maximum_models && heroes > 0 && heroes <= document.campaign.configuration.hero_limit && treasury >= 0;
  const add = async () => { if (!selected) return; const kind = selected.type === "hero" ? "hero" : "henchman"; await app.runAction("composeDraft", { band_id: document.campaign.identity.band_id, name, rows: [{ profile_id: String(selected.id), kind, quantity, equipment: [] }] }); setName(""); setQuantity(1); };
  return <section className="draft-workspace" aria-label="Initial warband draft"><div className="page-title"><p>INITIAL WARBAND</p><h2>{document.campaign.identity.warband_name}</h2><span>{models}/{document.campaign.configuration.maximum_models} models · {heroes}/{document.campaign.configuration.hero_limit} heroes · {treasury} gc</span></div>
    <div className="draft-columns"><article><h3>Roster</h3>{document.campaign.warriors.map((warrior) => <div className="roster-row" key={warrior.id}><div><strong>{warrior.name}</strong><span>{warrior.profile_name} · {warrior.quantity ?? 1} × {warrior.cost} gc</span></div><button onClick={() => void app.runAction("removeDraftRow", { warrior_id: warrior.id })}>Remove</button></div>)}</article>
      <form onSubmit={(event) => { event.preventDefault(); void add(); }}><h3>Add warriors</h3><label>Profile<select value={String(selected?.id ?? "")} onChange={(event) => setProfileId(event.target.value)}>{profiles.map((row) => <option value={String(row.id)} key={String(row.id)}>{resolveName(row, locale)} · {String(row.cost ?? 0)} gc</option>)}</select></label><label>Name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Optional" /></label><label>Quantity<input type="number" min="1" max="15" value={quantity} onChange={(event) => setQuantity(Math.max(1, Number(event.target.value)))} /></label><button className="primary" disabled={!selected} type="submit">Add to roster</button></form></div>
    <button className="primary" disabled={!legal} onClick={() => void app.runAction("commitInitialWarband", {})}>Commit initial warband</button>{!legal && <p role="status">Draft must meet model, hero and treasury limits before commit.</p>}</section>;
}
