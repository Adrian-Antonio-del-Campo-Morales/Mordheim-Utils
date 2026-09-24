import { translate, uiMessageForText, type UiMessage } from "./features/campaign/i18n-core";
import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import type { CampaignAppService } from "./features/campaign/types";
import { CampaignAppProvider, localizeErrorMessage } from "./features/campaign/useCampaignApp";
import { OperationProgress } from "./features/common/OperationProgress";
import { withOperationProgress } from "./features/common/operationProgressEvents";
import { createService, loadKnowledge } from "./features/campaign/default-deps";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { catalogueLabel } from "@app/rules/catalogue-text";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { knowledgeName, variantName } from "./features/campaign/displayText";
import { presentationOutput } from "./features/campaign/presentation-output";
import { campaignPersonalName, warbandPersonalName, textJoin, textNumber, textSymbol } from "./features/campaign/presentation-values";
import { I18nProvider, type Locale } from "./features/campaign/i18n";
import { warbandVariants } from "@domain/campaign/band-variants";

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

function bandSetLabel(set: BandSet, locale: Locale) {
  return translate({ key: set === "trollheim" ? "shell.band-set-trollheim" : set === "core" ? "ui.706f7722a9f9" : set === "1a" ? "shell.band-set-1a" : set === "1b" ? "shell.band-set-1b" : "shell.band-set-1c" }, locale);
}

