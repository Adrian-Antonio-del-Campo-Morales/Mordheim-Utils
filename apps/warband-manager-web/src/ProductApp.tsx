import { useEffect, useMemo, useRef, useState } from "react";

import type { CampaignAppService } from "./features/campaign/types";
import { CampaignAppProvider } from "./features/campaign/useCampaignApp";
import { CampaignSlice } from "./features/campaign/CampaignSlice";
import { createService, loadKnowledge } from "./features/campaign/default-deps";
import { ArtefactKnowledgeReader, resolveName } from "@adapters/knowledge-reader/index";
import { CampaignStatistics } from "./features/statistics/CampaignStatistics";

type Locale = "es" | "en";
type Page = "home" | "campaign" | "statistics" | "library" | "rules" | "settings";
interface Session { id: string; service: CampaignAppService; source: string; }

const copy = {
  es: { home: "Inicio", campaign: "Campaña", library: "Biblioteca", rules: "Reglas", settings: "Ajustes", newCampaign: "Nueva campaña", newWarband: "Nueva banda", load: "Cargar", save: "Exportar .mordheim", undo: "Deshacer", pdf: "Exportar PDF", welcome: "Tu banda a través del tiempo", empty: "Crea una banda nueva o carga una campaña .mordheim para comenzar.", sessions: "Campañas en esta sesión", kbFail: "No se pudo cargar la base de conocimiento.", retry: "Reintentar", campaignName: "Nombre de campaña", warbandName: "Nombre de banda", band: "Lista de banda", create: "Crear borrador", open: "Abrir", remove: "Retirar", unsaved: "Cambios sin exportar", language: "Idioma", sessionHelp: "Las campañas permanecen en esta sesión. Expórtalas antes de cerrar o recargar.", search: "Buscar reglas", noRules: "No hay resultados." },
  en: { home: "Home", campaign: "Campaign", library: "Library", rules: "Rules", settings: "Settings", newCampaign: "New campaign", newWarband: "New warband", load: "Load", save: "Export .mordheim", undo: "Undo", pdf: "Export PDF", welcome: "A warband through time", empty: "Create a new warband or load a .mordheim campaign to begin.", sessions: "Campaigns in this session", kbFail: "The knowledge base could not be loaded.", retry: "Retry", campaignName: "Campaign name", warbandName: "Warband name", band: "Warband list", create: "Create draft", open: "Open", remove: "Remove", unsaved: "Unexported changes", language: "Language", sessionHelp: "Campaigns remain for this session. Export them before closing or reloading.", search: "Search rules", noRules: "No results." },
} as const;

function download(filename: string, bytes: BlobPart, type: string) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}

type RuleCategory = "special-rules" | "conditions" | "core-rules" | "skills" | "equipment" | "spells" | "scenarios" | "injuries";

function rulesRows(knowledge: ArtefactKnowledgeReader, category: RuleCategory) {
  if (category === "special-rules") return knowledge.rulesDocument("special-rules");
  if (category === "conditions") return knowledge.rulesDocument("conditions");
  if (category === "core-rules") return knowledge.rulesDocument("core-combat");
  if (category === "skills") return knowledge.list("skill");
  if (category === "equipment") return knowledge.list("item");
  if (category === "scenarios") return knowledge.list("scenario");
  if (category === "spells") {
    const lores = knowledge.campaignSection("magic")["lores"];
    return Array.isArray(lores) ? lores.flatMap((lore) => {
      const row = lore as Record<string, unknown>;
      return Array.isArray(row["spells"]) ? row["spells"] as Record<string, unknown>[] : [];
    }) : [];
  }
  const tables = knowledge.campaignSection("serious-injuries")["tables"];
  return Array.isArray(tables) ? tables as Record<string, unknown>[] : [];
}

