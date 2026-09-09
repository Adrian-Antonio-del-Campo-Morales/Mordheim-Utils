# Coordination log — web repo rework (parallel agents)

Agents working in parallel on [`web-migration-parallel-plan.md`](../../web-migration-parallel-plan.md)
log here: claimed tasks, decisions that cross task boundaries, and information
the other agent needs. Append entries; never rewrite another agent's entry.

---

## 2026-09-09 — Agent B: P6.1 **completed** — timeline & state selection

**Service level** (`packages/typescript/application/campaign/timeline.test.ts`,
4 tests, real P3.2 port + neutral KB): moment enumeration
(draft → states → battles → pending post-battles in timeline order),
`selectMoment` mutates only the view (campaign deep-equal before/after,
never dirty), and the plan's acceptance **export → reimport preserves the
timeline verbatim** (states/battles/post_battles/current_state_number) —
including the view section travelling through the port on import.

**UI** (`apps/warband-manager-web/src/features/timeline/TimelinePanel.tsx`
+ 3 component tests): ordered moment list with human labels (dates for
states, scenario for battles), selected moment marked `aria-current`,
navigation through the service only. Wired **additively** into
`CampaignSlice.tsx` above the state display; `useCampaignApp` gained
`selectMoment` (wraps `app.selectMoment`, updates the document snapshot,
propagates errors) — one new seam method, existing slice behaviour intact.

**Noted:** your P6.2 DraftPanel tests were failing mid-write during my run
(mtimes seconds before); with your latest files the app suite is **11 tests,
2 failed** — both yours (`P6.2 DraftPanel`), all 9 of mine green. App build
is currently blocked by 2 type errors in your in-flight
draft files (`DraftPanel.test.tsx` prop mismatch,
`useDraftWorkflow.ts` unused var) — heads-up only, not mine to fix.

**Verified:** packages **98/98** + tsc clean; app 9/11 (2 yours); Python
regression **289 passed**; `git diff --check` clean. Nothing committed.

---

## 2026-09-09 — Agent B: claiming **P6.1** (timeline & state selection)

Taking **P6.1 — Timeline y selección de estados** (depends on P3.5/P5.1/
P5.2, all green; explicitly parallel with your P6.2).

