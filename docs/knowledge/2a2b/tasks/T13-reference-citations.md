# T13 — F050 localized racial-maximum reference citations

Execution delivery for the lot reserved as **F050 — localized reference
citations** in the [initiative checklist](../README.md) and for the registered
finding
[T13-F050](T13-execution-follow-ups.md#t13-f050--human-racial-maximum-reference-leaks-into-the-enes-reference-sheet)
(the canonical `(campaign.limit.racial-maximum.human)` reference F042 added to
the Sisters of Sigmar rule `band--human-maximum-characteristics` is published,
but the EN/ES reference sheet renders the catalogue id instead of the linked
meaning).

This is a **consumer-side presentation defect**, not a publication defect: the
generator check is current, the canonical citation is preserved, and the repair
resolves the citation into readable EN/ES text at the maintained read-model
seam. The executor **does not accept or close anything**: F050 keeps its status,
T15 keeps its status, no shared document (README, plans, follow-up register) was
edited, and no commit or push was made.

## 1. Problem and required outcome

The published band-rule prose keeps the canonical reference verbatim:

> Sisters of Sigmar are Humans and use the Human racial maximum profile
> (campaign.limit.racial-maximum.human).

The reference sheet projected that sentence literally in both locales, so a
reader saw a catalogue id. The required outcome is **legible, localized
resolution from published data and maintained mechanisms**, preserving the
canonical reference and the rule meaning. Deleting the token, wordizing the id,
hiding the text or weakening the regression assertion are explicitly not
acceptable; it is not enough to prove that `campaign.limit.` disappears — the
correct text that replaces it must be stated and asserted.

The resolved sentence is now, exactly:

| Locale | Rendered `p.rule-prose` |
| --- | --- |
| EN | `Sisters of Sigmar are Humans and use the Human racial maximum profile (M 4, WS 6, BS 6, S 4, T 4, W 3, I 6, A 4, Ld 9).` |
| ES | `Las Hermanas de Sigmar son Humanas y usan el perfil máximo racial humano (M 10, HA 6, HP 6, F 4, R 4, H 3, I 6, A 4, L 9).` |

## 2. Entry state, reservation and evidence

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, unchanged at
  closing. The shared tree carried 240 dirty entries at entry (249 at closing);
  every one of them belongs to another lot.
- Entry snapshot: `build/cache/t13-parallel/reference-citations/entry/`
  (`head.txt`, `git-status.txt`, `hashes.txt`, and byte copies of every file the
  lot touches). The five recorded entry hashes were re-verified at closing and
  still match their copies — no entry copy was overwritten:

  | File | Entry SHA-256 |
  | --- | --- |
  | `packages/typescript/application/rules/rules-catalogue.ts` | `221639f4…` |
  | `packages/typescript/application/rules/catalogue-text.ts` | `d159e20f…` |
  | `packages/typescript/application/rules/warband-reference.ts` | `2ffa2115…` |
  | `tests/typescript/application/rules/warband-reference.test.ts` | `d7591c2c…` |
  | `tests/web/warband-reference-template.test.tsx` | `516c93a6…` |

- Reservation respected: only the owned paths were edited; canonical/staged
  sources, schemas, specifications/pins, the Python auditor (F051), eligibility,
  engines, the generator and its outputs, `src/` components/layouts and the
  shared documents were read-only. The untracked T13.2 hirelings/commands
  artifacts already on disk were not touched.

## 3. Trace: source → publication → reader → projection → render

| Layer | Entity | Observation |
| --- | --- | --- |
| Source | `sources/knowledge/bands/mordheim/*/special-rules.yaml` | Every `campaign.limit.*` reference in the corpus is of the `campaign.limit.racial-maximum.*` family; no other `campaign.limit.*` family exists. |
| Publication | `tools/knowledge/generate_knowledge_web.py` → `outputs/web-public/knowledge/` | `knowledge-web.json` (bands/profiles/skills and the prose URLs plus `catalogue_url: knowledge-catalogue.json`), `rules-prose.json`, `display-text.json`, `knowledge-catalogue.json`. The citation is published verbatim in `rules-prose.json`; the linked profiles are published under `campaign.racial_maximums`. |
| Reader/localization | `adapters/knowledge-reader/index.ts`, `presentation.ts` | `ArtefactKnowledgeReader.recordText(row, field, locale)` binds prose rows to presentation entries and returns `ResolvedKbText`; the reader does not interpret ids, so the citation resolved as raw text — this is where the leak was possible. |
| Projection | `application/rules/rules-catalogue.ts`, `warband-reference.ts` | `RulesCatalogue.localizedEffect` produced the rule `effect`; `RulesCatalogue.entries("band-rules", …)` and `WarbandReferences.sheet` project those entries into the sheet. |
| Render | `src/features/rules/WarbandReferenceTemplate.tsx` (`p.rule-prose`), `ProductApp.tsx` RulesPage | Both consumers print `entry.effect` unchanged, so the fix belongs upstream of the component. |

## 4. Scope decision: what the resolver interprets

Only the citation form the canonical corpus writes is interpreted: a
parenthesised `(campaign.limit.racial-maximum.<key>)` id. Measurements over the
current publication (`build/cache/t13-parallel/reference-citations/citation-coverage.txt`):

- 99 citation occurrences in published prose, 19 distinct ids, every one of them
  present in the 30 `campaign.racial_maximums` rows, and every row publishing all
  nine numeric characteristics.
- Zero occurrences of any other `campaign.limit.*` family.

This is deliberately **not** a general reference interpreter. Other families,
other prose conventions and non-parenthesised mentions keep their published
form; if a real source ever adds one, the presentation gate's technical-id
detector is the backstop (§12, §14).

## 5. Layer decision

The resolution is composed in the **rules read model**, at
`RulesCatalogue.localizedEffect`, using the catalogue's existing text vocabulary
and brand (`CatalogueText` in `application/rules/catalogue-text.ts`). Rationale:

- `localizedEffect` is the single place where published prose becomes an entry
  `effect`, and it already resolves distances (`adaptDistanceText`); the citation
  is the same kind of resolution from published data.
- Consumers (`RulesPage`, `WarbandReferences.sheet`) and the rendered component
  needed no change, and no Web component or layout was touched.
- `application/rules/warband-reference.ts` needed no change: it consumes
  `catalogue.entries`, so it inherits the resolved text. No edit was made to it.
- The published artefact, the canonical sources and the reader seam
  (`adapters/knowledge-reader/**`) are unchanged, so nothing about the leak is
  hidden in the data.

## 6. Implementation

| File | Change |
| --- | --- |
| `packages/typescript/application/rules/reference-citations.ts` (new) | `resolveLimitCitations(text, publishedRacialMaximums, locale)`: probes for the citation prefix, reads the published rows lazily, builds the localized statline of each linked profile, and replaces every citation with `(<phrase>)`. Also owns the citation grammar (`CITATION_SOURCE`), the family prefix/probe constants and `maximumProfile`. |
| `packages/typescript/application/rules/catalogue-text.ts` | New label `racial-maximum-not-published`; `","`-style separator and `(`/`)` punctuation admitted by the existing vocabulary helpers; new `catalogueCitationText` (composes one resolved text with the catalogue phrases that replace its citations) and `catalogueCharacteristicKey` (localized characteristic abbreviations, `M/WS/BS/S/T/W/I/A/Ld` or `M/HA/HP/F/R/H/I/A/L`). |
| `packages/typescript/application/rules/rules-catalogue.ts` | `localizedEffect` now returns `resolveLimitCitations(...)` for resolved prose; lazy `publishedRacialMaximums()` cache reads `knowledge.list("racial_maximum")` once per catalogue instance. |
| `tests/typescript/application/rules/reference-citations.test.ts` (new, 10 tests) | Real artefact EN/ES plus synthetic controls (§10). |
| `tests/web/features/rules/reference-citations.test.tsx` (new, 5 tests) | Rendered regression over the real reader and the real template. |
| `tests/typescript/application/rules/warband-reference.test.ts` | The two failing bare `not.toContain("campaign.limit.")` assertions became positive: the localized sentence **and** the resolved human statline are asserted in each locale. |
| `tests/web/warband-reference-template.test.tsx` | Rendered assertion now pins the exact Sisters sentence including the statline, and the absence of `campaign.limit.`. |

Diffstat (tracked files): 4 files changed, 74 insertions, 5 deletions.

Two implementation details worth recording:

1. **No arbitrary-string branding.** The first draft sliced the resolved text
   and asserted `as ResolvedKbText` / `as CatalogueText`, which the deep GUI
   audit classified as `presentation-cast`/`presentation-type-forgery`
   (+5 review findings). The delivered version follows the maintained
   `adaptDistanceText` idiom already used in the same directory: the public
   contract returns branded text while the implementation signature stays plain
   `string`, so no assertion brands a caller-supplied string. `catalogueJoin`
   and the other pre-existing casts in `catalogue-text.ts` are untouched.
2. **Per-row completeness.** A row that does not publish all nine numeric
   characteristics is an explicit localized absence, never a partial statline
   that would bound a missing characteristic wrongly. A duplicated id is not one
   profile, so it too degrades to the absence label instead of an arbitrary pick
   (the maintained reader indexes this family by id, so the seam cannot currently
   produce it; the resolver contract is unit-tested directly).

## 7. Behavior contract

| Input state | Output |
| --- | --- |
| Known id, row publishes all nine numerics | `(<localized statline>)` in profile order (EN canonical keys; ES printed keys, M adapted with `adaptCharacteristicValue`) |
| Unknown id (no published row) | `(<localized absence label>)` |
| Row publishing an incomplete characteristic set | `(<localized absence label>)` |
| Id published twice (two rows) | `(<localized absence label>)` |
| Several citations in one text | Each replaced independently, in order |
| Same citation repeated | Every occurrence replaced |
| Text without a citation | Returned unchanged; the campaign catalogue is never read |
| Missing translation of the row | Untouched existing contract: the reader's localized unavailable notice; no English is substituted into ES and no id is shown |

## 8. Baseline reproduction (before the repair)

`npm run test --workspace campaign-web-core -- ../../tests/typescript/application/rules/warband-reference.test.ts`
— `1 failed (1)`, `2 failed | 6 passed (8)`, EXIT=1
(`build/cache/t13-parallel/reference-citations/baseline-warband-reference.txt`).
Both failures are the EN and ES raw-id assertions on the Sisters rule. Related
suites were already green: `rules-catalogue.test.ts` +
`equipment-access-contract.test.ts` = 18 passed
(`baseline-related-suites.txt`), rendered template = 5 passed
(`baseline-template.txt`).

## 9. Results (after the repair)

| Command | Result | Log |
| --- | --- | --- |
| `npm run test --workspace campaign-web-core -- ../../tests/typescript/application/rules/{reference-citations,warband-reference,rules-catalogue,equipment-access-contract}.test.ts` | 4 files, **36 passed**, EXIT=0 | `final-ts-suites.txt` |
| `npm run test --workspace warband-manager-web -- ../../tests/web/features/rules/reference-citations.test.tsx ../../tests/web/warband-reference-template.test.tsx` | 2 files, **10 passed**, EXIT=0 | `final-web-suites.txt` |
| `npm run typecheck --workspace campaign-web-core` | EXIT=0 | `typecheck-core-final.txt` |
| `npm run typecheck --workspace warband-manager-web` | EXIT=0 | `typecheck-web-final.txt` |
| `python -X utf8 tools/knowledge/generate_knowledge_web.py --check` | `check ok`, EXIT=0 | `generator-check-final.txt` |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q` | 1 passed, EXIT=0 | `pytest-documentation-final.txt` |
| `python tools/mordheim-utils.py check-presentation` | detectors 136/136; dynamic completeness 0 findings; static 775 inherited findings (see §12) | `presentation-gate-final.txt` |

Focused counts: `reference-citations.test.ts` 10, `warband-reference.test.ts` 8
(was 2 failing / 6 passing), `rules-catalogue.test.ts` 16,
`equipment-access-contract.test.ts` 2, rendered `reference-citations.test.tsx`
5, `warband-reference-template.test.tsx` 5.

The F044 notes/recipients cases are unaffected and exercised by the same suites:
`warband-reference.test.ts` includes the Underworld list-names, item references,
recipients and restrictions case in both locales, and
`equipment-access-contract.test.ts` stays green.

## 10. Negative controls

Application suite (`tests/typescript/application/rules/reference-citations.test.ts`):

- Real Sisters EN/ES: resolved sentence plus the exact statline, and no
  `campaign.limit.` in the entry.
- Every published citation of the real catalogue: ≥21 citing rows resolve through
  `RulesCatalogue`; every browsable category (>1000 entries) is free of raw ids
  **and** of the absence label, which no current citation needs.
- Multi-citation (Black Dwarfs: dwarf + bull centaur + human) and repeated
  citation (Restless Dead: Grave Guard twice) resolve each occurrence.
- Synthetic known / unknown / partial-row / duplicated-id / repeated / no-citation
  states.
- Prose without a citation under a **deferred** campaign catalogue still
  resolves, proving the resolver never makes band-rule reading depend on the
  campaign fragment.
- Missing translation: the reader's localized unavailable notice is kept in ES
  while EN still resolves — the state belongs to the row's translation, not to
  the resolver.
- Preservation: the published `rules-prose` row still carries
  `(campaign.limit.racial-maximum.human)` verbatim.

Rendered regression (`tests/web/features/rules/reference-citations.test.tsx`):
exact EN and ES Sisters sentence over the real reader and template,
multi-citation and repeated-citation sheets, and no `campaign.limit.` anywhere
in the rendered container — so the fix cannot later be "achieved" by deleting the
prose.

## 11. Preservation

- The canonical reference is intact in the sources (read-only here) and in the
  published artefact; the generator check reports the publication current.
- No generated artefact was edited by hand; no source, schema, pin or KB file was
  modified.
- `adapters/knowledge-reader/**` is unchanged, so the resolution is layered above
  the maintained reader rather than weakening it.
- The assertions that failed at baseline were **strengthened**, not relaxed: the
  two bare absence checks were replaced by positive content assertions plus the
  absence check.

## 12. Presentation gates

`python tools/mordheim-utils.py check-presentation` (`presentation-gate-final.txt`):

| Phase | Result |
| --- | --- |
| Detector self-tests (`node:test`) | **136 tests, 0 failed** |
| Static GUI text audit (`--strict --deep --check`) | **775 findings of 2267 sinks — FAIL (inherited)** |
| Dynamic visible-completeness audit | **0 findings** (`raw-text=0 technical-id=0 wrong-locale=0 generic-fallback=0 missing-presentation-entry=0 unexpected-row-in-category=0 unsupported-document-rendered=0`) |

Classification of the static failure: **inherited, not this lot's**. The
per-file finding set attributable to the lot's files is exactly the pre-existing
set recorded in the entry copies:

- `catalogue-text.ts`: the same six `presentation-type-forgery` expressions that
  the entry backup already produced (`catalogueLabel` fallback,
  `catalogueJoin`, two `catalogueNumber` branches, `catalogueCharacteristic`,
  `cataloguePunctuation`); the first draft's five additional review findings were
  removed by the restructuring in §6.
- `reference-citations.ts` and `rules-catalogue.ts`: **0 findings**.

The gate's exit code stays 1 because of the inherited static findings. No budget,
threshold or foreign expectation was changed to obtain green, and the dynamic
layer — the one that classifies visible leaks, including technical ids — is
green.

## 13. Browser verification

A real dev server was run (`npm run dev --workspace warband-manager-web --
--port 5199 --strictPort`, stopped afterwards) against the real publication:

| Locale | Flow | Result |
| --- | --- | --- |
| ES (app default) | Rules → Bandas → Hermanas de Sigmar → expand *Máximos de Características Humanos* | `Las Hermanas de Sigmar son Humanas y usan el perfil máximo racial humano (M 10, HA 6, HP 6, F 4, R 4, H 3, I 6, A 4, L 9).` — no `campaign.limit.`, no absence label |
| EN | Settings → Language → English → Rules → Warbands → Sisters of Sigmar → expand *Human Maximum Characteristics* | `Sisters of Sigmar are Humans and use the Human racial maximum profile (M 4, WS 6, BS 6, S 4, T 4, W 3, I 6, A 4, Ld 9).` — no `campaign.limit.`, no absence label |

Evidence: `build/cache/t13-parallel/reference-citations/browser-verification.txt`
(the extracted sentences), plus a captured screenshot of the EN sheet.

**Rendered test vs browser test.** The jsdom regressions pin the exact sentence
of both locales and cover multi- and repeated-citation sheets; the browser check
exercises the real product flow (locale switch, warband browser, `<details>`
expansion) against the real publication for the Sisters case only. The
multi/repeated cases therefore have rendered-test evidence, not browser evidence.

## 14. Limits and non-claims

- Only the parenthesised `campaign.limit.racial-maximum.<key>` citation form is
  interpreted; a differently written reference would still render literally.
  No such form exists in the current corpus.
- The resolved text is the **nine-characteristic maximum profile in profile
  order**, not the full profile card and not the band's own profile bonuses; it
  states the linked racial maximum, which is what the rule sentence refers to.
- ES Movement prints the maintained cm conversion (`4` → `10`) because the
  resolver reuses `adaptCharacteristicValue`; that convention is shared with
  every other profile characteristic in the product, but the maximum-profile
  wording itself was not re-checked against a printed ES source (§15 P3).
- The absence and duplicated-id branches are unreachable with the current
  publication (all 19 cited ids resolve, no duplicates); they are contract
  behaviour proven by synthetic controls.
- This lot does not accept F050 or T15, does not certify the whole EN/ES
  reference flow, does not resolve any other citation family and does not touch
  the static-audit inheritance described in §12.

## 15. Pending proposals

Proposals only; no entry was added to the shared register and no ID was assigned.
The coordinator assigns IDs and decides ownership.

### P1 — Non-parenthesised and foreign citation families render literally

- **Reproducer:** add a synthetic prose row whose effect cites
  `campaign.limit.racial-maximum.human` **without** parentheses (or cites any
  future `campaign.limit.<other-family>.*` id) and project it through
  `RulesCatalogue.entry`.
- **Impact:** the citation reaches the sheet as a technical id; today only the
  dynamic completeness detector would catch it, and no product test pins it.
- **Deferral reason:** no such form exists in sources (0 occurrences measured);
  inventing grammar for unpublished forms would build the general interpreter
  this lot explicitly avoids.
- **Owner:** coordinator; T15 reference/presentation owner as executor.
- **Resume:** before accepting any new source that introduces a citation form or
  a `campaign.limit.*` family.
- **Closure criterion:** a new form is either transcribed legibly in EN/ES with a
  regression over real data, or a deliberate decision records that it stays
  literal.

### P2 — Absence and duplicated-id branches have no real-data coverage

- **Reproducer:** publish (or simulate in a fixture copied from the artefact
  shape) a prose row citing an id that has no `campaign.racial_maximums` row, and
  one whose id appears twice.
- **Impact:** the visible fallback of a real broken or incoherent reference has
  only synthetic proof today.
- **Deferral reason:** the current publication resolves 19/19 cited ids and has no
  duplicate ids; canonical rows must not be invented for a witness.
- **Owner:** coordinator; KB/editorial owner for the fixture.
- **Resume:** with the first real absent or duplicated reference, or with the
  next publication review.
- **Closure criterion:** real-data evidence shows the explicit localized absence
  (never an id, never another locale, never a partial statline).

### P3 — ES Movement for maximum profiles was not checked against a printed source

- **Reproducer:** compare the rendered ES maximum statline (`M 10` for canonical
  `4`) with the printed Spanish profile convention for racial maximums.
- **Impact:** if the printed ES material expresses maximum profiles differently,
  the ES statline would be internally consistent but editorially wrong.
- **Deferral reason:** the conversion is the product's maintained convention for
  every profile characteristic and the lot must not invent new profile wording;
  the editorial check belongs to the profile/editorial pass.
- **Owner:** coordinator; KB/editorial owner.
- **Resume:** next profile-editorial pass, before any claim that the ES maximum
  wording is editorially certified.
- **Closure criterion:** a cited source or spec records the ES convention for
  maximum-profile statlines, and the resolver follows it.

### P4 — The catalogue module owns a brand the static gate still flags

- **Reproducer:** run `npm run audit:gui:deep` and read the six
  `presentation-type-forgery` findings in `application/rules/catalogue-text.ts`.
- **Impact:** the legitimate brand owner of catalogue text is indistinguishable
  from a forged cast in the report, so real regressions in that file are harder
  to see; F050 adds none, but the debt stays.
- **Deferral reason:** declaring an owned constructor for the module is a
  presentation-gate change (detector/allowlist), outside this lot's reservation.
- **Owner:** coordinator; presentation-gate owner as executor.
- **Resume:** next presentation-gate maintenance pass, before T14/T15 accept
  static-audit evidence that includes this file.
- **Closure criterion:** the module is either registered as an owned brand
  constructor or restructured cast-free, with the detector's negative tests
  still proving that deliberate forgery fails.

### P5 — T13-F050 stays open

The register entry keeps its `open` status; acceptance of this delivery, the
T13/T15 status change and any claim that the affected EN/ES suite is fully green
belong to the coordinator. The first draft's five extra static findings and the
per-locale browser evidence should be recorded in the entry when the coordinator
reconciles it.

## 16. Independent coordinator acceptance — 2026-10-02

**Accepted for the currently published parenthesised racial-maximum citations;
F050 resolved and reservation released.** This does not close T15, certify the
static presentation gate or claim interpretation of unpublished citation forms.

Independent evidence is in
`build/cache/t13-parallel/reference-citations-coordinator-review/`: `review.py`,
`independent-review.json`, isolated `probe.test.ts` and its scoped Vitest config.
The coordinator independently verified:

- Five entry byte copies match their recorded hashes. All 701 frozen canonical
  YAML hashes remain unchanged; the accepted F051 auditor hash is preserved.
  `warband-reference.ts` is unchanged; reader seams, generator and reference
  components have no working-tree diff.
- Fresh runs: **36 TypeScript, 10 rendered, 21 maintained distance-display and
  four independent reader probes pass**. Both workspace typechecks and the
  generator `--check` pass. The reviewer did not repeat the browser session;
  section 13 is retained executor browser evidence, supplemented by fresh real
  rendered output checks.
- The actual publication has 30 unique maximum profiles and 19 cited IDs. All
  cited IDs resolve, every profile carries all nine numeric values, and no
  current EN/ES effect uses an unadmitted `campaign.limit.*` form.
- The retained static report has 775 findings. The six in `catalogue-text.ts`
  contain expressions already present in its entry bytes; the other two changed
  production files add none. Dynamic report findings are empty. These retained
  reports are inspected evidence, not a newly repeated full presentation gate.

**Closing-checksum erratum:** `postchange-hashes.txt` reports two incorrect
values, for `reference-citations.ts` and `reference-citations.test.ts`. All listed
values have the proper SHA-256 length; this is a value discrepancy, not malformed
hex length. The original report is preserved and is not used as proof of those
bytes. The independently reviewed and freshly tested current values are:

| File | Independent SHA-256 |
| --- | --- |
| `packages/typescript/application/rules/reference-citations.ts` | `34352606e6793cc1a09f2a5ad4fa6aa0406123fa62285befcf64216cf300e503` |
| `tests/typescript/application/rules/reference-citations.test.ts` | `359d7f43011885e9c8cfdfda32fb071edeee1f6d5be42fa05b949ad4c1d25328` |

The other five reported file hashes match; the independent JSON records all
seven current hashes and the discrepancies. Acceptance refers to these current
tested bytes, not the two erroneous values in the executor's report.

Disposition of section 15 proposals:

1. **P1 → F053:** conditional source-admission task for another citation grammar
   or family. No current source needs that extension. An admitted product flow
   may not intentionally display raw IDs merely because a grammar is unsupported.
2. **P2 → F054 for duplicate identity handling:** a new independent probe through
   the actual reader confirms its index retains the last row when two maxima
   share an ID. The resolver then receives one row and prints that profile.
   Consequently section 7's duplicated-ID absence behavior is a **direct helper
   contract**, not an end-to-end reader guarantee. Missing and incomplete rows
   do produce the localized absence through the real reader in both locales;
   these controls need no deliberately damaged canonical KB row. No current
   published IDs are duplicated.
3. **P3 resolved at the maintained product-convention boundary:**
   [reference-template guidance](../../../guides/warband-reference-template.md)
   requires ES Movement in the existing centimetre convention, and
   `adaptCharacteristicValue` explicitly documents `M 4 → M 10`. The independent
   probes and maintained distance suite confirm this path is reused once without
   changing stored values or other maxima. No printed Spanish-source editorial
   certification is claimed; a contrary future source would require a separate
   units-policy review rather than a special F050 formatter.
4. **P4 → F055:** the six inherited catalogue-brand static findings retain their
   own presentation-gate owner and closure barrier; no suppression is accepted.
5. **P5 resolved by this independent acceptance:** source/read-model/render
   resolution is accepted for valid current citations. First-draft additional
   static findings are absent in the final report. T15 and other product gates
   retain their own acceptance conditions.

The coordinator records these dispositions in the shared follow-up register and
releases the reservation. No production repair, commit, push or agent launch was
performed during this review.