function profileLinks(knowledge: ArtefactKnowledgeReader, category: RuleCategory, entry: Record<string, unknown>, locale: Locale) {
  if (category !== "skills" && category !== "equipment") return [];
  const entryId = String(entry.id ?? entry.item_id ?? "");
  const skillCategory = String(entry.category ?? "").toLocaleLowerCase();
  const bands = new Map(knowledge.list("band").map((band) => [String(band.id), resolveName(band, locale)]));
  return knowledge.list("profile").flatMap((profile) => {
    const access = Array.isArray(profile.skill_access) ? profile.skill_access.map((value) => String(value).toLocaleLowerCase()) : [];
    const traits = profile.combat_traits && typeof profile.combat_traits === "object" ? profile.combat_traits as Record<string, unknown> : {};
    const starting = Array.isArray(traits.starting_skills) ? traits.starting_skills.map(String) : [];
    const fixed = Array.isArray(profile.fixed_equipment) ? profile.fixed_equipment.map((value) => typeof value === "string" ? value : String((value as Record<string, unknown>).item_id ?? "")) : [];
    const relation = category === "skills"
      ? starting.includes(entryId) ? "starting skill" : skillCategory && access.includes(skillCategory) ? "skill table" : null
      : fixed.includes(entryId) ? "equipment" : null;
    if (!relation) return [];
    return [{ band: bands.get(String(profile.band_id)) ?? String(profile.band_id), profile: resolveName(profile, locale), relation, profileId: String(profile.id) }];
  }).sort((left, right) => `${left.band}:${left.profile}`.localeCompare(`${right.band}:${right.profile}`, locale));
}

function RulesPage({ knowledge, locale }: { knowledge: ArtefactKnowledgeReader; locale: Locale }) {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<RuleCategory>("special-rules");
  const needle = query.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase();
  const rows = rulesRows(knowledge, kind).filter((row) => JSON.stringify(row).normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase().includes(needle));
  const [selected, setSelected] = useState<string | null>(null);
  const selectedRow = rows.find((row) => String(row.id ?? row.item_id) === selected) ?? rows[0];
  const links = selectedRow ? profileLinks(knowledge, kind, selectedRow, locale) : [];
  const categories: readonly [RuleCategory, string][] = locale === "es" ? [["special-rules","Reglas especiales"],["conditions","Condiciones"],["core-rules","Reglas básicas"],["skills","Habilidades"],["equipment","Equipo"],["spells","Hechizos"],["scenarios","Escenarios"],["injuries","Heridas graves"]] : [["special-rules","Special rules"],["conditions","Conditions"],["core-rules","Core rules"],["skills","Skills"],["equipment","Equipment"],["spells","Spells"],["scenarios","Scenarios"],["injuries","Serious injuries"]];
  return <section className="page"><div className="page-title"><p>KNOWLEDGE BASE</p><h1>{copy[locale].rules}</h1></div>
    <div className="rules-toolbar"><div className="tabs">{categories.map(([value,label]) => <button className={kind === value ? "active" : ""} onClick={() => { setKind(value); setSelected(null); setQuery(""); }} key={value}>{label}</button>)}</div><input aria-label={copy[locale].search} placeholder={copy[locale].search} value={query} onChange={(e) => setQuery(e.target.value)} /></div>
    <div className="rules-layout"><div className="rule-list">{rows.map((row) => { const id=String(row.id ?? row.item_id); return <button className={id===String(selectedRow?.id ?? selectedRow?.item_id) ? "active" : ""} onClick={() => setSelected(id)} key={`${kind}:${id}`}>{resolveName(row, locale)}</button>; })}{rows.length===0 && <p>{copy[locale].noRules}</p>}</div>
    <article className="rule-detail">{selectedRow && <><h2>{resolveName(selectedRow, locale)}</h2><p>{localizedText(selectedRow, locale)}</p>{Array.isArray(selectedRow.tags) && <div className="rule-tags">{selectedRow.tags.map((tag) => <span key={String(tag)}>{String(tag)}</span>)}</div>}{Array.isArray(selectedRow.source_refs) && <><h3>{locale === "es" ? "Fuentes" : "Sources"}</h3><ul>{selectedRow.source_refs.map((source, index) => { const row=source as Record<string, unknown>; const label=String(row.section ?? row.manual ?? source); const url=typeof row.url === "string" ? row.url : null; return <li key={`${label}:${index}`}>{url ? <a href={url} target="_blank" rel="noreferrer">{label}</a> : label}</li>; })}</ul></>}{links.length > 0 && <><h3>{locale === "es" ? "Disponible para" : "Available to"}</h3><ul>{links.map((link) => <li key={`${link.band}:${link.profileId}:${link.relation}`}>{link.band} · {link.profile} ({link.relation})</li>)}</ul></>}</>}</article></div></section>;
}

function localizedText(row: Record<string, unknown>, locale: Locale): string {
  for (const key of ["effect", "description", "text", "note"]) {
    const translated = row[`${key}_i18n`];
    if (translated && typeof translated === "object" && typeof (translated as Record<string, unknown>)[locale] === "string") return String((translated as Record<string, unknown>)[locale]);
    if (typeof row[key] === "string") return String(row[key]);
  }
  return locale === "es" ? "No hay texto descriptivo disponible." : "No descriptive text is available.";
}

