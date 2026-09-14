import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import type { CampaignAppService } from "./features/campaign/types";
import { CampaignAppProvider, localizeErrorMessage } from "./features/campaign/useCampaignApp";
import { OperationProgress, withOperationProgress } from "./features/common/OperationProgress";
import { createService, loadKnowledge } from "./features/campaign/default-deps";
import { ArtefactKnowledgeReader, resolveName, titleCaseDisplay } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { knowledgeName } from "./features/campaign/displayText";
import { warbandVariants } from "@domain/campaign/band-variants";

type Locale = "es" | "en";
type Page = "campaign" | "statistics" | "rules" | "settings";
type BandSet = "core" | "1a" | "1b" | "1c" | "trollheim";
interface Session { id: string; service: CampaignAppService; source: string; }

const CampaignSlice = lazy(() => import("./features/campaign/CampaignSlice").then(({ CampaignSlice }) => ({ default: CampaignSlice })));
const CampaignStatistics = lazy(() => import("./features/statistics/CampaignStatistics").then(({ CampaignStatistics }) => ({ default: CampaignStatistics })));

const BAND_SETS: readonly BandSet[] = ["core", "1a", "1b", "1c", "trollheim"];

function bandSetFor(row: unknown): BandSet | null {
  const values = row as Readonly<Record<string, unknown>>;
  const set = values.collection === "trollheim" ? "trollheim" : String(values.grade).toLowerCase();
  return BAND_SETS.includes(set as BandSet) ? set as BandSet : null;
}

function bandSetLabel(set: BandSet): string {
  return set === "trollheim" ? "Trollheim" : set === "core" ? "Core" : set.toUpperCase();
}

const copy = {
  es: { home: "Inicio", campaign: "Campaña", library: "Biblioteca", rules: "Reglas", settings: "Ajustes", newCampaign: "Nueva Campaña", newWarband: "Nueva Banda", load: "Cargar", save: "Exportar .mordheim", undo: "Deshacer", pdf: "Exportar PDF", welcome: "Tu banda a través del tiempo", empty: "Crea una banda nueva o carga una campaña .mordheim para comenzar.", bandCategoriesHint: "Puedes seleccionar categorías de bandas en Ajustes", sessions: "Campañas en Esta Sesión", kbFail: "No se pudo cargar la base de conocimiento.", retry: "Reintentar", campaignName: "Nombre de Campaña", warbandName: "Nombre de Banda", band: "Lista de Banda", create: "Crear Borrador", open: "Abrir", remove: "Retirar", unsaved: "Cambios Sin Exportar", language: "Idioma", sessionHelp: "Las campañas permanecen en esta sesión. Expórtalas antes de cerrar o recargar.", search: "Buscar Reglas", noRules: "No hay resultados.", close: "Cerrar", dismiss: "Cerrar Aviso", created: "Creada", exportEmpty: "La exportación no generó ningún archivo.", primaryNav: "Navegación Principal" },
  en: { home: "Home", campaign: "Campaign", library: "Library", rules: "Rules", settings: "Settings", newCampaign: "New Campaign", newWarband: "New Warband", load: "Load", save: "Export .mordheim", undo: "Undo", pdf: "Export PDF", welcome: "A warband through time", empty: "Create a new warband or load a .mordheim campaign to begin.", bandCategoriesHint: "You can select warband categories in Settings", sessions: "Campaigns in This Session", kbFail: "The knowledge base could not be loaded.", retry: "Retry", campaignName: "Campaign Name", warbandName: "Warband Name", band: "Warband List", create: "Create Draft", open: "Open", remove: "Remove", unsaved: "Unexported Changes", language: "Language", sessionHelp: "Campaigns remain for this session. Export them before closing or reloading.", search: "Search Rules", noRules: "No results.", close: "Close", dismiss: "Dismiss Notice", created: "Created", exportEmpty: "Export did not produce a file.", primaryNav: "Primary Navigation" },
} as const;

function download(filename: string, bytes: BlobPart, type: string) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}