const copy = {
  es: { home: translate({ key: "ui.25bc89b63ee9" }, "es"), campaign: translate({ key: "ui.13624dd6f3e9" }, "es"), library: translate({ key: "ui.9c5b3b83b2a3" }, "es"), rules: translate({ key: "ui.bf1282ddb578" }, "es"), settings: translate({ key: "ui.2df28c1f8cad" }, "es"), newCampaign: translate({ key: "ui.d325957ad08f" }, "es"), newWarband: translate({ key: "ui.083ba81a5d68" }, "es"), load: translate({ key: "ui.13ee8d2a16d3" }, "es"), save: translate({ key: "ui.373cebbe9dba" }, "es"), undo: translate({ key: "ui.d9c1a97cb7b4" }, "es"), pdf: translate({ key: "ui.4a2705e83df4" }, "es"), welcome: translate({ key: "ui.dce22bdd39e0" }, "es"), empty: translate({ key: "ui.b71786907662" }, "es"), bandCategoriesHint: translate({ key: "ui.437ab4903693" }, "es"), sessions: translate({ key: "ui.8b7fc0a559ca" }, "es"), kbFail: translate({ key: "ui.3d733bbc4609" }, "es"), retry: translate({ key: "ui.4f33f62c367f" }, "es"), campaignName: translate({ key: "ui.dc16c1d56cf1" }, "es"), warbandName: translate({ key: "ui.007d0333e929" }, "es"), band: translate({ key: "ui.cd959a776d5d" }, "es"), create: translate({ key: "ui.e8da0940668b" }, "es"), open: translate({ key: "ui.142a02b2308b" }, "es"), remove: translate({ key: "ui.d985a24dd184" }, "es"), unsaved: translate({ key: "ui.702ac59cfa98" }, "es"), language: translate({ key: "ui.c74e31108a77" }, "es"), sessionHelp: translate({ key: "ui.6874b1ed5b90" }, "es"), search: translate({ key: "ui.a608c2f61aa0" }, "es"), noRules: translate({ key: "ui.59a2ff361cea" }, "es"), close: translate({ key: "ui.b61e7685256c" }, "es"), dismiss: translate({ key: "ui.fbcd944d8abb" }, "es"), created: translate({ key: "ui.f86a90df203e" }, "es"), exportEmpty: translate({ key: "ui.e642b741e547" }, "es"), primaryNav: translate({ key: "ui.e9621df7eb16" }, "es") },
  en: { home: translate({ key: "ui.25bc89b63ee9" }, "en"), campaign: translate({ key: "ui.13624dd6f3e9" }, "en"), library: translate({ key: "ui.9c5b3b83b2a3" }, "en"), rules: translate({ key: "ui.bf1282ddb578" }, "en"), settings: translate({ key: "ui.2df28c1f8cad" }, "en"), newCampaign: translate({ key: "ui.d325957ad08f" }, "en"), newWarband: translate({ key: "ui.083ba81a5d68" }, "en"), load: translate({ key: "ui.13ee8d2a16d3" }, "en"), save: translate({ key: "ui.373cebbe9dba" }, "en"), undo: translate({ key: "ui.d9c1a97cb7b4" }, "en"), pdf: translate({ key: "ui.4a2705e83df4" }, "en"), welcome: translate({ key: "ui.dce22bdd39e0" }, "en"), empty: translate({ key: "ui.b71786907662" }, "en"), bandCategoriesHint: translate({ key: "ui.437ab4903693" }, "en"), sessions: translate({ key: "ui.8b7fc0a559ca" }, "en"), kbFail: translate({ key: "ui.3d733bbc4609" }, "en"), retry: translate({ key: "ui.4f33f62c367f" }, "en"), campaignName: translate({ key: "ui.dc16c1d56cf1" }, "en"), warbandName: translate({ key: "ui.007d0333e929" }, "en"), band: translate({ key: "ui.cd959a776d5d" }, "en"), create: translate({ key: "ui.e8da0940668b" }, "en"), open: translate({ key: "ui.142a02b2308b" }, "en"), remove: translate({ key: "ui.d985a24dd184" }, "en"), unsaved: translate({ key: "ui.702ac59cfa98" }, "en"), language: translate({ key: "ui.c74e31108a77" }, "en"), sessionHelp: translate({ key: "ui.6874b1ed5b90" }, "en"), search: translate({ key: "ui.a608c2f61aa0" }, "en"), noRules: translate({ key: "ui.59a2ff361cea" }, "en"), close: translate({ key: "ui.b61e7685256c" }, "en"), dismiss: translate({ key: "ui.fbcd944d8abb" }, "en"), created: translate({ key: "ui.f86a90df203e" }, "en"), exportEmpty: translate({ key: "ui.e642b741e547" }, "en"), primaryNav: translate({ key: "ui.e9621df7eb16" }, "en") },
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
        .map((lore) => ({ id: String(lore.id), name: knowledge.recordText(lore, "name", locale), rows: rows.filter((row) => row.lore_id === lore.id) }))
        .filter((group) => group.rows.length)
        .sort((a, b) => a.name.localeCompare(b.name, locale, { sensitivity: "base" }))
    : kind === "band-rules" && !query.trim()
      ? knowledge.list("band")
          .map((band) => ({ id: String(band.id), name: knowledge.recordText(band, "name", locale), rows: rows.filter((row) => row.band_id === band.id) }))
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
  const categoryIds: readonly RuleCategory[] = ["special-rules", "band-rules", "conditions", "core-rules", "skills", "equipment", "spells", "scenarios", "injuries"];
  const categories = categoryIds.map((id) => [id, catalogueLabel(id, locale)] as const);
  return <section className={`page rules-page ${selected ? "show-rule-detail" : "show-rule-list"}`}><div className="page-title"><h1>{presentationOutput(copy[locale].rules)}</h1><span>{presentationOutput(translate({ key: "ui.1e2bcd33f1d8" }, locale))}</span></div>
    <div className="rules-toolbar"><div className="tabs">{categories.map(([value,label]) => <button className={kind === value ? "active" : ""} onClick={() => { setKind(value); setSelected(null); setQuery(""); resultRef.current = null; }} key={value}>{presentationOutput(label)}</button>)}</div><input aria-label={presentationOutput(copy[locale].search)} placeholder={presentationOutput(copy[locale].search)} value={query} onChange={(e) => { setQuery(e.target.value); setSelected(null); resultRef.current = null; }} /></div>
    <div className="rules-layout"><div className="rule-list">{ruleGroups.length ? ruleGroups.map((group) => kind === "band-rules" || kind === "spells" ? <details className="rule-group collapsible" key={group.id}><summary>{presentationOutput(group.name)}</summary>{group.rows.map((row) => <button className={row===selectedRow ? "active" : ""} onClick={(event) => openRule(`${row.category_id}:${row.entry_id}`, event.currentTarget)} key={row.entry_id}><span>{presentationOutput(row.name)}</span></button>)}</details> : <section className="rule-group" aria-labelledby={`rule-group-${group.id}`} key={group.id}><h3 id={`rule-group-${group.id}`}>{presentationOutput(group.name)}</h3>{group.rows.map((row) => <button className={row===selectedRow ? "active" : ""} onClick={(event) => openRule(`${row.category_id}:${row.entry_id}`, event.currentTarget)} key={row.entry_id}><span>{presentationOutput(row.name)}</span></button>)}</section>) : rows.map((row) => <button className={row===selectedRow ? "active" : ""} onClick={(event) => openRule(`${row.category_id}:${row.entry_id}`, event.currentTarget)} key={`${row.category_id}:${row.entry_id}`}><span>{presentationOutput(row.name)}</span>{query.trim() && <small>{presentationOutput(categories.find(([id]) => id === row.category_id)?.[1] ?? translate({ key: "knowledge.unavailable" }, locale))}</small>}</button>)}{rows.length===0 && <p>{presentationOutput(copy[locale].noRules)}</p>}</div>
    <article className="rule-detail" ref={ruleDetailRef} tabIndex={-1}>{selectedRow && <><button className="rule-back" onClick={() => setSelected(null)}>{presentationOutput(translate({ key: "ui.583cd20e817c" }, locale))}</button><h2>{presentationOutput(selectedRow.name)}</h2><p className="rule-prose">{presentationOutput(selectedRow.effect)}</p>{selectedRow.tags.length > 0 && <div className="rule-tags">{selectedRow.tags.map((tag) => <span key={String(tag)}>{presentationOutput(tag)}</span>)}</div>}{selectedRow.source_refs.length > 0 && <><h3>{presentationOutput(translate({ key: "ui.0f00c972abf5" }, locale))}</h3><ul>{selectedRow.source_refs.map((source, index) => { const row=source as Record<string, unknown>; const label=textJoin([translate({ key: "ui.0f00c972abf5" }, locale), textNumber(index + 1, locale)]); const url=typeof row.url === "string" ? row.url : null; return <li key={`${label}:${index}`}>{url ? <a href={url} target="_blank" rel="noreferrer">{presentationOutput(label)}</a> : presentationOutput(label)}</li>; })}</ul></>}{links.length > 0 && <><h3>{presentationOutput(translate({ key: "ui.f8ac335d7a31" }, locale))}</h3><ul>{links.map((link) => <li key={`${link.band}:${link.profile_id}:${link.relation}`}>{presentationOutput(link.band)} {presentationOutput(textSymbol("·"))} {presentationOutput(link.profile)} {presentationOutput(textSymbol("("))}{presentationOutput(link.relation)}{presentationOutput(textSymbol(")"))}</li>)}</ul></>}</>}</article></div></section>;
}