export function ProductApp() {
  const [locale, setLocale] = useState<Locale>("es");
  const t = copy[locale];
  const [page, setPage] = useState<Page>("home");
  const [knowledge, setKnowledge] = useState<ArtefactKnowledgeReader | null>(null);
  const [kbError, setKbError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [pendingRemove, setPendingRemove] = useState<string | null>(null);
  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [campaignName, setCampaignName] = useState("");
  const [warbandName, setWarbandName] = useState("");
  const [bandId, setBandId] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const active = sessions.find((session) => session.id === activeId) ?? null;

  const loadKb = () => { setKbError(null); void loadKnowledge().then(setKnowledge).catch((e: Error) => setKbError(e.message)); };
  useEffect(loadKb, []);
  useEffect(() => { const subscriptions = sessions.map((s) => s.service.subscribe(() => setRevision((v) => v + 1))); return () => subscriptions.forEach((off) => off()); }, [sessions]);
  useEffect(() => { const dirty = sessions.some((s) => s.service.isDirty()); const guard=(event: BeforeUnloadEvent) => { if (dirty) event.preventDefault(); }; addEventListener("beforeunload", guard); return () => removeEventListener("beforeunload", guard); }, [sessions, revision]);

  const bands = useMemo(() => knowledge?.list("band") ?? [], [knowledge]);
  useEffect(() => { if (!bandId && bands[0]) setBandId(String(bands[0].id)); }, [bands, bandId]);

  const addSession = (service: CampaignAppService, source: string) => { const id = crypto.randomUUID(); setSessions((all) => [...all, { id, service, source }]); setActiveId(id); setPage("campaign"); };
  const create = async () => { if (!knowledge) return; const service=createService(knowledge); const result=await service.createCampaign({ band_id: bandId, campaign_name: campaignName, warband_name: warbandName }); if (result.ok) { addSession(service, "created"); setShowCreate(false); setCampaignName(""); setWarbandName(""); } };
  const importFile = async (file: File) => { if (!knowledge) return; const service=createService(knowledge); const result=await service.importCampaign({ text: await file.text(), confirm_replace: true }); if (result.ok) addSession(service, file.name); else setKbError(result.message); };
  const exportSession = async (session: Session) => { const result=await session.service.prepareExport(); if (result.ok && result.payload) { download(result.payload.filename, result.payload.text, "application/json"); session.service.markExported(result.document); return true; } return false; };
  const exportActive = async () => { if (active) await exportSession(active); };
  const undo = async () => { if (active) await active.service.run("undo", {}); };
  const exportPdf = async () => { if (!active) return; const doc=active.service.current(); if (!doc) return; const { createWarbandPdf } = await import("./features/export/warband-pdf"); const bytes=await createWarbandPdf(doc, locale); download(`${doc.campaign.identity.warband_name.replace(/[^\w-]+/g, "_")}.pdf`, bytes, "application/pdf"); };

  return <div className="app-shell">
    <header className="topbar"><button className="brand" onClick={() => setPage("home")}><strong>MORDHEIM</strong><span>WARBAND MANAGER</span></button>
      <nav aria-label="Primary">{(["home","campaign","statistics","library","rules","settings"] as Page[]).map((key) => <button key={key} className={page===key ? "active" : ""} disabled={(key==="campaign"||key==="statistics")&&!active} onClick={() => setPage(key)}>{key === "statistics" ? locale === "es" ? "Estadísticas" : "Statistics" : t[key]}</button>)}</nav>
      <div className="actions"><button onClick={() => setShowCreate(true)} disabled={!knowledge}>{t.newCampaign}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge}>{t.load}</button><button onClick={undo} disabled={!active?.service.canUndo()}>{t.undo}</button><button onClick={exportActive} disabled={!active}>{t.save}</button><button onClick={() => void exportPdf()} disabled={!active}>{t.pdf}</button></div>
      <input hidden ref={fileRef} type="file" accept=".mordheim,application/json" onChange={(e) => { const f=e.target.files?.[0]; if(f) void importFile(f); e.target.value=""; }} />
    </header>
    {kbError && <output className="global-error" role="alert">{t.kbFail} {kbError} <button onClick={loadKb}>{t.retry}</button></output>}
    <main>
      {page==="home" && <section className="hero"><p>MORDHEIM CAMPAIGN MANAGER</p><h1>{t.welcome}</h1><p>{t.empty}</p><div><button className="primary" onClick={() => setShowCreate(true)} disabled={!knowledge}>{t.newWarband}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge}>{t.load}</button></div>{sessions.length>0 && <SessionCards />}</section>}
      {page==="library" && <section className="page"><div className="page-title"><p>SESSION</p><h1>{t.sessions}</h1><span>{t.sessionHelp}</span></div><SessionCards /></section>}
      {page==="campaign" && active && <CampaignAppProvider service={active.service}><CampaignSlice knowledge={knowledge ?? undefined} locale={locale} /></CampaignAppProvider>}
      {page==="statistics" && active?.service.current() && <CampaignStatistics document={active.service.current()!} locale={locale} />}
      {page==="rules" && knowledge && <RulesPage knowledge={knowledge} locale={locale} />}
      {page==="settings" && <section className="page"><div className="page-title"><p>PREFERENCES</p><h1>{t.settings}</h1></div><label>{t.language}<select value={locale} onChange={(e) => setLocale(e.target.value as Locale)}><option value="es">Español</option><option value="en">English</option></select></label><p>{t.sessionHelp}</p></section>}
    </main>
    {showCreate && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="new-title"><button className="close" aria-label="Close" onClick={() => setShowCreate(false)}>×</button><h2 id="new-title">{t.newCampaign}</h2><label>{t.campaignName}<input value={campaignName} onChange={(e) => setCampaignName(e.target.value)} /></label><label>{t.warbandName}<input value={warbandName} onChange={(e) => setWarbandName(e.target.value)} /></label><label>{t.band}<select value={bandId} onChange={(e) => setBandId(e.target.value)}>{bands.map((row) => <option value={String(row.id)} key={String(row.id)}>{resolveName(row, locale)}</option>)}</select></label><button className="primary" disabled={!campaignName.trim()||!warbandName.trim()||!bandId} onClick={() => void create()}>{t.create}</button></section></div>}
    {pendingRemove && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true"><h2>{locale === "es" ? "Cambios sin exportar" : "Unexported changes"}</h2><p>{locale === "es" ? "Esta campaña tiene cambios. Puedes exportarlos antes de retirarla de la sesión." : "This campaign has changes. You can export them before removing it from the session."}</p><div className="modal-actions"><button className="primary" onClick={() => void (async () => { const session=sessions.find((item) => item.id===pendingRemove); if(session && await exportSession(session)) removeSession(pendingRemove); })()}>{locale === "es" ? "Exportar y retirar" : "Export and remove"}</button><button onClick={() => removeSession(pendingRemove)}>{locale === "es" ? "Descartar" : "Discard"}</button><button onClick={() => setPendingRemove(null)}>{locale === "es" ? "Cancelar" : "Cancel"}</button></div></section></div>}
  </div>;

  function removeSession(id: string) { setSessions((all) => all.filter((item) => item.id!==id)); if(activeId===id) { setActiveId(null); setPage("library"); } setPendingRemove(null); }
  function SessionCards() { return <div className="session-grid">{sessions.map((session) => { const doc=session.service.current()!; return <article key={session.id} className={session.id===activeId ? "session-card active" : "session-card"}><span>{session.service.isDirty() ? t.unsaved : session.source}</span><h2>{doc.campaign.identity.warband_name}</h2>{renameId===session.id ? <form className="inline-form" onSubmit={(event) => { event.preventDefault(); void session.service.run("renameCampaign", { name: renameValue }).then(() => { setRenameId(null); setRenameValue(""); }); }}><input aria-label={t.campaignName} value={renameValue} onChange={(event) => setRenameValue(event.target.value)} /><button disabled={!renameValue.trim()}>OK</button></form> : <p>{doc.campaign.identity.campaign_name} · {doc.campaign.identity.warband_type}</p>}<div><button className="primary" onClick={() => { setActiveId(session.id); setPage("campaign"); }}>{t.open}</button><button onClick={() => { setRenameId(session.id); setRenameValue(doc.campaign.identity.campaign_name); }}>{locale === "es" ? "Renombrar" : "Rename"}</button><button onClick={() => session.service.isDirty() ? setPendingRemove(session.id) : removeSession(session.id)}>{t.remove}</button></div></article>; })}</div>; }
}