type RuleCategory = "special-rules" | "band-rules" | "conditions" | "core-rules" | "skills" | "equipment" | "spells" | "scenarios" | "injuries";

function RulesPage({ knowledge, locale }: { knowledge: ArtefactKnowledgeReader; locale: Locale }) {
  const catalogue = new RulesCatalogue(knowledge);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<RuleCategory>("special-rules");
  const rows = query.trim()
    ? catalogue.search(query, { locale })
    : catalogue.entries(kind, locale);
  const ruleGroups = kind === "spells" && !query.trim()
    ? ((knowledge.campaignSection("magic").lores ?? []) as readonly Readonly<Record<string, unknown>>[])
        .map((lore) => ({ id: String(lore.id), name: resolveName(lore, locale), rows: rows.filter((row) => row.lore_id === lore.id) }))
        .filter((group) => group.rows.length)
        .sort((a, b) => a.name.localeCompare(b.name, locale, { sensitivity: "base" }))
    : kind === "band-rules" && !query.trim()
      ? knowledge.list("band")
          .map((band) => ({ id: String(band.id), name: resolveName(band, locale), rows: rows.filter((row) => row.band_id === band.id) }))
          .filter((group) => group.rows.length)
          .sort((a, b) => a.name.localeCompare(b.name, locale, { sensitivity: "base" }))
    : [];
  const [selected, setSelected] = useState<string | null>(null);
  const ruleDetailRef = useRef<HTMLElement>(null);
  const resultRef = useRef<HTMLButtonElement | null>(null);
  const resultScroll = useRef(0);
  function openRule(id: string, button: HTMLButtonElement) {
    resultRef.current = button;
    resultScroll.current = window.scrollY;
    setSelected(id);
  }
  useLayoutEffect(() => {
    if (!window.matchMedia?.("(max-width: 680px)").matches) return;
    if (selected) {
      ruleDetailRef.current?.focus({ preventScroll: true });
      ruleDetailRef.current?.scrollIntoView({ block: "start" });
    } else if (resultRef.current) {
      resultRef.current.focus({ preventScroll: true });
      window.scrollTo({ top: resultScroll.current });
    }
  }, [selected]);
  const selectedRow = rows.find((row) => `${row.category_id}:${row.entry_id}` === selected) ?? rows[0];
  const links = selectedRow ? catalogue.profileLinks(selectedRow.category_id, selectedRow, locale) : [];
  const categories: readonly [RuleCategory, string][] = locale === "es" ? [["special-rules","Reglas Generales"],["band-rules","Reglas de Banda"],["conditions","Condiciones"],["core-rules","Reglas Básicas"],["skills","Habilidades"],["equipment","Equipo"],["spells","Hechizos"],["scenarios","Escenarios"],["injuries","Heridas Graves"]] : [["special-rules","Shared Rules"],["band-rules","Warband Rules"],["conditions","Conditions"],["core-rules","Core Rules"],["skills","Skills"],["equipment","Equipment"],["spells","Spells"],["scenarios","Scenarios"],["injuries","Serious Injuries"]];
  return <section className={`page rules-page ${selected ? "show-rule-detail" : "show-rule-list"}`}><div className="page-title"><h1>{copy[locale].rules}</h1><span>{locale === "es" ? "Busca y explora la base de conocimiento de Mordheim sin salir de la gestión de campaña." : "Search and browse the Mordheim knowledge base without leaving campaign management."}</span></div>
    <div className="rules-toolbar"><div className="tabs">{categories.map(([value,label]) => <button className={kind === value ? "active" : ""} onClick={() => { setKind(value); setSelected(null); setQuery(""); resultRef.current = null; }} key={value}>{label}</button>)}</div><input aria-label={copy[locale].search} placeholder={copy[locale].search} value={query} onChange={(e) => { setQuery(e.target.value); setSelected(null); resultRef.current = null; }} /></div>
    <div className="rules-layout"><div className="rule-list">{ruleGroups.length ? ruleGroups.map((group) => kind === "band-rules" ? <details className="rule-group collapsible" key={group.id}><summary>{titleCaseDisplay(group.name)}</summary>{group.rows.map((row) => <button className={row===selectedRow ? "active" : ""} onClick={(event) => openRule(`${row.category_id}:${row.entry_id}`, event.currentTarget)} key={row.entry_id}><span>{titleCaseDisplay(row.name)}</span></button>)}</details> : <section className="rule-group" aria-labelledby={`rule-group-${group.id}`} key={group.id}><h3 id={`rule-group-${group.id}`}>{titleCaseDisplay(group.name)}</h3>{group.rows.map((row) => <button className={row===selectedRow ? "active" : ""} onClick={(event) => openRule(`${row.category_id}:${row.entry_id}`, event.currentTarget)} key={row.entry_id}><span>{titleCaseDisplay(row.name)}</span></button>)}</section>) : rows.map((row) => <button className={row===selectedRow ? "active" : ""} onClick={(event) => openRule(`${row.category_id}:${row.entry_id}`, event.currentTarget)} key={`${row.category_id}:${row.entry_id}`}><span>{titleCaseDisplay(row.name)}</span>{query.trim() && <small>{categories.find(([id]) => id === row.category_id)?.[1]}</small>}</button>)}{rows.length===0 && <p>{copy[locale].noRules}</p>}</div>
    <article className="rule-detail" ref={ruleDetailRef} tabIndex={-1}>{selectedRow && <><button className="rule-back" onClick={() => setSelected(null)}>{locale === "es" ? "← Volver a resultados" : "← Back to results"}</button><h2>{titleCaseDisplay(selectedRow.name)}</h2><p className="rule-prose">{selectedRow.effect}</p>{selectedRow.tags.length > 0 && <div className="rule-tags">{selectedRow.tags.map((tag) => <span key={String(tag)}>{String(tag)}</span>)}</div>}{selectedRow.source_refs.length > 0 && <><h3>{locale === "es" ? "Fuentes" : "Sources"}</h3><ul>{selectedRow.source_refs.map((source, index) => { const row=source as Record<string, unknown>; const label=String(row.section ?? row.manual ?? source); const url=typeof row.url === "string" ? row.url : null; return <li key={`${label}:${index}`}>{url ? <a href={url} target="_blank" rel="noreferrer">{label}</a> : label}</li>; })}</ul></>}{links.length > 0 && <><h3>{locale === "es" ? "Disponible para" : "Available to"}</h3><ul>{links.map((link) => <li key={`${link.band}:${link.profile_id}:${link.relation}`}>{titleCaseDisplay(link.band)} · {titleCaseDisplay(link.profile)} ({titleCaseDisplay(link.relation)})</li>)}</ul></>}</>}</article></div></section>;
}