export function ProductApp() {
  const [locale, setLocale] = useState<Locale>("es");
  const t = copy[locale];
  const [page, setPage] = useState<Page>("campaign");
  const [knowledge, setKnowledge] = useState<ArtefactKnowledgeReader | null>(null);
  const [kbError, setKbError] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [disabledMessage, setDisabledMessage] = useState<UiMessage | null>(null);
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
    .sort((a, b) => knowledge!.recordText(a, "name", locale).localeCompare(knowledge!.recordText(b, "name", locale), locale)), [knowledge, locale, enabledBandSets]);
  useEffect(() => { if (!bands.some((row) => String(row.id) === bandId)) setBandId(bands[0] ? String(bands[0].id) : ""); }, [bands, bandId]);
  const variants = useMemo(() => knowledge && bandId ? warbandVariants(knowledge, bandId) : [], [knowledge, bandId]);
  useEffect(() => { setVariantId(""); }, [bandId]);
  const toggleBandSet = (set: BandSet) => setEnabledBandSets((current) => {
    const next = new Set(current);
    if (next.has(set)) next.delete(set); else next.add(set);
    return next;
  });

  const addSession = (service: CampaignAppService, source: string) => { const id = crypto.randomUUID(); setSessions((all) => [...all, { id, service, source }]); setActiveId(id); setPage("campaign"); };
  const create = async () => { if (!knowledge) return; const band=bands.find((row)=>String(row.id)===bandId); if(!band)return; await withOperationProgress(async () => { try { const service=createService(knowledge); const result=await service.createCampaign({ band_id: bandId, campaign_name: campaignName.trim() || (translate({ key: "ui.f0efa10d6f50" }, locale)), warband_name: knowledge.recordText(band, "name", locale), ...(variantId ? { variant: variantId } : {}) }); if (result.ok) { addSession(service, "created"); setShowCreate(false); setCampaignName(""); setVariantId(""); } else setOperationError(result.message); } catch(error) { setOperationError(error instanceof Error ? error.message : String(error)); } }); };
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

  return <I18nProvider locale={locale}><div className="app-shell" onPointerDownCapture={(event) => { const control=(event.target as Element).closest<HTMLElement>("button:disabled, input:disabled, select:disabled, [aria-disabled=true]"); if(control)setDisabledMessage(uiMessageForText(control.dataset.disabledReason) ?? { key: "error.action-failed" }); }}>
    <OperationProgress locale={locale} />
    <header className="topbar"><button className="brand" onClick={() => setPage("campaign")}><strong>{presentationOutput(translate({ key: "ui.d8dd5b3c8140" }, locale))}</strong><span>{presentationOutput(translate({ key: "ui.d2d821b8db1a" }, locale))}</span></button>
      <div className="mobile-context" aria-live="polite" aria-label={presentationOutput(textJoin([active?.service.current() ? campaignPersonalName(active.service.current()!.campaign, locale) : translate({ key: "shell.mordheim" }, locale), active?.service.isDirty() ? t.unsaved : active ? translate({ key: "ui.7111850c4aeb" }, locale) : t.empty], " · "))} data-title={presentationOutput(active?.service.current() ? campaignPersonalName(active.service.current()!.campaign, locale) : translate({ key: "shell.mordheim" }, locale))} data-status={presentationOutput(active?.service.isDirty() ? t.unsaved : active ? translate({ key: "ui.7111850c4aeb" }, locale) : t.empty)} />
      <nav aria-label={presentationOutput(t.primaryNav)}>{(["campaign","rules","settings"] as const).map((key,index) => <button key={key} className={page===key || (key==="campaign"&&page==="statistics") ? "active" : ""} onClick={() => setPage(key)}><span aria-hidden="true">{presentationOutput(textSymbol(index === 0 ? "◆" : index === 1 ? "☰" : "⚙"))}</span>{presentationOutput(t[key])}</button>)}</nav>
      <div className="actions"><button ref={createButtonRef} onClick={() => setShowCreate(true)} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}><span aria-hidden="true">{presentationOutput(textSymbol("＋"))}</span>{presentationOutput(t.newCampaign)}</button><button ref={libraryButtonRef} onClick={() => setShowLibrary(true)}><span aria-hidden="true">{presentationOutput(textSymbol("▣"))}</span>{presentationOutput(translate({ key: "ui.14acc4b06843" }, locale))}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}><span aria-hidden="true">{presentationOutput(textSymbol("↥"))}</span>{presentationOutput(t.load)}</button><button onClick={exportActive} disabled={!active} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.234ef5180a" }, locale)) : undefined}><span aria-hidden="true">{presentationOutput(textSymbol("↓"))}</span>{presentationOutput(translate({ key: "ui.a4e236e5f40f" }, locale))}</button><button onClick={undo} disabled={!active?.service.canUndo()} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.a0b1cad4df" }, locale)) : !active.service.canUndo() ? presentationOutput(translate({ key: "disabled.02baa9ca1c" }, locale)) : undefined}><span aria-hidden="true">{presentationOutput(textSymbol("↶"))}</span>{presentationOutput(t.undo)}</button><button onClick={() => void exportPdf()} disabled={!active} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.4e787caac0" }, locale)) : undefined}><span aria-hidden="true">{presentationOutput(textSymbol("▤"))}</span>{presentationOutput(t.pdf)}</button></div>
      <input hidden aria-label={presentationOutput(translate({ key: "ui.a2032dcbe79e" }, locale))} ref={fileRef} type="file" multiple accept=".mordheim,application/json" onChange={(e) => { const files=[...(e.target.files??[])]; if(files.length) void importFiles(files); e.target.value=""; }} />
    </header>
    {kbError && <output className="global-error" role="alert">{presentationOutput(t.kbFail)} <button onClick={loadKb}>{presentationOutput(t.retry)}</button></output>}
    {disabledMessage && <output className="global-error" role="alert">{presentationOutput(translate(disabledMessage, locale))} <button onClick={() => setDisabledMessage(null)}>{presentationOutput(t.dismiss)}</button></output>}
    {operationError && <output className="global-error" role="alert">{presentationOutput(localizeErrorMessage(operationError, locale, (id) => knowledgeName(knowledge ?? undefined, "profile", id, locale)))} <button onClick={() => setOperationError(null)}>{presentationOutput(t.dismiss)}</button></output>}
    <main>
      {page==="campaign" && active && <CampaignAppProvider service={active.service} locale={locale} profileName={(id) => knowledgeName(knowledge ?? undefined, "profile", id, locale)}><Suspense fallback={null}><CampaignSlice knowledge={knowledge ?? undefined} locale={locale} /></Suspense></CampaignAppProvider>}
      {page==="campaign" && !active && <section className="empty-workspace"><h1>{presentationOutput(t.campaign)}</h1><p>{presentationOutput(t.empty)}</p><p>{presentationOutput(t.bandCategoriesHint)}</p><div><button className="primary" onClick={() => setShowCreate(true)} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}>{presentationOutput(t.newCampaign)}</button><button onClick={() => fileRef.current?.click()} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}>{presentationOutput(t.load)}</button></div></section>}
      {page==="campaign" && active && <button className="statistics-link" onClick={() => setPage("statistics")}>{presentationOutput(translate({ key: "ui.980e0b2b3439" }, locale))}</button>}
      {page==="statistics" && active?.service.current() && <Suspense fallback={null}><CampaignStatistics document={active.service.current()!} locale={locale} /></Suspense>}
      {page==="rules" && knowledge && <RulesPage knowledge={knowledge} locale={locale} />}
      {page==="settings" && <section className="page"><div className="page-title"><h1>{presentationOutput(t.settings)}</h1><span>{presentationOutput(translate({ key: "ui.05464f7ff4f2" }, locale))}</span></div><div className="settings-card"><label><span>{presentationOutput(t.language)}</span><select value={locale} onChange={(e) => setLocale(e.target.value as Locale)}><option value="es">{presentationOutput(translate({ key: "shell.language-es" }, locale))}</option><option value="en">{presentationOutput(translate({ key: "shell.language-en" }, locale))}</option></select></label><fieldset className="band-set-picker"><legend>{presentationOutput(translate({ key: "ui.42caf13d9870" }, locale))}</legend>{BAND_SETS.map((set) => <label key={set}><input type="checkbox" checked={enabledBandSets.has(set)} onChange={() => toggleBandSet(set)} /><span>{presentationOutput(bandSetLabel(set, locale))}</span></label>)}</fieldset><p>{presentationOutput(translate({ key: "ui.41e3cc2b218c" }, locale))}</p><div><span>{presentationOutput(translate({ key: "ui.1b3f05e763e0" }, locale))}</span><strong>{presentationOutput(translate({ key: "ui.d4fd9c530e89" }, locale))}</strong></div><p>{presentationOutput(t.sessionHelp)}</p></div></section>}
    </main>
    <nav className="mobile-nav" aria-label={presentationOutput(translate({ key: "ui.ef08f2dd2211" }, locale))}>{(["campaign","rules","settings"] as const).map((key,index) => <button aria-current={page === key || (key === "campaign" && page === "statistics") ? "page" : undefined} aria-label={presentationOutput(textJoin([t[key], translate({ key: "ui.c96644056635" }, locale)], " · "))} key={key} className={page===key || (key==="campaign"&&page==="statistics") ? "active" : ""} onClick={() => { setPage(key); setShowMore(false); }}><span aria-hidden="true">{presentationOutput(textSymbol(index === 0 ? "◆" : index === 1 ? "☰" : "⚙"))}</span>{presentationOutput(t[key])}</button>)}<button aria-label={presentationOutput(translate({ key: "ui.dd92209d34de" }, locale))} aria-expanded={showMore} aria-controls="mobile-more-menu" onClick={() => setShowMore((value) => !value)}><span aria-hidden="true">{presentationOutput(textSymbol("•••"))}</span>{presentationOutput(translate({ key: "ui.cb53dee52de4" }, locale))}</button></nav>
    {showMore && <div className="mobile-more-backdrop" onClick={() => setShowMore(false)}><section id="mobile-more-menu" className="mobile-more" role="dialog" aria-modal="true" aria-label={presentationOutput(translate({ key: "ui.dd92209d34de" }, locale))} onClick={(event) => event.stopPropagation()}><header><strong>{presentationOutput(translate({ key: "ui.206f0ea6cc1a" }, locale))}</strong><button aria-label={presentationOutput(t.close)} onClick={() => setShowMore(false)}> {presentationOutput(textSymbol("×"))} </button></header><button onClick={() => { setShowMore(false); setShowCreate(true); }} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}>{presentationOutput(textSymbol("＋"))} {presentationOutput(t.newCampaign)}</button><button onClick={() => { setShowMore(false); setShowLibrary(true); }}>{presentationOutput(textSymbol("▣"))} {presentationOutput(translate({ key: "ui.14acc4b06843" }, locale))}</button><button onClick={() => { setShowMore(false); fileRef.current?.click(); }} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}>{presentationOutput(textSymbol("↥"))} {presentationOutput(t.load)}</button><button onClick={() => { setShowMore(false); void exportActive(); }} disabled={!active} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.234ef5180a" }, locale)) : undefined}>{presentationOutput(textSymbol("↓"))} {presentationOutput(translate({ key: "ui.a4e236e5f40f" }, locale))}</button><button onClick={() => { setShowMore(false); void undo(); }} disabled={!active?.service.canUndo()} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.a0b1cad4df" }, locale)) : !active.service.canUndo() ? presentationOutput(translate({ key: "disabled.02baa9ca1c" }, locale)) : undefined}>{presentationOutput(textSymbol("↶"))} {presentationOutput(t.undo)}</button><button onClick={() => { setShowMore(false); void exportPdf(); }} disabled={!active} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.4e787caac0" }, locale)) : undefined}>{presentationOutput(textSymbol("▤"))} {presentationOutput(t.pdf)}</button><button onClick={() => { setShowMore(false); setPage("statistics"); }} disabled={!active} data-disabled-reason={!active ? presentationOutput(translate({ key: "disabled.ebcc664743" }, locale)) : undefined}>{presentationOutput(textSymbol("▥"))} {presentationOutput(translate({ key: "ui.980e0b2b3439" }, locale))}</button></section></div>}
      {showCreate && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="new-title"><button className="close" aria-label={presentationOutput(t.close)} onClick={closeCreate}> {presentationOutput(textSymbol("×"))} </button><h2 id="new-title">{presentationOutput(translate({ key: "ui.8bbe966d26c9" }, locale))}</h2><p>{presentationOutput(translate({ key: "ui.560d3d09f337" }, locale))}</p><label>{presentationOutput(t.campaignName)}<input autoFocus placeholder={presentationOutput(translate({ key: "ui.f0efa10d6f50" }, locale))} value={campaignName} onChange={(e) => setCampaignName(e.target.value)} /></label><fieldset className="band-picker"><legend>{presentationOutput(t.band)}</legend>{bands.map((row) => { const set = bandSetFor(row); return <label key={String(row.id)}><input type="radio" name="band" value={String(row.id)} checked={bandId===String(row.id)} onChange={(e)=>setBandId(e.target.value)} /><span>{presentationOutput(knowledge!.recordText(row, "name", locale))}</span>{set && <small>{presentationOutput(bandSetLabel(set, locale))}</small>}</label>; })}</fieldset>{variants.length > 0 && <label>{presentationOutput(translate({ key: "ui.a6111107cc8c" }, locale))}<select value={variantId} onChange={(event)=>setVariantId(event.target.value)}><option value="">{presentationOutput(translate({ key: "ui.0333b61e34a6" }, locale))}</option>{variants.map((variant)=><option key={variant.id} value={variant.id}>{presentationOutput(variantName(knowledge ?? undefined, bandId, variant.id, locale))}</option>)}</select></label>}<div className="modal-actions"><button onClick={closeCreate}>{presentationOutput(translate({ key: "ui.45ac97c49aed" }, locale))}</button><button className="primary" disabled={!bandId || (variants.length > 0 && !variantId)} data-disabled-reason={!bandId ? presentationOutput(translate({ key: "disabled.f41ec72501" }, locale)) : variants.length > 0 && !variantId ? presentationOutput(translate({ key: "disabled.bed7f968f3" }, locale)) : undefined} onClick={() => void create()}>{presentationOutput(translate({ key: "ui.f4c21e1ded7f" }, locale))}</button></div></section></div>}
    {showLibrary && <div className="modal-backdrop" role="presentation"><section className="modal campaign-library" role="dialog" aria-modal="true" aria-labelledby="campaign-library-title"><button autoFocus className="close" aria-label={presentationOutput(t.close)} onClick={closeLibrary}> {presentationOutput(textSymbol("×"))} </button><h2 id="campaign-library-title">{presentationOutput(translate({ key: "ui.8523c3277600" }, locale))}</h2><p>{presentationOutput(t.sessionHelp)}</p>{sessions.length ? <SessionCards /> : <p>{presentationOutput(t.empty)}</p>}<div className="library-footer"><button onClick={() => fileRef.current?.click()} disabled={!knowledge} data-disabled-reason={!knowledge ? presentationOutput(translate({ key: "disabled.239bd32144" }, locale)) : undefined}>{presentationOutput(translate({ key: "ui.174585612f37" }, locale))}</button><button onClick={() => { closeLibrary(); setShowCreate(true); }}>{presentationOutput(t.newCampaign)}</button></div></section></div>}
    {pendingRemove && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="discard-session-title"><h2 id="discard-session-title">{presentationOutput(translate({ key: "ui.702ac59cfa98" }, locale))}</h2><p>{presentationOutput(translate({ key: "ui.e55c432e8c4f" }, locale))}</p><div className="modal-actions"><button className="primary" onClick={() => void (async () => { const session=sessions.find((item) => item.id===pendingRemove); if(session && await exportSession(session)) removeSession(pendingRemove); })()}>{presentationOutput(translate({ key: "ui.d181633917e4" }, locale))}</button><button onClick={() => removeSession(pendingRemove)}>{presentationOutput(translate({ key: "ui.161b3b7a9d0d" }, locale))}</button><button onClick={() => setPendingRemove(null)}>{presentationOutput(translate({ key: "ui.45ac97c49aed" }, locale))}</button></div></section></div>}
  </div></I18nProvider>;

  function removeSession(id: string) { const remaining=sessions.filter((item) => item.id!==id); setSessions(remaining); if(activeId===id) { setActiveId(remaining.at(-1)?.id??null); setPage("campaign"); } setPendingRemove(null); }
  function SessionCards() { return <div className="session-grid">{sessions.map((session) => { const doc=session.service.current()!; return <article key={session.id} className={session.id===activeId ? "session-card active" : "session-card"}><div className="session-summary"><span>{presentationOutput(session.service.isDirty() ? t.unsaved : session.source === "created" ? t.created : translate({ key: "shell.imported" }, locale))}</span><strong>{presentationOutput(campaignPersonalName(doc.campaign, locale))}</strong><small><span>{presentationOutput(warbandPersonalName(doc.campaign, locale))}</span> {presentationOutput(textSymbol("·"))} {presentationOutput(knowledgeName(knowledge ?? undefined, "band", doc.campaign.identity.band_id, locale))} {presentationOutput(textSymbol("·"))} {presentationOutput(textNumber((doc.campaign.battles ?? []).length, locale))} {presentationOutput(translate({ key: "ui.ae80271353ba" }, locale))}</small></div>{renameId===session.id ? <form className="inline-form" onSubmit={(event) => { event.preventDefault(); void withOperationProgress(() => session.service.run("renameCampaign", { name: renameValue })).then((result) => { if (!result.ok) { setOperationError(result.message); return; } setRenameId(null); setRenameValue(""); }).catch((error: unknown) => setOperationError(error instanceof Error ? error.message : String(error))); }}><input aria-label={presentationOutput(t.campaignName)} value={renameValue} onChange={(event) => setRenameValue(event.target.value)} /><button disabled={!renameValue.trim()} data-disabled-reason={!renameValue.trim() ? presentationOutput(translate({ key: "disabled.e9af446561" }, locale)) : undefined}>{presentationOutput(translate({ key: "shell.ok" }, locale))}</button></form> : <div className="session-actions"><button className="primary" onClick={() => { setActiveId(session.id); setPage("campaign"); setShowLibrary(false); }}>{presentationOutput(t.open)}</button><button onClick={() => { setRenameId(session.id); setRenameValue(doc.campaign.identity.campaign_name); }}>{presentationOutput(translate({ key: "ui.af7d7211e1f2" }, locale))}</button><button onClick={() => session.service.isDirty() ? setPendingRemove(session.id) : removeSession(session.id)}>{presentationOutput(t.remove)}</button></div>}</article>; })}</div>; }
}
