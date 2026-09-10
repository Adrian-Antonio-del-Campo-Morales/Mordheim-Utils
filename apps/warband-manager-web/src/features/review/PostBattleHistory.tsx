import type { CampaignDocument } from "../campaign/types";

export function PostBattleHistory({ document, battleNumber, locale }: { readonly document: CampaignDocument; readonly battleNumber: number; readonly locale: "es" | "en" }) {
  const post = document.campaign.post_battles.find((row) => row.battle_number === battleNumber);
  const t = locale === "es" ? { title:"POST-BATALLA",missing:"No se encontró el post-batalla.",complete:"Completado",steps:"Pasos completados",gold:"Cambio de oro",wyrdstone:"Cambio de piedra bruja",events:"REGISTRO DE EVENTOS",empty:"No se registraron eventos detallados." } : { title:"POST-BATTLE",missing:"Post-battle not found.",complete:"Complete",steps:"Completed steps",gold:"Gold change",wyrdstone:"Wyrdstone change",events:"EVENT LOG",empty:"No detailed events were recorded." };
  if (!post) return <section className="page"><p>{t.missing}</p></section>;
  return <section className="page" aria-label={`${t.title} #${battleNumber}`}>
    <div className="page-title"><p>{t.title} #{battleNumber}</p><h2>{t.complete}</h2></div>
    <dl className="campaign-metrics"><div><dt>{t.steps}</dt><dd>{post.completed_steps.length}/8</dd></div><div><dt>{t.gold}</dt><dd>{post.gold_delta ?? 0} gc</dd></div><div><dt>{t.wyrdstone}</dt><dd>{post.wyrdstone_delta ?? 0}</dd></div></dl>
    <article className="rule-detail"><h3>{t.events}</h3>{post.event_log?.length ? <ol>{post.event_log.map((event, index) => <li key={`${index}:${String(event.type)}`}><strong>{String(event.type ?? "event")}</strong> — {String(event.description ?? "")}</li>)}</ol> : <p>{t.empty}</p>}</article>
  </section>;
}