export function ProductApp() {
  const [locale, setLocale] = useState<Locale>("es");
  const t = copy[locale];
  const [page, setPage] = useState<Page>("campaign");
  const [knowledge, setKnowledge] = useState<ArtefactKnowledgeReader | null>(null);
  const [kbError, setKbError] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [pendingRemove, setPendingRemove] = useState<string | null>(null);
  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [campaignName, setCampaignName] = useState("");
  const [bandId, setBandId] = useState("");
  const [variantId, setVariantId] = useState("");
  const [enabledBandSets, setEnabledBandSets] = useState<ReadonlySet<BandSet>>(() => new Set(BAND_SETS));
  const fileRef = useRef<HTMLInputElement>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);
  const libraryButtonRef = useRef<HTMLButtonElement>(null);
  const active = sessions.find((session) => session.id === activeId) ?? null;

  const loadKb = () => { setKbError(null); void loadKnowledge().then(setKnowledge).catch((e: Error) => setKbError(e.message)); };
  useEffect(loadKb, []);
  useEffect(() => { const subscriptions = sessions.map((s) => s.service.subscribe(() => setRevision((v) => v + 1))); return () => subscriptions.forEach((off) => off()); }, [sessions]);
  useEffect(() => { const dirty = sessions.some((s) => s.service.isDirty()); const guard=(event: BeforeUnloadEvent) => { if (dirty) event.preventDefault(); }; addEventListener("beforeunload", guard); return () => removeEventListener("beforeunload", guard); }, [sessions, revision]);

  const bands = useMemo(() => [...(knowledge?.list("band") ?? [])]
    .filter((row) => { const set = bandSetFor(row); return set !== null && enabledBandSets.has(set); })
    .sort((a, b) => resolveName(a, locale).localeCompare(resolveName(b, locale), locale)), [knowledge, locale, enabledBandSets]);
  useEffect(() => { if (!bands.some((row) => String(row.id) === bandId)) setBandId(bands[0] ? String(bands[0].id) : ""); }, [bands, bandId]);
  const variants = useMemo(() => knowledge && bandId ? warbandVariants(knowledge, bandId) : [], [knowledge, bandId]);
  useEffect(() => { setVariantId(""); }, [bandId]);
  const toggleBandSet = (set: BandSet) => setEnabledBandSets((current) => {
    const next = new Set(current);
    if (next.has(set)) next.delete(set); else next.add(set);
    return next;
  });

  const addSession = (service: CampaignAppService, source: string) => { const id = crypto.randomUUID(); setSessions((all) => [...all, { id, service, source }]); setActiveId(id); setPage("campaign"); };
  const create = async () => { if (!knowledge) return; const band=bands.find((row)=>String(row.id)===bandId); if(!band)return; await withOperationProgress(async () => { try { const service=createService(knowledge); const result=await service.createCampaign({ band_id: bandId, campaign_name: campaignName.trim() || (locale === "es" ? "Nueva Campaña de Mordheim" : "New Mordheim Campaign"), warband_name: resolveName(band, locale), ...(variantId ? { variant: variantId } : {}) }); if (result.ok) { addSession(service, "created"); setShowCreate(false); setCampaignName(""); setVariantId(""); } else setOperationError(result.message); } catch(error) { setOperationError(error instanceof Error ? error.message : String(error)); } }); };
  const importFiles = async (files: readonly File[]) => { await withOperationProgress(async () => {
    if (!knowledge) return;
    const imported: Session[] = [];
    const failures: string[] = [];
    for (const file of files) {
      try {
        const service = createService(knowledge);
        const result = await service.importCampaign({ text: await file.text(), confirm_replace: true });
        if (result.ok) imported.push({ id: crypto.randomUUID(), service, source: file.name });
        else failures.push(`${file.name}: ${result.message}`);
      } catch (error) {
        failures.push(`${file.name}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    if (imported.length) {
      setSessions((all) => [...all, ...imported]);
      setActiveId(imported.at(-1)!.id);
      setPage("campaign");
    }
    if (failures.length) setOperationError(failures.join(" · "));
  }); };
  const exportSession = async (session: Session) => withOperationProgress(async () => { try { const result=await session.service.prepareExport(); if (result.ok && result.payload) { download(result.payload.filename, result.payload.text, "application/json"); session.service.markExported(result.document); return true; } setOperationError(result.ok ? t.exportEmpty : result.message); } catch(error) { setOperationError(error instanceof Error ? error.message : String(error)); } return false; });
  const exportActive = async () => { if (active) await exportSession(active); };
  const undo = useCallback(async () => { if (!active) return; await withOperationProgress(async () => { try { const result=await active.service.run("undo", {}); if (!result.ok) setOperationError(result.message); } catch(error) { setOperationError(error instanceof Error ? error.message : String(error)); } }); }, [active]);
  const closeCreate = () => { setShowCreate(false); requestAnimationFrame(() => createButtonRef.current?.focus()); };
  const closeLibrary = () => { setShowLibrary(false); requestAnimationFrame(() => libraryButtonRef.current?.focus()); };
  useEffect(() => { const onKeyDown=(event:KeyboardEvent)=>{const target=event.target as HTMLElement|null;const editing=target?.matches("input, textarea, select, [contenteditable=true]");if(event.key==="Escape"){if(document.querySelector(":popover-open"))return;if(pendingRemove)setPendingRemove(null);else if(showCreate)closeCreate();else if(showLibrary)closeLibrary();else if(showMore)setShowMore(false);}else if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="z"&&!editing&&active?.service.canUndo()){event.preventDefault();void undo();}};addEventListener("keydown",onKeyDown);return()=>removeEventListener("keydown",onKeyDown);},[active,pendingRemove,showCreate,showLibrary,showMore,undo]);
  const exportPdf = async () => { if (!active) return; const doc=active.service.current(); if (!doc) return; await withOperationProgress(async () => { try { const { createWarbandPdf } = await import("./features/export/warband-pdf"); const bytes=await createWarbandPdf(doc, locale, knowledge ?? undefined); const selected=String(doc.view.selected_moment??"draft:0"); const suffix=selected.startsWith("state:")?`-state-${selected.slice(6)}`:"-draft"; download(`${doc.campaign.identity.warband_name.replace(/[^\w-]+/g, "_")}${suffix}.pdf`, bytes, "application/pdf"); } catch (error) { setOperationError(error instanceof Error ? error.message : String(error)); } }); };

  return <div className="app-shell" onPointerDownCapture={(event) => { const control=(event.target as Element).closest<HTMLElement>("button:disabled, input:disabled, select:disabled, [aria-disabled=true]"); if(control)setOperationError(control.dataset.disabledReason || (locale === "es" ? "Esta acción no está disponible en el estado actual." : "This action is not available in the current state.")); }}>
    <OperationProgress locale={locale} />
    <header className="topbar"><button className="brand" onClick={() => setPage("campaign")}><strong>{locale === "es" ? "GESTOR DE CAMPAÑAS DE MORDHEIM" : "MORDHEIM CAMPAIGN MANAGER"}</strong><span>{locale === "es" ? "UNA BANDA A TRAVÉS DEL TIEMPO" : "A WARBAND THROUGH TIME"}</span></button>
      <div className="mobile-context" aria-live="polite" aria-label={`${active?.service.current()?.campaign.identity.campaign_name ?? "Mordheim"}. ${active?.service.isDirty() ? t.unsaved : active ? (locale === "es" ? "Guardada" : "Saved") : t.empty}`} data-title={active?.service.current()?.campaign.identity.campaign_name ?? "Mordheim"} data-status={active?.service.isDirty() ? t.unsaved : active ? (locale === "es" ? "Guardada" : "Saved") : t.empty} />
      <nav aria-label={t.primaryNav}>{(["campaign","rules","settings"] as const).map((key,index) => <button key={key} className={page===key || (key==="campaign"&&page==="statistics") ? "active" : ""} onClick={() => setPage(key)}><span aria-hidden="true">{["◆","☰","⚙"][index]}</span>{t[key]}</button>)}</nav>
      <div className="actions"><button ref={createButtonRef} onClick={() => setShowCreate(true)} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}><span aria-hidden="true">＋</span>{t.newCampaign}</button><button ref={libraryButtonRef} onClick={() => setShowLibrary(true)}><span aria-hidden="true">▣</span>{locale === "es" ? "Campañas" : "Campaigns"}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}><span aria-hidden="true">↥</span>{t.load}</button><button onClick={exportActive} disabled={!active} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña antes de guardarla." : "Open or create a campaign before saving it.") : undefined}><span aria-hidden="true">↓</span>{locale === "es" ? "Guardar" : "Save"}</button><button onClick={undo} disabled={!active?.service.canUndo()} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña antes de deshacer cambios." : "Open or create a campaign before undoing changes.") : !active.service.canUndo() ? (locale === "es" ? "No hay ninguna acción que se pueda deshacer." : "There is no action to undo.") : undefined}><span aria-hidden="true">↶</span>{t.undo}</button><button onClick={() => void exportPdf()} disabled={!active} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña antes de exportar el PDF." : "Open or create a campaign before exporting the PDF.") : undefined}><span aria-hidden="true">▤</span>{t.pdf}</button></div>
      <input hidden aria-label={locale === "es" ? "Cargar campañas .mordheim" : "Load .mordheim campaigns"} ref={fileRef} type="file" multiple accept=".mordheim,application/json" onChange={(e) => { const files=[...(e.target.files??[])]; if(files.length) void importFiles(files); e.target.value=""; }} />
    </header>
    {kbError && <output className="global-error" role="alert">{t.kbFail} {kbError} <button onClick={loadKb}>{t.retry}</button></output>}
    {operationError && <output className="global-error" role="alert">{localizeErrorMessage(operationError, locale)} <button onClick={() => setOperationError(null)}>{t.dismiss}</button></output>}
    <main>
      {page==="campaign" && active && <CampaignAppProvider service={active.service} locale={locale}><Suspense fallback={null}><CampaignSlice knowledge={knowledge ?? undefined} locale={locale} /></Suspense></CampaignAppProvider>}
      {page==="campaign" && !active && <section className="empty-workspace"><h1>{t.campaign}</h1><p>{t.empty}</p><p>{t.bandCategoriesHint}</p><div><button className="primary" onClick={() => setShowCreate(true)} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}>{t.newCampaign}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}>{t.load}</button></div></section>}
      {page==="campaign" && active && <button className="statistics-link" onClick={() => setPage("statistics")}>{locale === "es" ? "Estadísticas" : "Statistics"}</button>}
      {page==="statistics" && active?.service.current() && <Suspense fallback={null}><CampaignStatistics document={active.service.current()!} locale={locale} /></Suspense>}
      {page==="rules" && knowledge && <RulesPage knowledge={knowledge} locale={locale} />}
      {page==="settings" && <section className="page"><div className="page-title"><h1>{t.settings}</h1><span>{locale === "es" ? "Preferencias de campaña, selección de reglamento y opciones de presentación." : "Campaign preferences, rules selection and presentation options."}</span></div><div className="settings-card"><label><span>{t.language.toUpperCase()}</span><select value={locale} onChange={(e) => setLocale(e.target.value as Locale)}><option value="es">Español</option><option value="en">English</option></select></label><fieldset className="band-set-picker"><legend>{locale === "es" ? "Conjuntos de bandas disponibles" : "Available warband sets"}</legend>{BAND_SETS.map((set) => <label key={set}><input type="checkbox" checked={enabledBandSets.has(set)} onChange={() => toggleBandSet(set)} /><span>{set === "trollheim" ? "Trollheim" : set === "core" ? "Core" : set.toUpperCase()}</span></label>)}</fieldset><p>{locale === "es" ? "La selección se aplica a las nuevas campañas durante esta sesión." : "The selection applies to new campaigns during this session."}</p><div><span>{locale === "es" ? "Carpeta de Campaña" : "Campaign Storage"}</span><strong>{locale === "es" ? "Sesión del navegador" : "Browser session"}</strong></div><p>{t.sessionHelp}</p></div></section>}
    </main>
    <nav className="mobile-nav" aria-label={locale === "es" ? "Navegación móvil" : "Mobile navigation"}>{(["campaign","rules","settings"] as const).map((key,index) => <button aria-current={page === key || (key === "campaign" && page === "statistics") ? "page" : undefined} aria-label={`${t[key]} · ${locale === "es" ? "móvil" : "mobile"}`} key={key} className={page===key || (key==="campaign"&&page==="statistics") ? "active" : ""} onClick={() => { setPage(key); setShowMore(false); }}><span aria-hidden="true">{["◆","☰","⚙"][index]}</span>{t[key]}</button>)}<button aria-label={locale === "es" ? "Más acciones" : "More actions"} aria-expanded={showMore} aria-controls="mobile-more-menu" onClick={() => setShowMore((value) => !value)}><span aria-hidden="true">•••</span>{locale === "es" ? "Más" : "More"}</button></nav>
    {showMore && <div className="mobile-more-backdrop" onClick={() => setShowMore(false)}><section id="mobile-more-menu" className="mobile-more" role="dialog" aria-modal="true" aria-label={locale === "es" ? "Más acciones" : "More actions"} onClick={(event) => event.stopPropagation()}><header><strong>{locale === "es" ? "Acciones" : "Actions"}</strong><button aria-label={t.close} onClick={() => setShowMore(false)}>×</button></header><button onClick={() => { setShowMore(false); setShowCreate(true); }} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}>＋ {t.newCampaign}</button><button onClick={() => { setShowMore(false); setShowLibrary(true); }}>▣ {locale === "es" ? "Campañas" : "Campaigns"}</button><button onClick={() => { setShowMore(false); fileRef.current?.click(); }} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}>↥ {t.load}</button><button onClick={() => { setShowMore(false); void exportActive(); }} disabled={!active} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña antes de guardarla." : "Open or create a campaign before saving it.") : undefined}>↓ {locale === "es" ? "Guardar" : "Save"}</button><button onClick={() => { setShowMore(false); void undo(); }} disabled={!active?.service.canUndo()} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña antes de deshacer cambios." : "Open or create a campaign before undoing changes.") : !active.service.canUndo() ? (locale === "es" ? "No hay ninguna acción que se pueda deshacer." : "There is no action to undo.") : undefined}>↶ {t.undo}</button><button onClick={() => { setShowMore(false); void exportPdf(); }} disabled={!active} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña antes de exportar el PDF." : "Open or create a campaign before exporting the PDF.") : undefined}>▤ {t.pdf}</button><button onClick={() => { setShowMore(false); setPage("statistics"); }} disabled={!active} data-disabled-reason={!active ? (locale === "es" ? "Abre o crea una campaña para consultar sus estadísticas." : "Open or create a campaign to view its statistics.") : undefined}>▥ {locale === "es" ? "Estadísticas" : "Statistics"}</button></section></div>}
      {showCreate && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="new-title"><button className="close" aria-label={t.close} onClick={closeCreate}>×</button><h2 id="new-title">{locale === "es" ? "Crear Campaña" : "Create Campaign"}</h2><p>{locale === "es" ? "Empieza con la información mínima. La banda inicial se construye después." : "Start with the minimum information. The initial warband is built next."}</p><label>{t.campaignName}<input autoFocus placeholder={locale === "es" ? "Nueva Campaña de Mordheim" : "New Mordheim Campaign"} value={campaignName} onChange={(e) => setCampaignName(e.target.value)} /></label><fieldset className="band-picker"><legend>{t.band}</legend>{bands.map((row) => { const set = bandSetFor(row); return <label key={String(row.id)}><input type="radio" name="band" value={String(row.id)} checked={bandId===String(row.id)} onChange={(e)=>setBandId(e.target.value)} /><span>{resolveName(row, locale)}</span>{set && <small>{bandSetLabel(set)}</small>}</label>; })}</fieldset>{variants.length > 0 && <label>{locale === "es" ? "Variante de banda" : "Warband variant"}<select value={variantId} onChange={(event)=>setVariantId(event.target.value)}><option value="">{locale === "es" ? "Selecciona una variante…" : "Select a variant…"}</option>{variants.map((variant)=><option key={variant.id} value={variant.id}>{variant.names[locale]??variant.names.en??variant.id}</option>)}</select></label>}<div className="modal-actions"><button onClick={closeCreate}>{locale === "es" ? "Cancelar" : "Cancel"}</button><button className="primary" disabled={!bandId || (variants.length > 0 && !variantId)} data-disabled-reason={!bandId ? (locale === "es" ? "Selecciona una lista de banda." : "Select a warband list.") : variants.length > 0 && !variantId ? (locale === "es" ? "Selecciona una variante de banda." : "Select a warband variant.") : undefined} onClick={() => void create()}>{locale === "es" ? "Crear" : "Create"}</button></div></section></div>}
    {showLibrary && <div className="modal-backdrop" role="presentation"><section className="modal campaign-library" role="dialog" aria-modal="true" aria-labelledby="campaign-library-title"><button autoFocus className="close" aria-label={t.close} onClick={closeLibrary}>×</button><h2 id="campaign-library-title">{locale === "es" ? "Biblioteca de Campañas" : "Campaign Library"}</h2><p>{t.sessionHelp}</p>{sessions.length ? <SessionCards /> : <p>{t.empty}</p>}<div className="library-footer"><button onClick={() => fileRef.current?.click()} disabled={!knowledge} data-disabled-reason={!knowledge ? (locale === "es" ? "Espera a que termine de cargar la base de conocimiento." : "Wait for the knowledge base to finish loading.") : undefined}>{locale === "es" ? "Explorar…" : "Browse…"}</button><button onClick={() => { closeLibrary(); setShowCreate(true); }}>{t.newCampaign}</button></div></section></div>}
    {pendingRemove && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="discard-session-title"><h2 id="discard-session-title">{locale === "es" ? "Cambios Sin Exportar" : "Unexported Changes"}</h2><p>{locale === "es" ? "Esta campaña tiene cambios. Puedes exportarlos antes de retirarla de la sesión." : "This campaign has changes. You can export them before removing it from the session."}</p><div className="modal-actions"><button className="primary" onClick={() => void (async () => { const session=sessions.find((item) => item.id===pendingRemove); if(session && await exportSession(session)) removeSession(pendingRemove); })()}>{locale === "es" ? "Exportar y retirar" : "Export and remove"}</button><button onClick={() => removeSession(pendingRemove)}>{locale === "es" ? "Descartar" : "Discard"}</button><button onClick={() => setPendingRemove(null)}>{locale === "es" ? "Cancelar" : "Cancel"}</button></div></section></div>}
  </div>;

  function removeSession(id: string) { const remaining=sessions.filter((item) => item.id!==id); setSessions(remaining); if(activeId===id) { setActiveId(remaining.at(-1)?.id??null); setPage("campaign"); } setPendingRemove(null); }
  function SessionCards() { return <div className="session-grid">{sessions.map((session) => { const doc=session.service.current()!; return <article key={session.id} className={session.id===activeId ? "session-card active" : "session-card"}><div className="session-summary"><span>{session.service.isDirty() ? t.unsaved : session.source === "created" ? t.created : session.source}</span><strong>{doc.campaign.identity.campaign_name}</strong><small><span>{doc.campaign.identity.warband_name}</span> · {knowledgeName(knowledge ?? undefined, "band", doc.campaign.identity.band_id, locale, doc.campaign.identity.warband_type)} · {(doc.campaign.battles ?? []).length} {locale === "es" ? "batallas" : "battles"}</small></div>{renameId===session.id ? <form className="inline-form" onSubmit={(event) => { event.preventDefault(); void withOperationProgress(() => session.service.run("renameCampaign", { name: renameValue })).then((result) => { if (!result.ok) { setOperationError(result.message); return; } setRenameId(null); setRenameValue(""); }).catch((error: unknown) => setOperationError(error instanceof Error ? error.message : String(error))); }}><input aria-label={t.campaignName} value={renameValue} onChange={(event) => setRenameValue(event.target.value)} /><button disabled={!renameValue.trim()} data-disabled-reason={!renameValue.trim() ? (locale === "es" ? "Introduce un nombre para la campaña." : "Enter a campaign name.") : undefined}>OK</button></form> : <div className="session-actions"><button className="primary" onClick={() => { setActiveId(session.id); setPage("campaign"); setShowLibrary(false); }}>{t.open}</button><button onClick={() => { setRenameId(session.id); setRenameValue(doc.campaign.identity.campaign_name); }}>{locale === "es" ? "Renombrar" : "Rename"}</button><button onClick={() => session.service.isDirty() ? setPendingRemove(session.id) : removeSession(session.id)}>{t.remove}</button></div>}</article>; })}</div>; }
}
