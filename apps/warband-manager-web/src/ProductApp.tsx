import { useEffect, useMemo, useRef, useState } from "react";

import type { CampaignAppService } from "./features/campaign/types";
import { CampaignAppProvider } from "./features/campaign/useCampaignApp";
import { CampaignSlice } from "./features/campaign/CampaignSlice";
import { createService, loadKnowledge } from "./features/campaign/default-deps";
import { ArtefactKnowledgeReader, resolveName } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { CampaignStatistics } from "./features/statistics/CampaignStatistics";

type Locale = "es" | "en";
type Page = "home" | "campaign" | "statistics" | "library" | "rules" | "settings";
interface Session { id: string; service: CampaignAppService; source: string; }

const copy = {
  es: { home: "Inicio", campaign: "Campaña", library: "Biblioteca", rules: "Reglas", settings: "Ajustes", newCampaign: "Nueva campaña", newWarband: "Nueva banda", load: "Cargar", save: "Exportar .mordheim", undo: "Deshacer", pdf: "Exportar PDF", welcome: "Tu banda a través del tiempo", empty: "Crea una banda nueva o carga una campaña .mordheim para comenzar.", sessions: "Campañas en esta sesión", kbFail: "No se pudo cargar la base de conocimiento.", retry: "Reintentar", campaignName: "Nombre de campaña", warbandName: "Nombre de banda", band: "Lista de banda", create: "Crear borrador", open: "Abrir", remove: "Retirar", unsaved: "Cambios sin exportar", language: "Idioma", sessionHelp: "Las campañas permanecen en esta sesión. Expórtalas antes de cerrar o recargar.", search: "Buscar reglas", noRules: "No hay resultados.", close: "Cerrar", dismiss: "Cerrar aviso", created: "Creada" },
  en: { home: "Home", campaign: "Campaign", library: "Library", rules: "Rules", settings: "Settings", newCampaign: "New campaign", newWarband: "New warband", load: "Load", save: "Export .mordheim", undo: "Undo", pdf: "Export PDF", welcome: "A warband through time", empty: "Create a new warband or load a .mordheim campaign to begin.", sessions: "Campaigns in this session", kbFail: "The knowledge base could not be loaded.", retry: "Retry", campaignName: "Campaign name", warbandName: "Warband name", band: "Warband list", create: "Create draft", open: "Open", remove: "Remove", unsaved: "Unexported changes", language: "Language", sessionHelp: "Campaigns remain for this session. Export them before closing or reloading.", search: "Search rules", noRules: "No results.", close: "Close", dismiss: "Dismiss", created: "Created" },
} as const;

function download(filename: string, bytes: BlobPart, type: string) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}

type RuleCategory = "special-rules" | "conditions" | "core-rules" | "skills" | "equipment" | "spells" | "scenarios" | "injuries";

function RulesPage({ knowledge, locale }: { knowledge: ArtefactKnowledgeReader; locale: Locale }) {
  const catalogue = new RulesCatalogue(knowledge);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<RuleCategory>("special-rules");
  const rows = query.trim()
    ? catalogue.search(query, { category_id: kind, locale })
    : catalogue.entries(kind, locale);
  const [selected, setSelected] = useState<string | null>(null);
  const selectedRow = rows.find((row) => row.entry_id === selected) ?? rows[0];
  const links = selectedRow ? catalogue.profileLinks(kind, selectedRow, locale) : [];
  const categories: readonly [RuleCategory, string][] = locale === "es" ? [["special-rules","Reglas especiales"],["conditions","Condiciones"],["core-rules","Reglas básicas"],["skills","Habilidades"],["equipment","Equipo"],["spells","Hechizos"],["scenarios","Escenarios"],["injuries","Heridas graves"]] : [["special-rules","Special rules"],["conditions","Conditions"],["core-rules","Core rules"],["skills","Skills"],["equipment","Equipment"],["spells","Spells"],["scenarios","Scenarios"],["injuries","Serious injuries"]];
  return <section className="page"><div className="page-title"><p>KNOWLEDGE BASE</p><h1>{copy[locale].rules}</h1></div>
    <div className="rules-toolbar"><div className="tabs">{categories.map(([value,label]) => <button className={kind === value ? "active" : ""} onClick={() => { setKind(value); setSelected(null); setQuery(""); }} key={value}>{label}</button>)}</div><input aria-label={copy[locale].search} placeholder={copy[locale].search} value={query} onChange={(e) => setQuery(e.target.value)} /></div>
    <div className="rules-layout"><div className="rule-list">{rows.map((row) => <button className={row.entry_id===selectedRow?.entry_id ? "active" : ""} onClick={() => setSelected(row.entry_id)} key={`${kind}:${row.entry_id}`}>{row.name}</button>)}{rows.length===0 && <p>{copy[locale].noRules}</p>}</div>
    <article className="rule-detail">{selectedRow && <><h2>{selectedRow.name}</h2><p>{selectedRow.effect}</p>{selectedRow.tags.length > 0 && <div className="rule-tags">{selectedRow.tags.map((tag) => <span key={String(tag)}>{String(tag)}</span>)}</div>}{selectedRow.source_refs.length > 0 && <><h3>{locale === "es" ? "Fuentes" : "Sources"}</h3><ul>{selectedRow.source_refs.map((source, index) => { const row=source as Record<string, unknown>; const label=String(row.section ?? row.manual ?? source); const url=typeof row.url === "string" ? row.url : null; return <li key={`${label}:${index}`}>{url ? <a href={url} target="_blank" rel="noreferrer">{label}</a> : label}</li>; })}</ul></>}{links.length > 0 && <><h3>{locale === "es" ? "Disponible para" : "Available to"}</h3><ul>{links.map((link) => <li key={`${link.band}:${link.profile_id}:${link.relation}`}>{link.band} · {link.profile} ({link.relation})</li>)}</ul></>}</>}</article></div></section>;
}

