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
  const t = locale === "es" ? { post:"Post-batalla",step:"Paso",continue:"Continúa con las acciones guiadas que aparecen debajo.",record:"Registrar batalla",scenario:"Escenario",opponent:"Oponente",result:"Resultado",victory:"Victoria",defeat:"Derrota",draw:"Empate",gold:"Oro",wyrdstone:"Piedra bruja",experience:"Experiencia",ooa:"Fuera de combate",submit:"Registrar batalla" } : { post:"Post-battle",step:"Step",continue:"Continue with the guided actions shown below.",record:"Record a battle",scenario:"Scenario",opponent:"Opponent",result:"Result",victory:"Victory",defeat:"Defeat",draw:"Draw",gold:"Gold",wyrdstone:"Wyrdstone",experience:"Experience",ooa:"Out of action",submit:"Record battle" };
  const available = document.campaign.warriors.filter((warrior) => (warrior.games_to_miss ?? 0) === 0);
  const record = async () => { setBusy(true); await app.runAction("recordBattle", { scenario: scenario || String(scenarios[0]?.id ?? "unknown"), opponent, result, gold_delta: Number(gold) || 0, wyrdstone: Number(wyrdstone) || 0, xp_delta: Number(xp) || 0, out_of_action_ids: outOfAction }); setBusy(false); };
  if (pending) return <section aria-label="Battle"><h2>{t.post} #{pending.battle_number}</h2><p role="status">{t.step} {pending.active_step + 1}/8. {t.continue}</p></section>;
  return <section aria-label="Battle"><h2>{t.record}</h2>{app.error && <output role="alert">{app.error}</output>}<form onSubmit={(event) => { event.preventDefault(); void record(); }}>
    <label>{t.scenario}<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{scenarios.map((row) => <option value={String(row.id)} key={String(row.id)}>{resolveName(row, locale)}</option>)}</select></label>
    <label>{t.opponent}<input required value={opponent} onChange={(event) => setOpponent(event.target.value)} /></label>
    <label>{t.result}<select value={result} onChange={(event) => setResult(event.target.value as typeof result)}><option value="win">{t.victory}</option><option value="loss">{t.defeat}</option><option value="draw">{t.draw}</option></select></label>
    <label>{t.gold}<input type="number" min="0" value={gold} onChange={(event) => setGold(event.target.value)} /></label><label>{t.wyrdstone}<input type="number" min="0" value={wyrdstone} onChange={(event) => setWyrdstone(event.target.value)} /></label><label>{t.experience}<input type="number" min="0" value={xp} onChange={(event) => setXp(event.target.value)} /></label>
    <fieldset><legend>{t.ooa}</legend>{available.map((warrior) => <label key={warrior.id}><input type="checkbox" checked={outOfAction.includes(warrior.id)} onChange={(event) => setOutOfAction((ids) => event.target.checked ? [...ids, warrior.id] : ids.filter((id) => id !== warrior.id))} />{warrior.name}</label>)}</fieldset>
    <button className="primary" disabled={busy || !opponent.trim() || available.length === 0} type="submit">{t.submit}</button>
  </form></section>;
}
