import { useLayoutEffect, useMemo, useRef, useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { WarbandReferences } from "@app/rules/warband-reference";
import { catalogueLabel } from "@app/rules/catalogue-text";
import type { Locale } from "../campaign/i18n";
import { bandCategoryKey, bandCategoryMessage } from "../campaign/band-categories";
import { translate } from "../campaign/i18n-core";
import { presentationOutput } from "../campaign/presentation-output";
import { WarbandReferenceTemplate } from "./WarbandReferenceTemplate";

export function WarbandsBrowser({ knowledge, locale, query }: { knowledge: ArtefactKnowledgeReader; locale: Locale; query: string }) {
  const references = useMemo(() => new WarbandReferences(knowledge), [knowledge]);
  const bands = useMemo(() => references.list(locale, query), [references, locale, query]);
  const [selection, setSelection] = useState<{ id: string; query: string } | null>(null);
  const explicitBand = selection?.query === query ? bands.find((band) => band.id === selection.id) : undefined;
  const selected = explicitBand ?? bands[0];
  const selectedId = selected?.id;
  const showingDetail = explicitBand !== undefined;
  const sheet = useMemo(() => selectedId ? references.sheet(selectedId, locale) : null, [references, selectedId, locale]);
  const articleRef = useRef<HTMLElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const originRef = useRef<HTMLButtonElement | null>(null);
  const scrollRef = useRef({ page: 0, list: 0 });
  const restoreRef = useRef(false);

  useLayoutEffect(() => {
    if (showingDetail && window.matchMedia?.("(max-width: 680px)").matches) {
      articleRef.current?.focus({ preventScroll: true });
      articleRef.current?.scrollIntoView?.({ block: "start" });
    } else if (restoreRef.current) {
      restoreRef.current = false;
      originRef.current?.focus({ preventScroll: true });
      if (listRef.current) listRef.current.scrollTop = scrollRef.current.list;
      window.scrollTo({ top: scrollRef.current.page });
    }
  }, [showingDetail, selected?.id]);

  return <div className={`rules-layout warband-browser ${showingDetail ? "show-band-detail" : "show-band-list"}`}>
    <div className="rule-list warband-list" ref={listRef} aria-label={presentationOutput(catalogueLabel("band-rules", locale))}>
      {bands.map((band) => <button key={band.id} className={band.id === selected?.id ? "active" : ""} aria-pressed={band.id === selected?.id} onClick={(event) => {
        originRef.current = event.currentTarget;
        scrollRef.current = { page: window.scrollY, list: listRef.current?.scrollTop ?? 0 };
        setSelection({ id: band.id, query });
      }}><span>{presentationOutput(band.name)}</span><small>{presentationOutput(translate(bandCategoryMessage(bandCategoryKey(band.row)), locale))}</small></button>)}
      {bands.length === 0 && <p className="warband-data-note">{presentationOutput(catalogueLabel("warband-empty", locale))}</p>}
    </div>
    {sheet && <article className="warband-detail" ref={articleRef} tabIndex={-1} aria-label={presentationOutput(sheet.name)}>
      <button className="warband-back" onClick={() => { restoreRef.current = true; setSelection(null); }}>{presentationOutput(catalogueLabel("warband-back", locale))}</button>
      <WarbandReferenceTemplate key={sheet.id} sheet={sheet} locale={locale} />
    </article>}
  </div>;
}