export function ProductApp() {
  const [locale, setLocale] = useState<Locale>("es");
  const t = copy[locale];
  const [page, setPage] = useState<Page>("home");
  const [knowledge, setKnowledge] = useState<ArtefactKnowledgeReader | null>(null);
  const [kbError, setKbError] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
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
  const create = async () => { if (!knowledge) return; const service=createService(knowledge); const result=await service.createCampaign({ band_id: bandId, campaign_name: campaignName, warband_name: warbandName }); if (result.ok) { addSession(service, "created"); setShowCreate(false); setCampaignName(""); setWarbandName(""); } else setOperationError(result.message); };
  const importFiles = async (files: readonly File[]) => {
    if (!knowledge) return;
    const imported: Session[] = [];
    const failures: string[] = [];
    for (const file of files) {
      const service = createService(knowledge);
      const result = await service.importCampaign({ text: await file.text(), confirm_replace: true });
      if (result.ok) imported.push({ id: crypto.randomUUID(), service, source: file.name });
      else failures.push(`${file.name}: ${result.message}`);
    }
    if (imported.length) {
      setSessions((all) => [...all, ...imported]);
      setActiveId(imported.at(-1)!.id);
      setPage("campaign");
    }
    if (failures.length) setOperationError(failures.join(" · "));
  };
  const exportSession = async (session: Session) => { const result=await session.service.prepareExport(); if (result.ok && result.payload) { download(result.payload.filename, result.payload.text, "application/json"); session.service.markExported(result.document); return true; } setOperationError(result.ok ? "Export did not produce a file." : result.message); return false; };
  const exportActive = async () => { if (active) await exportSession(active); };
  const undo = async () => { if (active) await active.service.run("undo", {}); };
  const exportPdf = async () => { if (!active) return; const doc=active.service.current(); if (!doc) return; try { const { createWarbandPdf } = await import("./features/export/warband-pdf"); const bytes=await createWarbandPdf(doc, locale); const selected=String(doc.view.selected_moment??"draft:0"); const suffix=selected.startsWith("state:")?`-state-${selected.slice(6)}`:selected.startsWith("post:")?`-post-${selected.slice(5)}`:"-draft"; download(`${doc.campaign.identity.warband_name.replace(/[^\w-]+/g, "_")}${suffix}.pdf`, bytes, "application/pdf"); } catch (error) { setOperationError(error instanceof Error ? error.message : String(error)); } };

  return <div className="app-shell">
    <header className="topbar"><button className="brand" onClick={() => setPage("home")}><strong>MORDHEIM</strong><span>WARBAND MANAGER</span></button>
      <nav aria-label="Primary">{(["home","campaign","statistics","library","rules","settings"] as Page[]).map((key) => <button key={key} className={page===key ? "active" : ""} disabled={(key==="campaign"||key==="statistics")&&!active} onClick={() => setPage(key)}>{key === "statistics" ? locale === "es" ? "Estadísticas" : "Statistics" : t[key]}</button>)}</nav>
      <div className="actions"><button onClick={() => setShowCreate(true)} disabled={!knowledge}>{t.newCampaign}</button><button onClick={() => setShowCreate(true)} disabled={!knowledge}>{t.newWarband}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge}>{t.load}</button><button onClick={undo} disabled={!active?.service.canUndo()}>{t.undo}</button><button onClick={exportActive} disabled={!active}>{t.save}</button><button onClick={() => void exportPdf()} disabled={!active}>{t.pdf}</button></div>
      <input hidden aria-label={locale === "es" ? "Cargar campañas .mordheim" : "Load .mordheim campaigns"} ref={fileRef} type="file" multiple accept=".mordheim,application/json" onChange={(e) => { const files=[...(e.target.files??[])]; if(files.length) void importFiles(files); e.target.value=""; }} />
    </header>
    {kbError && <output className="global-error" role="alert">{t.kbFail} {kbError} <button onClick={loadKb}>{t.retry}</button></output>}
    {operationError && <output className="global-error" role="alert">{operationError} <button onClick={() => setOperationError(null)}>{t.dismiss}</button></output>}
    <main>
      {page==="home" && <section className="hero"><p>MORDHEIM CAMPAIGN MANAGER</p><h1>{t.welcome}</h1><p>{t.empty}</p><div><button className="primary" onClick={() => setShowCreate(true)} disabled={!knowledge}>{t.newWarband}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge}>{t.load}</button></div>{sessions.length>0 && <SessionCards />}</section>}
      {page==="library" && <section className="page"><div className="page-title"><p>SESSION</p><h1>{t.sessions}</h1><span>{t.sessionHelp}</span></div><SessionCards /></section>}
      {page==="campaign" && active && <CampaignAppProvider service={active.service}><CampaignSlice knowledge={knowledge ?? undefined} locale={locale} /></CampaignAppProvider>}
      {page==="statistics" && active?.service.current() && <CampaignStatistics document={active.service.current()!} locale={locale} />}
      {page==="rules" && knowledge && <RulesPage knowledge={knowledge} locale={locale} />}
      {page==="settings" && <section className="page"><div className="page-title"><p>PREFERENCES</p><h1>{t.settings}</h1></div><label>{t.language}<select value={locale} onChange={(e) => setLocale(e.target.value as Locale)}><option value="es">Español</option><option value="en">English</option></select></label><p>{t.sessionHelp}</p></section>}
    </main>
    {showCreate && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="new-title"><button className="close" aria-label={t.close} onClick={() => setShowCreate(false)}>×</button><h2 id="new-title">{t.newCampaign}</h2><label>{t.campaignName}<input value={campaignName} onChange={(e) => setCampaignName(e.target.value)} /></label><label>{t.warbandName}<input value={warbandName} onChange={(e) => setWarbandName(e.target.value)} /></label><label>{t.band}<select value={bandId} onChange={(e) => setBandId(e.target.value)}>{bands.map((row) => <option value={String(row.id)} key={String(row.id)}>{resolveName(row, locale)}</option>)}</select></label><button className="primary" disabled={!campaignName.trim()||!warbandName.trim()||!bandId} onClick={() => void create()}>{t.create}</button></section></div>}
    {pendingRemove && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="discard-session-title"><h2 id="discard-session-title">{locale === "es" ? "Cambios sin exportar" : "Unexported changes"}</h2><p>{locale === "es" ? "Esta campaña tiene cambios. Puedes exportarlos antes de retirarla de la sesión." : "This campaign has changes. You can export them before removing it from the session."}</p><div className="modal-actions"><button className="primary" onClick={() => void (async () => { const session=sessions.find((item) => item.id===pendingRemove); if(session && await exportSession(session)) removeSession(pendingRemove); })()}>{locale === "es" ? "Exportar y retirar" : "Export and remove"}</button><button onClick={() => removeSession(pendingRemove)}>{locale === "es" ? "Descartar" : "Discard"}</button><button onClick={() => setPendingRemove(null)}>{locale === "es" ? "Cancelar" : "Cancel"}</button></div></section></div>}
  </div>;

  function removeSession(id: string) { const remaining=sessions.filter((item) => item.id!==id); setSessions(remaining); if(activeId===id) { setActiveId(remaining.at(-1)?.id??null); setPage(remaining.length ? "campaign" : "library"); } setPendingRemove(null); }
  function SessionCards() { return <div className="session-grid">{sessions.map((session) => { const doc=session.service.current()!; return <article key={session.id} className={session.id===activeId ? "session-card active" : "session-card"}><span>{session.service.isDirty() ? t.unsaved : session.source === "created" ? t.created : session.source}</span><h2>{doc.campaign.identity.warband_name}</h2>{renameId===session.id ? <form className="inline-form" onSubmit={(event) => { event.preventDefault(); void session.service.run("renameCampaign", { name: renameValue }).then(() => { setRenameId(null); setRenameValue(""); }); }}><input aria-label={t.campaignName} value={renameValue} onChange={(event) => setRenameValue(event.target.value)} /><button disabled={!renameValue.trim()}>OK</button></form> : <p>{doc.campaign.identity.campaign_name} · {doc.campaign.identity.warband_type}</p>}<div><button className="primary" onClick={() => { setActiveId(session.id); setPage("campaign"); }}>{t.open}</button><button onClick={() => { setRenameId(session.id); setRenameValue(doc.campaign.identity.campaign_name); }}>{locale === "es" ? "Renombrar" : "Rename"}</button><button onClick={() => session.service.isDirty() ? setPendingRemove(session.id) : removeSession(session.id)}>{t.remove}</button></div></article>; })}</div>; }
}
