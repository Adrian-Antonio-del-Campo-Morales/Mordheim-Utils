import { useMemo, useState } from "react";

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { resolveName } from "@adapters/knowledge-reader/index";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument, IdString } from "../campaign/types";

export interface BattlePanelProps {
  document: CampaignDocument;
  knowledge?: ArtefactKnowledgeReader;
  locale?: "es" | "en";
  onDocument?: (document: CampaignDocument) => void;
}

export function BattlePanel({ document, knowledge, locale = "en" }: BattlePanelProps) {
  const app = useCampaignApp();
  const scenarios = useMemo(() => knowledge?.list("scenario") ?? [], [knowledge]);
  const [scenario, setScenario] = useState(""); const [opponent, setOpponent] = useState("");
  const [result, setResult] = useState<"win" | "loss" | "draw">("win");
  const [gold, setGold] = useState("0"); const [wyrdstone, setWyrdstone] = useState("0");
  const [xp, setXp] = useState("0"); const [outOfAction, setOutOfAction] = useState<IdString[]>([]); const [busy, setBusy] = useState(false);
  const pending = document.campaign.post_battles.find((post) => !post.complete);
  const available = document.campaign.warriors.filter((warrior) => (warrior.games_to_miss ?? 0) === 0);
  const record = async () => { setBusy(true); await app.runAction("recordBattle", { scenario: scenario || String(scenarios[0]?.id ?? "unknown"), opponent, result, gold_delta: Number(gold) || 0, wyrdstone: Number(wyrdstone) || 0, xp_delta: Number(xp) || 0, out_of_action_ids: outOfAction }); setBusy(false); };
  if (pending) return <section aria-label="Battle"><h2>Post-battle #{pending.battle_number}</h2><p role="status">Step {pending.active_step} of 8. Full product resolution remains unavailable until its domain rules are ported.</p></section>;
  return <section aria-label="Battle"><h2>Record a battle</h2>{app.error && <output role="alert">{app.error}</output>}<form onSubmit={(event) => { event.preventDefault(); void record(); }}>
    <label>Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{scenarios.map((row) => <option value={String(row.id)} key={String(row.id)}>{resolveName(row, locale)}</option>)}</select></label>
    <label>Opponent<input required value={opponent} onChange={(event) => setOpponent(event.target.value)} /></label>
    <label>Result<select value={result} onChange={(event) => setResult(event.target.value as typeof result)}><option value="win">Victory</option><option value="loss">Defeat</option><option value="draw">Draw</option></select></label>
    <label>Gold<input type="number" min="0" value={gold} onChange={(event) => setGold(event.target.value)} /></label><label>Wyrdstone<input type="number" min="0" value={wyrdstone} onChange={(event) => setWyrdstone(event.target.value)} /></label><label>Experience<input type="number" min="0" value={xp} onChange={(event) => setXp(event.target.value)} /></label>
    <fieldset><legend>Out of action</legend>{available.map((warrior) => <label key={warrior.id}><input type="checkbox" checked={outOfAction.includes(warrior.id)} onChange={(event) => setOutOfAction((ids) => event.target.checked ? [...ids, warrior.id] : ids.filter((id) => id !== warrior.id))} />{warrior.name}</label>)}</fieldset>
    <button className="primary" disabled={busy || !opponent.trim() || available.length === 0} type="submit">Record battle</button>
  </form></section>;
}
