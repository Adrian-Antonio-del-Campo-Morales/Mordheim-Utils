/**
 * T12 fase D — test/tool support: load the generated KB artefact completely.
 *
 * The published artefact (`outputs/web-public/knowledge/knowledge-web.json`)
 * carries only the initial document: bands, profiles, skills, mechanics, prose
 * and the presentation index. The campaign catalogue — the equipment rows and
 * the campaign sections — travels next to it as `knowledge-catalogue.json`,
 * addressed by `catalogue_url` + `catalogue_digest`, and the product fetches it
 * on demand through `ensureCatalogue("items" | "campaign")`.
 *
 * Suites and tools that legitimately need every family merge that fragment here,
 * from the same directory and through the same digest-addressed contract: one
 * artefact, owned by the generator, never a hand-edited copy. A directory that
 * still ships the pre-partition document (items and campaign inline, no
 * `catalogue_url`) is read exactly as it is, so both layouts are supported.
 */
import { existsSync, readFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

export interface ArtefactDocumentOptions {
  /**
   * Merge `rules-prose.json` under `rules_prose` (default `true`). It is a bare
   * stem → rows map, not a document fragment, and callers that sweep only the
   * artefact's own effect text (its own suites cover the prose) can leave it out.
   */
  readonly prose?: boolean;
  /** Merge the presentation index from `display-text.json` (default `true`). */
  readonly displayText?: boolean;
}

/**
 * The initial document plus every fragment it references, merged in memory.
 *
 * `catalogue_url` is the only fragment Fase D moved out of the document: it was
 * inline at HEAD and now travels deferred. `display_text_url` and
 * `rules_prose_url` have always been separate URL-addressed artifacts; they are
 * merged here for callers that need the whole knowledge base, and can be left
 * out by callers that only sweep the document's own families.
 */
export function readArtefactDocument(
  path: string,
  options: ArtefactDocumentOptions = {},
): Record<string, unknown> {
  const { prose: includeProse = true, displayText: includeDisplayText = true } = options;
  const directory = dirname(path);
  const read = (file: string): Record<string, unknown> =>
    JSON.parse(readFileSync(resolve(directory, file), "utf-8")) as Record<string, unknown>;
  const fragment = (reference: unknown): Record<string, unknown> =>
    typeof reference === "string" && existsSync(resolve(directory, reference)) ? read(reference) : {};
  const document = read(basename(path));
  const prose = includeProse ? fragment(document.rules_prose_url) : {};
  return {
    ...document,
    ...(includeDisplayText ? fragment(document.display_text_url) : {}),
    ...fragment(document.catalogue_url),
    ...(Object.keys(prose).length ? { rules_prose: prose } : {}),
  };
}

/** Reader over the complete artefact: every family loaded, no deferred read. */
export function readArtefactReader(path: string): ArtefactKnowledgeReader {
  return ArtefactKnowledgeReader.from(readArtefactDocument(path));
}

/** The first existing path of a candidate list, or `null` (suite skips). */
export function firstExistingPath(candidates: readonly string[]): string | null {
  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}