**Files I will create/touch:**
- `apps/warband-manager-web/src/features/timeline/**` (new — timeline
  navigation UI, moment list, current-state panel; consumes the campaign
  slice's service through `useCampaignApp` only)
- `apps/warband-manager-web/src/features/campaign/CampaignSlice.tsx` —
  **additive wiring only**: mount the timeline panel beside the existing
  display; I will not alter your P6.2 draft UI files
- `packages/typescript/application/campaign/timeline.test.ts` (service-level
  tests of `selectMoment` + timeline invariants)
- coordination log updates.

**Files I will NOT touch:** `features/draft/**` (yours), `adapters/**`,
`domain/**`, `service.ts`, `types.ts`, your P6.2 files. Acceptance includes
the plan's "export & reimport preserves the timeline" item, which I'll run
through the real P3.2 port + Python cross-check pattern from P7.2 if needed.

---

## 2026-09-09 — Agent A (update 11): claiming **P6.2** (draft & initial composition feature block)

P7.2 is yours (noted, no overlap). I'm taking **P6.2 — Draft y composición
inicial**: the first P6.x feature block, enabled by my P3.5 kernel
(`createDraft`/`composeDraft`/`commitInitialWarband` are real now).

**Files I will create/touch:**
- `packages/typescript/application/campaign/features/draft/**` (orchestration
  over the kernel use cases)
- `apps/warband-manager-web/src/features/draft/**` (UI: warband picker,
  roster editor, limits display, commit button)
- `apps/warband-manager-web/src/App.tsx` (wire the draft feature beside the
  campaign slice — additive; the campaign slice stays untouched)
- coordination log updates.

**Files I will NOT touch:** everything under
`apps/warband-manager-web/src/features/campaign/**`,
`packages/typescript/adapters/**`, `domain/**` kernel files,
`application/campaign/service.ts`, `application/campaign/types.ts`, and your
P7.2 corpus. If `App.tsx` wiring conflicts with something you're doing, log
it and I'll rebase my edit.

---

## 2026-09-09 — Agent A (update 10): full integration green + **P7.5 completed** + KB bundling decision

**Integration verified after your P3.2 + my P3.5:** packages **60/60**, app
**5/5**, `npm run build` **unblocked and green** (240 kB → 75 kB gzip — your
last note flagged my WIP files as blocking it; they're finished now),
Python `tests/web` **33 passed** incl. your new contract round-trip tests
(16 in `tests/web/contract`). The plan's Python↔web round-trip acceptance
is green from both sides. Nice work on the adapter.

**P7.5 — KB artefact performance (completed):**
- Measured (ruleset `mordheim`): raw 2 176 kB, **gzip 209 kB**; index build
  from parsed JSON < 50 ms.
- `tests/web/test_kb_artefact_performance.py` (3 tests, skip cleanly without
  the artefact): gzip **budget < 300 kB** (test message tells you to
  partition rather than raise it), index-build cost < 2 s, and the record
  counts pinned (81/534/278/75 — update the test deliberately when the KB
  changes).

**Decision — KB bundling (`docs/decisions/web-kb-bundling.md`), resolves
your open P5.2 question:** ship the artefact as a **static asset** copied to
`public/knowledge/knowledge-web.json` at build time and `fetch()` it once
(209 kB gzip inlined would triple the JS bundle; a separate asset is
cacheable). Add a `createArtefactKnowledgeReaderFromUrl(url)` constructor
wrapping my P4.3 `ArtefactKnowledgeReader.from()`; no port change. **Your
action:** swap the fake reader in `default-deps.ts` when ready — that
completes P5.2's acceptance with real KB ids. **P8.1 must** run the
generator `--check` and copy the artefact to `public/knowledge/` before
`npm run build` (artefact stays gitignored).

**Next for me:** idle on new claims until you pick from P6.x — whichever
block you don't take, I will (claiming in the log first, as always).

---

## 2026-09-09 — Agent B: P7.2 **completed** — corrupt corpus asserted from both sides

**Corpus** (`tests/web/contract/corpus/`, 24 `.mordheim` files +
`manifest.json`): one violation per file — invalid JSON, top-level array,
wrong marker, retired v1/v2/v3, future version, missing/malformed version,
missing/malformed `saved_at`, missing campaign, unknown top-level section,
missing required campaign/identity fields, wrong types (`stats` string,
`complete: "yes"`), negative nonnegative int, unknown warrior property,
invalid `kind`, empty ids, bad `upkeep_resources` pair, battle missing
`casualties`, unknown view property. The manifest records the **stable TS
reason** and the **stable Python message substring** per file.

**Two harnesses, one manifest:**
- `packages/typescript/adapters/campaign-file/corpus.test.ts` (26 tests) —
  every file through `CampaignFileV4Adapter`, exact `reason` match,
  schema violations must carry `location`, retired messages name found +
  supported versions, and the error-quality rule (plan §P7.2): no stack
  traces / internal paths in messages.
- `tests/web/contract/test_corrupt_corpus.py` (28 tests) — every file
  through the desktop `load_campaign`, `CampaignFileError` with the
  manifest substring, same noise rules.

**Two real validator gaps the corpus caught and I fixed (my P3.2 files):**
1. `schema-validator.ts` didn't implement **`enum`** (invalid `kind` passed).
2. `additionalProperties: <schema>` (the `int_map` case) was only enforced
   when the object also had `properties` — now enforced standalone, and
   `additionalProperties` as a subschema validates the extra values.

**Contract note (both sides confirmed):** an unknown-but-schema-valid
`band_id` is still not a file-layer rejection — reference resolvability is
the KnowledgePort concern (Agent A's P3.3 finding holds).

**Repair of my own P5.2 tests (caused by progress, not breakage):** with the
real port + P3.5's `validateStructure` running on import, the slice's test
campaign needed a consistent timeline (`current_state_number` must exist in
`states`) and integer `stats` — the old fixture was schema-shaped but not
domain-valid. Fixed the fixture, no product code changed. Note the import
validation message is good UX already:
"Campaign rejected by domain validation: current_state_number 1 does not
exist in the timeline."

**Verified:** corpus TS 26/26; campaign-file suite **43/43**; packages **86/86**
(incl. Agent A's kernel tests); app **5/5**; app build OK (240 kB → 75 kB
gzip); Python `tests/web` **62 passed**, campaign+architecture+contracts+web
**289 passed**. `git diff --check` clean.

**Next for me:** P7.1 full bidirectional round-trip hardening or P6.8 prep —
will claim in the log before touching files.

---

## 2026-09-09 — Agent B: claiming **P7.2** (corrupt cases & references)

Note on your "next" list: the P5.2 Python↔web round-trip acceptance is
**already delivered** (my P3.2 entry — `tests/web/contract/test_p32_roundtrip.py`
validates TS-serialized documents with the desktop reader). So P7.5 stays
yours if you want it. I'm taking **P7.2: corrupt documents & unknown
references** — corpus of one-violation-per-file documents in
`tests/web/contract/corpus/`, asserted from BOTH implementations (TS adapter
typed reasons + Python reader stable errors), plus the contract finding that
an unknown-but-schema-valid `band_id` is NOT a file-layer error
(application/KnowledgePort concern per your P3.3 note). No overlap with
P7.5, P6.x or your other files.

---

## 2026-09-09 — Agent A (update 9): P3.5 **completed** — kernel use cases are real

**Claimed & delivered: P3.5 — domain kernel behaviour** in
`packages/typescript/domain/campaign/kernel/` (new files: `document.ts`,
`create-draft.ts`, `commit-warband.ts`, `record-battle.ts`,
`post-battle-steps.ts`, `equipment.ts`, `hirelings.ts`,
`kernel.test.ts`; modified: `default-usecases.ts`). The frozen P3.4 surface
(`state.ts`/`ports.ts`/`usecases.ts`) is untouched.

**What the kernel now does (pure TS ports of the Phase-2 Python domain):**
- `document.ts` — immutable helpers + structural invariants (ordered
  timeline, unique battle/post numbers, unique warrior/inventory ids,
  draft-has-no-states, `current_state_number` exists). `validateForExport`
  now runs these — stricter than before, same stable `invalid_input`
  reasons, so your P5.1 tests still pass unchanged.
- `create-draft.ts` — `createDraft` (band roster → identity/configuration
  from KB, mandatory members, cheapest-henchman fill to minimum models,
  all-hero-optional fallback) and batch `composeDraft` honouring the frozen
  `DraftCompositionInput` (`band_id` + `rows[]`), with gold/model/hero limit
  rejections. Profiles resolve by stable id with a band-scoping guard
  (artefact's unscoped fallback rows can't leak another band's profile).
- `commit-warband.ts` — State #0 with the Python legality formulas
  (members×5+XP+hireling rating; treasury = gold − recruitment −
  equipment).
- `record-battle.ts` — snapshot battle node + pending post-battle with
  hireling-upkeep follow-ups; result normalization win/loss/draw.
- `post-battle-steps.ts` — forward-only 8-step navigation, step payloads
  preserved verbatim in `step_state` (open-payload policy).
- `equipment.ts` — stash↔warrior with `owned = equipped + stash`
  conservation; fixed (non-transferable) entries refuse to move.
- `hirelings.ts` — hirelings add rating without consuming roster capacity;
  `applyAdvance` validates the choice format before state checks.

**Two integration notes for you (Agent B):**
1. **`createDefaultUseCases()` signature change (backwards compatible):**
   it now accepts an optional `KnowledgeReader` —
   `createDefaultUseCases(deps.knowledge)` — because the frozen surface
   calls `composeDraft(document, input)` without a reader and the real
   implementation needs one. I already wired it in your `service.ts` (one
   line); no-arg calls still work (every KB lookup misses → clean
   `not_found` rejections). All your P5.1 tests pass untouched.
2. **The `prerequisite_missing` stubs are gone** — every frozen
   `CampaignUseCases` method now has real behaviour. Your slice's
   "not ported yet" message path won't trigger for these actions anymore.
   Scenario loot / availability / advance rolls remain P6.4–P6.6.

**Verified:** `tsc --noEmit` clean (incl. your P3.2 adapter files);
packages **60/60** (my 12 new kernel tests + your suites); app 5/5;
Python regression **383 passed** (web+contracts+campaign+architecture+
knowledge).

**Next for me:** with P3.5 landed and your P3.2 in the tree, the natural
follow-ups are the Python↔web round-trip acceptance of P5.2 (once your P3.2
serializer is done) or P7.5 (KB artefact performance). Claiming here first.

---

## 2026-09-09 — Agent B: P3.2 **completed** + P5.2 fake port retired

**P3.2 — real `.mordheim` v4 file adapter** (`packages/typescript/adapters/campaign-file/`):

- `index.ts` — `CampaignFileV4Adapter implements CampaignFilePort`. Envelope
  ladder exactly per the contract README: invalid JSON → bad marker →
  retired v1–3 (found + supported in the message) → unsupported newer
  version → schema violation. `serializeCampaign` **validates before
  returning** ("Refusing to save" + JSON path), mirroring the Python writer.
- `schema-json.ts` — the contract schema embedded verbatim (generated from
  `contracts/campaign-file-v4/campaign-file-v4.schema.json`; single source of
  truth, no runtime dep). `schema-validator.ts` — minimal draft 2020-12
  walker over exactly the schema's keyword subset ($ref/$defs, prefixItems,
  const/pattern/minLength/minimum, additionalProperties:false), errors carry
  JSON paths like the Python reader.
- `index.test.ts` — **17 tests**: all four fixtures parse + shape coverage,
  every rejection class, semantic round-trip per fixture (comparing with
  `saved_at` **and** `view` excluded — the port serializes the campaign
  state; view is reconstructible and legitimately not re-emitted),
  open-payload preserve-in-place (injected future field survives byte-exact),
  refuse-to-save path.
- **P3.2↔P3.3 cross-check (Agent A: take note)** — the TS test emits
  `_ts-roundtrip-artefact.json` + `_p32-serialized-*.json` (gitignored), and
  my new `tests/web/contract/test_p32_roundtrip.py` (3 tests) validates each
  emitted file with the **desktop Python reader**
  (`load_campaign`) and asserts semantic equality with the fixtures modulo
  `saved_at`/`view`. **The plan's Python↔web round-trip acceptance now runs
  green.** If the artefact files are absent the Python tests skip cleanly.

**P5.2 completion:** `default-deps.ts` now wires `CampaignFileV4Adapter` as
the real file port (fake retired; the knowledge reader stays fake until we
decide how the KB artefact reaches the browser bundle — needs a P5/P8
decision on bundling `build/generated/knowledge-web/knowledge-web.json`).
App tests 5/5 with the real port.

**P5.1 test adjustment (Agent A: caused by your P3.5 progress):** your
`default-usecases.ts` rewiring made `assignEquipment` real, so my
service.test.ts no-throw case now expects the KB-miss rejection
(`not_found`) instead of `prerequisite_missing` — same rejection-as-value
convention, updated premise. One-line comment in the test documents this.

**Verification:** campaign-file 17/17; packages suite 59/60 (the 1 failure
is your in-flight `kernel.test.ts` "moves equipment stash↔warrior" — mtime
seconds before my run, not mine); app tsc clean except your WIP kernel
files; app tests 5/5; Python `campaign+architecture+contracts+web` = **260
passed**. App production build is currently blocked **only** by your
in-flight `create-draft.ts`/`commit-warband.ts`/`document.ts` type errors —
heads-up so you know they're visible from `npm run build`.

---

## 2026-09-09 — Agent A (update 8): claiming **P3.5** (domain kernel use cases)

`adapters/campaign-file/` is still empty, so **P3.2 stays yours** (your
conditional claim from the P5.2 entry is visible — go ahead). I'm taking
**P3.5: domain kernel behaviour** under `domain/campaign/kernel/` — files I
will create/touch: `document.ts` (immutable document helpers + invariants),
`create-draft.ts`, `compose-draft.ts`, `commit-warband.ts`,
`record-battle.ts`, `post-battle-steps.ts` (minimal step navigation),
`equipment.ts`, `hirelings.ts`, plus `default-usecases.ts` rewiring and
`*.test.ts` files beside them.

**Files I will NOT touch:** `adapters/campaign-file/**`, `application/**`,
`apps/**`, `kernel/state.ts`, `kernel/ports.ts`, `kernel/usecases.ts` (frozen
P3.4 surface — P3.5 implements against it, never edits it),
`kernel/rejections.ts` (read-only use).

**Note for your P3.2:** when you swap the fake file port, the slice's export
path will run my `validateForExport` invariants — documents failing them
should surface as `schema_violation`-adjacent export errors; the invariants
mirror the Python writer's structural checks (ordered timeline, unique
battles, draft-has-no-states). No action needed, just awareness.

---

## 2026-09-09 — Agent B: claiming **P3.2** (real `.mordheim` v4 file adapter)

Taking my earlier conditional claim: `packages/typescript/adapters/campaign-file/`
is still empty and no entry claims it. Agent A: as long as your next entry
(update 8) doesn't claim P3.2, this is mine — I'll deliver it this turn with
fixtures + all error classes + round-trip, then swap the real port into
`default-deps.ts` (my P5.2 file) and run the Python↔web round-trip that
completes P5.2's last acceptance item.

If you were about to start it, reply here before writing files and I'll yield.

---

## 2026-09-09 — Agent A (update 7): failure hunt across P4.2/P4.3 — 1 bug found & fixed

Probed the generator and adapter for edge-case failures:

1. **BUG (fixed):** `--ruleset trollheim` (a collection whose campaign
   catalogues don't cover it) crashed with a raw `ValueError` from deep in
   `mordheim_knowledge.loader` — no actionable context. `generate()` now
   wraps any non-GenerationError failure in `GenerationError` naming the
   ruleset; the build still stops, but with a clear message. Regression
   test added (`test_unsupported_ruleset_fails_with_actionable_error`).
2. **Adapter invariant probes (new `tests/web/test_adapter_hostile_inputs.py`,
   5 tests):** no null/empty ids in any family; no duplicate ids that would
   shadow the TS adapter's Maps; every `names` entry a non-empty string;
   `weapon_hands` positive ints; profile rows always carry
   `collection`+`band_id` (your scoped-key assumption in
   `indexProfiles`). All hold against the real artefact — your adapter's
   assumptions are guaranteed by the generator side, not just by luck.
3. **Artefact collections check:** `bands_by_collection` keys exactly match
   the ruleset's collections (new test).

Nothing your files need to change; the probes document the invariants your
`ArtefactKnowledgeReader` relies on. Verified after fixes: Python 380 green
(web+contracts+campaign+architecture+knowledge), TS tsc clean + 31/31.

**Still open for me:** P7.3 prep or a P6 block — claiming before touching.

---

## 2026-09-09 — Agent A (update 6): P3.3 **completed**

**Claimed & delivered: P3.3 — contract test harness** (`tests/web/contract/
test_contract_harness.py`, 13 tests).

Same-scenario evidence for both implementations, from the contract README:
- the 5 rejection cases (invalid JSON, wrong marker, retired v1–v3 with found+
  supported in the message, schema violation naming `identity`, unresolvable
  `band_id`);
- `saved_at`-only semantic volatility verified for **all four fixtures**
  through real save/load round-trips;
- **open-payload preserve-in-place**: an injected future field in
  `step_state` survives a Python round-trip byte-exactly;
- fixtures ↔ KB id agreement (band ids resolve against the source tree).

**Contract finding worth reading (Agent B — affects P3.2/P5.2):** the schema
and KB-reference validation are **independent layers**. The Python reader
does NOT resolve `band_id` against the KB on load (schema checks presence,
not resolvability) — resolvability is a KnowledgePort concern at application
level. Your TS file adapter must do the same: schema-valid documents with an
unknown band pass the file layer; the domain/application layer rejects them
via KnowledgeReader (`not_found`). Documented in the harness test
`test_harness_unresolvable_band_id_is_a_reference_concern`.

Verified: `tests/web` full = **23 passed** (10 + 13); cross-suite Python
373 green; TS 31/31 green (your service tests untouched).

**Next for me:** with P5.2 (yours) in flight I'll take **P7.3 (architecture
& bundle checks)** prep or pick up a P6 feature block — claiming in the log
before touching files, as usual.

---

## 2026-09-09 — Agent A (update 5): P4.3 **completed** + artefact path aligned

1. **Artefact path fixed (your sync item #3):** `ROOT` in the generator is
   now `parents[2]` — it writes `<repo>/build/generated/knowledge-web/
   knowledge-web.json`, the documented path your coherence test reads.
   Re-verified: byte-determinism still holds (`--check` ok) and the artefact
   regenerates identically at the new location. Deleted the stale
   `tools/build/` copy.
2. **`ok: false` on error sites (your P5.1 note):** acknowledged — but that
   was in `kernel/ports.ts`, which you own; I saw you already added the
   discriminator there and my adapter picks it up unchanged (my adapter's
   error returns don't construct `CampaignFileError`s, they only produce
   `KnowledgeResult`).
3. **P5.2 claim acknowledged** — good luck; everything you need is in place
   (P4.3 reader works against the real artefact end to end).
4. Verified after the path change: TS `tsc` clean, **31/31 TS tests**, Python
   `tests/web` **10/10**.

**Next for me: P3.3 (contract test harness) — claiming now.**

---

## 2026-09-09 — Agent B: P5.2 **completed** (vertical slice, fake ports)

**Claimed & delivered: P5.2 — import → display → edit → export.**

- `apps/warband-manager-web/src/features/campaign/` (new, app-owned):
  - `CampaignSlice.tsx` — the slice UI: file input, identity/roster/
    inventory rendering, error `role=alert` panel, dirty `role=status`
    indicator, replace-campaign confirmation button, sample rename edit and
    the export button.
  - `useCampaignApp.ts` — the only place the shell touches the service;
    translates file-port errors into human messages (retired version names
    the found version and the fix; schema violations include the JSON path);
    `FileReader` fallback for jsdom's missing `File.text`.
  - `fake-file-port.ts` / `fake-knowledge-reader.ts` — **stand-in ports**;
    swapping in P3.2/P4.3 is a one-line change in `default-deps.ts`.
- `App.tsx` now renders the slice (P3.1's placeholder smoke test still
  passes — heading preserved).
- **Wired the `@domain`/`@app` path aliases** (tsconfig `paths` + Vite
  `resolve.alias`), both P3.1-owned files. Note for Agent A: Vite alias
  replacements need forward slashes on Windows — `fileURLToPath` output must
  be normalized or module resolution fails at build time.
- Tests: 4 component tests (import & display, retired-version alert,
  invalid-JSON alert, replace-confirmation flow) + the shell smoke test.

**Acceptance status (plan §6):** import ✓, readable errors ✓, display with
resolved ids ✓ (fake KB), one edit ✓ (view-level; real rule edits need
P3.5/P6.x — the `__rename_warband__` action currently surfaces the standard
not-ported rejection), export via Blob download ✓, dirty indicator ✓,
confirm-before-replace ✓. **Remaining for full acceptance:** Python↔web
round-trip of the exported file, which lands automatically once P3.2's real
serializer replaces the fake.

**Verified:** app typecheck clean; app 5/5 tests; packages 31/31; app build
OK (204 kB → 64 kB gzip); lint clean; Python 250 green (`campaign+
architecture+contracts+web` — up from 237, Agent A added 13). `git diff
--check` clean.

**Next for me:** idle on features until P3.2 lands (then I swap the fake
port + run the Python↔web round-trip), or I can take **P3.2 itself** if
Agent A is busy with P4.3 follow-ups — claiming here first, per protocol.

---

## 2026-09-09 — Agent B: P5.1 **completed** (+ one P3.4 port fix)

**Claimed & delivered: P5.1 — in-memory application service.**

- `application/campaign/service.ts` — `createCampaignAppService(deps)`
  implementing the frozen `CampaignAppService`: `importCampaign` (with the
  confirm-replace guard), `exportCampaign` (validated serialization +
  filename from warband name), `run(action, input)` dispatch to domain use
  cases, `selectMoment` (never dirties), `isDirty`, `current`.
- **Undo/history** lives in the service (50-deep stack), separate from rule
  logic; every successful use-case run pushes the previous document.
- `domain/campaign/kernel/default-usecases.ts` — default use cases covering
  what the frozen state model already supports (`selectMoment`,
  `validateForExport` with structural invariants: timeline ordering, unique
  battle numbers, draft/state consistency, `current_state_number` must
  exist). Everything else rejects with `prerequisite_missing` until P3.5/
  P6.x land — rejections are values, never thrown.
- `domain/campaign/kernel/rejections.ts` — shared rejection constructor for
  feature blocks.
- `application/campaign/service.test.ts` — 9 tests: import → edit → export
  with fakes in plain Node, confirm-replace guard, file-error translation
  (invalid JSON / retired version / schema violation), no-campaign errors,
  unknown action, not-ported rejection, dirty tracking, undo semantics.

**One fix to my own P3.4 port (additive, contract-level):**
`CampaignFileError` now carries `ok: false` as discriminator — without it,
`ParseResult`/`SerializeResult` could not narrow by `ok` (found while
writing the service; the earlier fakes in `types.test.ts` masked it because
TS only needs the discriminant present in *one* member when the objects are
built inline). Agent A: your adapter's error returns need `ok: false` added
— one-line change per error site, and `if (!parsed.ok)` narrowing now works
everywhere.

**Note:** I saw your knowledge-reader WIP compile errors from last turn are
resolved (full `tsc` clean now, 31/31 TS tests green including your locale
chain tests). The artefact path question from my sync entry still stands:
the generator writes `tools/build/…` but the documented path is
`<repo>/build/…` — I copied it there manually; please align `ROOT` to
`parents[2]` when convenient.

**Verified:** `tsc --noEmit` clean across domain+application+adapters;
31/31 TS tests; Python 237 green; `git diff --check` clean.

**Next for me:** P5.2 vertical slice (import → display → edit → export in
the React shell) now that P3.1+P3.2-less flow works with the real file port
blocked only on P3.2 — I'll build P5.2 with the fake file port first and
integrate P3.2 when either of us lands it. Claiming P5.2 here.

---

## 2026-09-09 — Agent B: contract sync P4.2 ↔ P3.4 **resolved**

I read your update 2 and answers, and verified them against the **real
artefact** (generated locally, 81 bands / 534 profiles / 278 items / 75
skills — matches your stats). Findings and resolutions:

**1. Confirmed matches (no conflict):**
- `KnowledgeKind` families ↔ emitted record families: one-to-one ✓
- `names` per locale with canonical `en`, `es` from `name_i18n` ✓ (every
  record family carries non-empty `names`; locale set is exactly `en|es` —
  matches my `Locale` union)
- `items` use `item_id`, other families use `id` ✓ (documented in the ports)
- `indexes.items_by_id` / `bands_by_collection` coherent with arrays ✓
- deterministic output re-verified by me on a second generation ✓

**2. Conflict found & resolved (port change, generator unchanged):**
My original `Id` union only covered 8 id spaces; your adapter needs the
campaign-section families too (hirelings, injuries, mutations, lores,
post-battle steps, warband groups, racial maximums, collections). **I have
extended `Id` in `domain/campaign/kernel/ports.ts`** with `injury_id`,
`mutation_id`, `post_battle_step_id`, `warband_group_id`,
`racial_maximum_id`, `collection_id`, and added the exported map
`ID_KIND_BY_FAMILY` (record family → id discriminator) so your adapter can
convert without a hand-maintained switch. This is additive — your two open
compile errors (`KnowledgeKind` not assignable to id kind) should now be
solvable with `ID_KIND_BY_FAMILY[kind]` instead of a cast. My typecheck in
`domain/` + `application/` stays clean with the new union.

**3. One operational note — artefact output path:**
Generating via `python tools/knowledge/generate_knowledge_web.py` writes to
`tools/build/generated/knowledge-web/…` (ROOT = `parents[1]` of a script in
`tools/knowledge/` = `tools/`), but both your doc and my coherence test
document the location as `<repo>/build/generated/knowledge-web/…`. I copied
the artefact to the documented path and removed `tools/build/`. **Please
either change `ROOT` to `parents[2]` in your generator or confirm the
intended path** — one of us should align it; the artefact itself is
byte-identical either way (it is gitignored, so no repo pollution either
way). My `adapters/knowledge-reader/artefact-coherence.test.ts` (new, 5
tests) runs against the documented path and skipIf the artefact is absent.

**4. I did NOT touch your WIP files** (`adapters/knowledge-reader/index.ts`,
`knowledge-reader.test.ts`, `artefact-types.ts`) — they are mid-write and
fail typecheck right now; flagged here so nobody mistakes that for a broken
integration. Your `knowledge-reader.test.ts` locale-chain failures look like
in-progress work, not contract drift — ping me here if you want the
coherence test extended instead.

**Files I touched this turn:** `domain/campaign/kernel/ports.ts` (Id union +
ID_KIND_BY_FAMILY), `adapters/knowledge-reader/artefact-coherence.test.ts`
(new), this log. Verified: `tsc` clean outside your WIP files, my 22/22 →
25/27 test total with your 2 WIP failures, Python 237 green.

**Next for me:** P5.1 application service as soon as your P4.3 lands (or
with fakes now if you prefer); P3.2 remains open for either of us.

---

## 2026-09-09 — Agent A (update 3): claiming **P4.3**

Taking **P4.3 (KnowledgeReader adapter over the generated artefact)** now —
if you were about to claim it, say so in the log before pushing files under
`packages/typescript/adapters/knowledge-reader/`. I will only create files
there plus this log entry; nothing else.

---

## 2026-09-09 — Agent A (update 2): P4.2 **completed**

**Claimed & delivered: P4.2 — generator YAML → JSON web.**

- `tools/knowledge/generate_knowledge_web.py` — reads only through
  `mordheim_knowledge` loaders; validates ids/references **before** writing
  (`GenerationError` stops the build); deterministic output verified
  **byte-identical** across runs (sha256 checked); `--check` mode for CI
  (regenerate & compare); `--output` override. Output: `build/generated/
  knowledge-web/knowledge-web.json` — gitignored (`build/` already was).
- `tests/web/test_knowledge_artefact.py` — 6 tests: required sections present,
  byte-determinism, id uniqueness (profiles scoped `collection/band_id`),
  reference resolution (profiles→bands, items⊆KB universe, indexes coherent),
  exclusion policy (no `out-of-scope`/simulation surfaces), per-locale names
  with canonical English. All 10 `tests/web` green; 360 passed across
  `campaign+contracts+knowledge+architecture+web`.
- **Artefact stats (mordheim):** 81 bands, 534 profiles, 278 items (excl.
  `out-of-scope`), 75 skills, 2.3 MB raw (gzip expected well under 400 KB —
  measure in P7.5).

**Answers to your requests (P4.2 output vs your ports):**
1. Your `KnowledgeKind` union matches my emitted record families one-to-one
   (`band`, `profile`, `item`, `skill`, `scenario`, `post_battle_step`,
   `injury`, `lore`, `mutation`, `hireling`, `warband_group`,
   `racial_maximum`) — **no change needed before freezing**. Two notes:
   - my `items` records use field **`item_id`** (not `id`); bands/profiles/
     skills use `id`. Your `Id` union values map directly.
   - my `campaign` section keeps catalogue documents keyed by YAML stem
     (`trading-post`, `serious-injuries`, …) plus dedicated
     `hirelings{profiles,rules,traits}`, `warband_groups`,
     `racial_maximums`, `post_battle_sequence` (normalized: `id`, `name`,
     `resolves`, `order`, `repeatability`). P4.3 flattens these into
     `KnowledgeRecord`s at load — the raw sections stay preserve-in-place.
2. **P3.2: go ahead** — I won't take it. Implement `CampaignFilePort` per
   your error reasons; my Python writer (`persistence/campaigns.py`, v4 with
   jsonschema validation on write+load) is the reference producer; fixtures
   in `contracts/campaign-file-v4/fixtures/` are your test corpus.
3. Deleted `docs/decisions/web-rework-coordination.md` (your duplicate
   consolidation note acknowledged — this log is the single board).

**Next for me: P4.3 (KnowledgeReader adapter over the artefact)** unless you
claim it in the log; otherwise I'll pick up P3.3 (contract test harness).

---

## 2026-09-09 — Agent A (this thread)

**Claimed:** P4.1 — Inventario de catálogos KB requeridos por campaña.

**Delivered:**
- `docs/decisions/web-knowledge-catalog-inventory.md` — versioned inventory
  (24 catalogue groups) derived from the public read surface of
  `KnowledgePort`, with per-catalogue stable IDs, the **explicit Combat Lab /
  simulation exclusions** (simulation mappings, execution contract, runtime
  scope, item kind `out-of-scope`), and the agreed **web artefact JSON shape**
  (see below).
- `tests/web/test_kb_artefact_inventory.py` — 4 tests keeping the inventory
  honest: every required pattern matches real KB files and is documented;
  documented campaign catalogues are actually consumed by the port; every
  `band_id` in the v4 fixtures resolves against the KB; excluded surfaces are
  documented. **No dependency on P4.2's generator** — it reads YAML sources
  directly, so P4.2 can start now.

**Decision — artefact JSON shape (for P4.2/P4.3):**
- top level: `schema_version: 1`, `ruleset`, `collections`, `bands`,
  `profiles`, `items`, `skills`, `weapon_hands`, `campaign.{...}`, `indexes`;
- **display names travel per locale** as `names: {en, es}` on each record —
  this resolves coupling #2 of the prep doc (no `mordheim_knowledge.i18n` at
  web read time; the web resolves locale client-side);
- stable IDs byte-identical to the KB (`band_id`, `profile_id`, `item_id`,
  `rule_id`); no name-based inference;
- deterministic output: sorted by ID, no timestamps.

**Decision — item kinds in the artefact:** `armour`,
`close-combat-weapon`, `combat-equipment`, `material-or-upgrade`,
`ranged-weapon`, `shield-or-defence`, `trollheim-equipment`. Excluded:
`out-of-scope` (57 rows, steeds/spawns marked out of campaign scope).

**Fact useful to P4.2 sizing:** for ruleset `mordheim` — 48 bands in 2
collections (mordheim, trollheim), 335 items, 75 skills, 102 hireling
profiles + 44 hireling rules, 10 post-battle steps, 29 racial maximum rows.

**Not touched:** any `apps/`, `packages/` or TS files (P3.x unclaimed),
persistence, v4 contract. Only new files + this log.

**Next for me:** P4.2 (generator YAML → JSON web) unless the other agent
claims it; if so I'll take P3.4 (TS interfaces).

---

## 2026-09-09 — Agent B (REPO REWORK 2 thread)

**Claimed & completed: P3.1 — TypeScript workspace (React + Vite).**

- Files owned and created: everything under `apps/warband-manager-web/`
  (`package.json`, `tsconfig.json`, `vite.config.ts`, `eslint.config.js`,
  `index.html`, `src/main.tsx`, `src/App.tsx`, `src/App.test.tsx`,
  `README.md`) plus 4 additive lines in `.gitignore` (gitignoring
  `apps/warband-manager-web/dist|coverage` and `packages/typescript/**`
  build output). Sorry for the tiny shared-file touch — it was additive only.
- Verified: `npm install` clean, `npm test` (1 test), `npm run build`
  (typecheck + Vite build OK, 193 kB → 61 kB gzip), `npm run lint` clean.

**Claimed & completed: P3.4 — public domain/application TS interfaces.**

- Files owned and created: `packages/typescript/{package.json,tsconfig.json,
  vitest.config.ts}` and `domain/campaign/kernel/{state,ports,usecases}.ts`,
  `domain/campaign/index.ts`, `application/campaign/{types.ts,index.ts,
  types.test.ts}`, `architecture/purity.test.ts`.
- **Verified:** `tsc --noEmit` clean (strict + `exactOptionalPropertyTypes`);
  5 vitest tests pass in plain Node (fakes for KnowledgeReader, use cases,
  app service). Purity test verified **non-vacuous** by mutation: injecting a
  `react` import into `domain/` fails the suite.
- **Note:** there is an older `docs/decisions/web-rework-coordination.md` I
  created earlier; **this log is now the single board** — I will only update
  this file from now on (feel free to delete the other one, Agent A).

**Decisions Agent A must know:**
1. **Package manager: npm** (plan §12: no switching inside tasks). Node 26.
2. `packages/typescript/` has its own npm project (not npm workspaces yet).
   Its `tsconfig.json` includes `adapters/**/*.ts` with a **glob**, so P3.2
   and P4.3 can drop files under `packages/typescript/adapters/` and be
   typechecked + tested by the existing scripts without editing shared
   config. If you need a workspace-level restructure, propose it here first.
3. **Types are aligned with your P4.1 decisions:** `KnowledgeRecord.names`
   is `Record<Locale, string>` (`en`/`es` per locale, resolved client-side —
   coupling #2); ids are a tagged union (`band_id`/`profile_id`/`item_id`/
   `skill_id`/`scenario_id`/`rule_id`/`lore_id`/`hireling_id`), so id spaces
   cannot be mixed; `KnowledgeResult` models absence as `{ok:false,
   reason:"not_found"}` — never a name-based guess.
4. **Use-case results are values, not exceptions:** `UseCaseResult = {ok:true,
   state} | UseCaseRejection` with stable `reason` strings — P6.x and P5.1
   share this convention; rejection reasons listed in `kernel/usecases.ts`.
5. **`saved_at` is the only volatile field** in comparisons (file port types
   in `kernel/ports.ts` mirror the v4 README).
6. The domain state model mirrors the v4 contract sections 1:1
   (`identity/configuration/resources/current_state_number/warriors/battles/
   states/post_battles/inventory/special_rules/manual_log` + separate
   `view`), so P3.2's document→state mapping stays mechanical.

**Requests to Agent A:**
- P4.2: generator output shape — please emit the artefact you specified; if
  record `kind` values or id fields differ from the `KnowledgeKind`/`Id`
  union in `domain/campaign/kernel/ports.ts`, tell me here **before** you
  freeze the generator, so P4.3's adapter and my ports stay in sync.
- P3.2 (unclaimed): the file port to implement is `CampaignFilePort` in
  `kernel/ports.ts` (`parseCampaignFile`/`serializeCampaign`, error reasons
  `invalid_json|bad_marker|retired_version|unsupported_version|
  schema_violation|unknown_section|io_error`). Drop it under
  `packages/typescript/adapters/campaign-file/` and it's picked up by the
  existing tsconfig/vitest globs automatically.

**Next for me:** standing by for P5.1/P5.2 once P3.2 lands, or I can take
**P3.2 itself** if Agent A prefers to continue on P4.2 — claiming here first
to avoid collision.
