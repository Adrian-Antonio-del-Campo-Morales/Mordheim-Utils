# Project backlog

Track unresolved defects, verification work and deferred capabilities here.
Detailed procedures belong in the linked guides; affected records and live
counts belong in executable inventories and generated reports.

Statuses below describe the recorded evidence. A reported failure remains
unverified against the current tree until the relevant check is rerun; a closed
implementation queue does not establish integrated correctness.

## Work overview

| Work | Recorded status | Dependency or next step |
| --- | --- | --- |
| [Modular integration](#close-modular-integrated-verification) | Implementation queue closed; integrated verification pending | Run the scoped closure procedure on one integrated revision. |
| [Web artefacts](#regenerate-the-web-artefacts) | Generation and freshness pass on 2026-10-21; one artefact-level check outstanding | Confirm Dwarf inheritance against the fresh artefacts. |
| [Combat Lab popover](#combat-lab-checklist-popover-closes-during-layout) | Failure observed; cause unknown | Reproduce the focused case and establish why the popover closes. |
| [Test classification](#test-classification-coverage) | Phase classification implemented and selected by both runners; functional ordering not validated | Decide cross-runner integration and validate the order on an integrated revision. |
| [Optimized engines](#subsequent-vectorized-and-native-engine-work) | Follow-on work to scope | Complete modular verification before defining the porting delta. |
| [Knowledge and translations](#knowledge-gaps) | Open follow-ups | Use canonical references and the live review queues. |

## Pending verification and reported defects

### Close modular integrated verification

**Status:** the implementation queue is recorded as closed. On 2026-10-21 the
default E2E battery (5,254 scenarios), the modular and construction suites
(1,975 passed, 9 skipped), the clause-registry tool tests and the shared
eligibility bundle pass, and `clause_registry.py query --pending` is empty.
`verify` now reports `structural_complete=True` (1,054 profiles compile) with
`semantic_complete=False` (622/2,087 obligations verified, 1,465 pending, 3,793
passed cases, 864 detected mutations, 217/217 required interactions covered).
The TypeScript typecheck and `build-eligibility.mjs --check` pass, and the
register keeps its 4,556 keys with `--pending` empty. Integrated verification
stays open because the pending obligations and the E2E coverage gaps below
remain. Follow the
[closure procedure](docs/reference/verification.md#modular-integration-closure).

- Run the existing modular combat, construction, modular semantic and E2E
  checks together on one integrated revision. Include the E2E scenarios,
  coverage inventory and accepted-evidence non-regression checks from
  `tests/E2E/modular-engine/`.
- Verify the configuration → `compile_fighter` → `initialize_duel` →
  `resolve_round` path using existing canonical cases. Include recipients,
  equipment loss, effect composition, save ordering, resources and expiry in
  the affected cases; add only genuinely missing discriminators.
- Check TypeScript types, the generated eligibility bundle, relevant editorial
  contracts and clause-register integrity. Confirm no admitted work is pending
  and preserve the 4,556 clause keys and their traceability.
- Group failures by shared cause and fix admitted defects without weakening
  positive tests or admission controls. Earlier failures count when they prevent
  closure; record any unresolved concrete blocker here. Repaired on 2026-10-21:
  the `profile-rule.*` compiler namespace now accepts both maintained contract
  tables (Necrotect Hatred), default profile compilation supplies each printed
  mandatory initial choice through `required_profile_build` (Trapper, Rat Ogre,
  Cripple), the Curse of the Revenant projection supplies its Great Thirster
  prerequisite, and three non-discriminating mutations now remove every carrier
  they claim to remove (True Grit ×2) or witness the fist consumer (plague-cart
  unarmed exemption). Structural layer: 1,054 profiles compile.
- Rerun affected groups after fixes, then perform one final integrated
  confirmation on the delivered revision. Reuse valid output instead of
  repeating unchanged checks. The 2026-10-21 battery is that integrated run for
  the E2E corpus; rerun only what later changes affect.
- Vectorized: the armour operator now matches `phases.armour_target` and its
  seven exact parity checks pass. The two parity report tests remain incomplete
  while 248 vectorized obligations (244 tags, 4 fields) are pending in the
  follow-on port; the family/roster coverage checks also fail on the grown
  catalogue (14 failures in `tests/python/combat/vectorized`, measured
  2026-10-21).
- Semantic pins: the 421 stale `sources[].digest` pins measured on 2026-10-21
  were renewed with `refresh_spec_digests.py`; only digest fields changed and
  `--check` now reports 0 stale. The semantic suite passes against the current
  content, and the reviewed dispositions for Inconsistency, Spectral Touch,
  Netter, Energy Focus and Sea Dragon Cloak are preserved. That renewal is not
  a per-specification interpretation review: the scope/rule-row changes behind
  the stale pins have not been reviewed file by file, and a corpus-wide refresh
  is still not semantic acceptance.
- Knights Feats was reviewed on 2026-10-21. Only Sword Master is a published
  canonical skill with an executable mechanic, so the Knights Errant list now
  publishes that single member and the other three printed feats are refused
  instead of being admitted as selectable no-ops. Combat Charge, Lancer and
  Armour Specialist have no canonical skill record, mechanic or execution
  contract; Lancer's mounted charge continuation and Armour Specialist's 5+
  armour-save floor would also need operators that do not exist. Their printed
  text stays in the band rule. Publishing and implementing them is future work,
  not an admitted defect.
- Resolve admitted E2E coverage gaps under `MORDHEIM_E2E_REQUIRE_COMPLETE=1`
  before global closure: 27 identities with admitted clauses and no scenario,
  and 44 identities with uncovered clauses (measured 2026-10-21). Passing
  ordinary inventory checks after justified exclusions does not establish
  completeness or positive semantic evidence.
- Carry the modular whipcrack priority correction into optimized-backend parity
  work. The vectorized proposal was deferred; this integration verifies only
  the modular path and does not establish optimized parity.

**Close when:** the applicable integrated checks, including the modular E2E
battery, pass on the delivered revision,
all admitted consequences have a usable configuration-to-consumption path,
no known executable or composition defect remains, and register integrity is
preserved. A closed CSV alone does not certify the modular engine.

**Scope:** modular E2E validation is part of this closure. Investigate and fix
admitted defects exposed by the battery without weakening source-derived
expectations. This closure does not include optimized-backend parity, engine
coverage campaigns, statistical certification or optimized engine implementation.

### Regenerate the web artefacts

**Status:** generation and freshness pass on 2026-10-21.
`python tools/knowledge/generate_knowledge_web.py` wrote 161 bands, 1,056
profiles, 464 deferred items and 87 skills with no bilingual label conflict, and
`--check` reports the artefacts up to date. Aquatic Mutants pass against the
fresh artefacts
([`mutations.test.ts`](tests/typescript/domain/campaign/mutations.test.ts), 9
tests, run from `packages/typescript`). Dwarf inheritance was not separately
rechecked against the regenerated JSON: its four E2E scenarios pass in the
battery but exercise compilation, not the web projection.

**Next steps:** confirm Dwarf inheritance in the fresh artefacts, or state the
limitation where the web route is validated. Do not hand-edit generated JSON or
weaken validation.

**Close when:** generation and freshness checks pass and every claimed
artefact-level check has been run against the current artefacts.

### Combat Lab checklist popover closes during layout

**Status:** reproduced on 2026-10-21; no cause has been established.

**Recorded failure:** two cases in
[`test_checklist_popover.py`](tests/python/ui/test_checklist_popover.py),
`test_popover_body_matches_the_dark_theme` and
`test_popover_shows_a_visible_scrollbar`, fail after `root.update()`: the
popover's scrollbar path is already destroyed (`TclError: bad window path
name`), so the widget tree is torn down during layout. Both failed before and
after the UI ownership move.

**Next step:** determine why the popover closes during layout and correct its
lifecycle or the test's focus setup as appropriate.

**Close when:** both focused cases pass with the theme, width and scrollbar
assertions preserved.

### Test classification coverage

**Status:** the phase classification is implemented and connected to both
runners. `pyproject.toml` registers the eleven categories,
`tests/conftest.py` rejects a collected item under a classified root without
exactly one, and `tools/verification/test_sequence.py` orders the eight
functional phases with a barrier between parallel categories. On 2026-10-21 the
Python suite collected 13,029 items, all partitioned across the categories; the
TypeScript (964 items) and web (444 items) suites select categories through
native Vitest projects. No functional battery was executed to validate the
classification. See
[the sequence contract](docs/reference/test-sequence.md#verification-performed-on-2026-10-21).

**Pending:**

- The Python launcher sequences Python only. The TypeScript/web projects are
  selectable (`--project`), but running the eight phases in one command does not
  execute them; integrating them needs a separate cross-runner session with the
  web suite's working directory and its own barrier. Until then, the phase
  sequence is a Python contract plus separately selectable JS categories.
- Vitest 3.2.7 has no per-test tag, so a Vitest file is the smallest selectable
  unit. `tests/web/architecture/boundaries.test.ts` mixes source-boundary checks
  with two post-build bundle guards; the whole file is `phase0_preflight` and the
  bundle guards skip without a build. Per-test selection needs a newer Vitest
  with tags, or a `<name>.<category>.test.ts` token plus one project per token
  (renames 158 files and changes every Vitest report identity).
- The additional categories run only with `--extras` or
  `--sequence-category`. A default phase run therefore leaves the semantic audit,
  coverage baseline and coverage gate unvalidated; that is a deliberate ordering
  decision, not a claim that they pass.
- Phase 0 contains harness self-tests that are independent of the product; the
  harness and mutation witnesses that drive the real pipeline are classified in
  the phase they exercise. If a future phase-0 item starts loading the KB or
  compiling fighters, it must move to that product phase rather than keep the
  preflight label.
- `tests/python/application`, `tests/python/ui`, `tests/python/persistence` and
  `tests/python/cli` are classified as the application tier under
  `phase7_warband` because the requested phases name only Warband Manager. If the
  Combat Lab shell is meant to have its own phase, that is a new category and
  launcher decision.
- A test added to a classified root without a category fails collection by
  design. Re-collect after concurrent edits; the guard covers only the listed
  roots and `tests/specs` remains declarative YAML.
- Validate the ordering on one integrated revision once the functional failures
  recorded above are repaired. A plan printout proves selection and order, not
  that a prerequisite passes before its consumers.

**Close when:** the cross-runner decision is recorded, the Vitest per-file
limitation is either accepted permanently or removed, and a functional run on an
integrated revision confirms the phase order.

### T08 vectorized `cripple` fixture gap

**Status:** accepted temporary exception, documented 2026-10-23. T08 consumes
the frozen corpus for every other execution block; this one test still compiles
its crippler from the KB.

**Test and original build:**
`tests/engines/vectorized/test_rule_families_a.py::test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects`
compiles `FighterBuild("mordheim", band_id="chaos-streets-mordheim-inhabitants",
profile_id="cripples", collection="trollheim")` and initializes it with
`_new_state(cripple, 1, FixedRng(4))`.

**Failure:**
`ValueError: Disability requires one permanent supplied result (condition.disability-1..6)`.

**No exact fixture:** the corpus has no recoverable entry for that build. Its
only frozen crippler uses `condition.disability-6`, which is not the rolled 4
the test asserts, and the available artefacts contain no `CompiledFighter` with
disability 4.

**Accepted exception:** keep this single `compile_fighter` call and the original
scenario temporarily. Do not change the assertion, substitute `disability-6`,
invent a configuration or repair the compiler as part of the testing rework.

**Close when:** T06/coordination decides whether to publish an exact frozen
variant with a supplied permanent result of 4 or to move the scenario to the
construction tier. Until then the test is not fixture-independent.

## Statistical parity adaptation and backend verification

Parity battery renovation, scope revised 2026-10-22: adapt the existing scenario
catalogue and profiles to statistical comparison of real modular/candidate duel
results, preserving historical tolerances and the legacy command path. Remove
internal-event witnesses as prerequisites; do not add engine instrumentation.
Keep genuine unsupported-input cases explicit and inside the coverage denominator.
The statistical path is connected (P03: catalogue → real duels → outcome
comparison → CLI/report); focused execution evidence remains pending and P04/P05
are later execution campaigns.

Known limits to keep visible: `c03-petru-potion` (B01.3) stays `INCOMPATIBLE`
inside the denominator because its origin is Petru's pre-battle potion table,
which the KB declares out of scope (`implemented: NO`, pre-battle campaign
allocation with persistence). `v01-restriction` (B01.5) keeps its limit because the
only expression of the clause is a charge `build_duel_state` rejects before
sampling. `v14-handler`/`v14-handler-absent` (B14.5) are **not** a limit: the
bear-only reading was wrong. `leadership.py:170-203` carries a second canonical
branch for Squigs (recipient identity `night-goblins-web:cave-squigs`, provider
`squig-herder` with `mechanic.handler-leadership` within 6", 12" with a squig
prodder, mirrored in `vectorized/_leadership.py:346-366`), so both cases are
prepared with Cave Squigs + Squig Herder and a supplied Stupidity state that
makes the Leadership test observable. They must be executed before their parity
is claimed.
`q00-honorable`, the knocked-down recovery cases and the other former `state:`
blocks are now prepared inside the duel with the current APIs. See the
[current plan](TMP_VECTORIAL_ENGINE_2A2B/parity_update/PARITY_BATTERY_RENOVATION.md)
and [adaptation status](TMP_VECTORIAL_ENGINE_2A2B/parity_update/P03-deliverable.md).

The modular remains the validated oracle. NumPy is received as implemented;
this backlog does not restart its port or establish that G07 passed. Keep the
motor's historical acceptance separate from the renewed statistical campaign.

1. **Record applicable NumPy evidence:** identify the integrated revision, the
   historical battery actually run, results and remaining concrete defects.
   Reuse valid G07 evidence; do not require the renewed profiles or internal
   instrumentation to close that separate scope. Implementation alone does not
   establish statistical acceptance.
2. **Complete the native implementation where support is missing:** port the same contracts into the
   existing Cython backend and compile/folding layer. Rebuild the extension and
   test the native path explicitly; a NumPy fallback is not native evidence.
   Independent backend families may be developed in parallel with disjoint owners.
3. **Verify and qualify the optimized backends:** use the existing deterministic
   rule and whole-duel comparisons first, then targeted interactions and the
   applicable parity/certification gates in
   [Verification](docs/reference/verification.md). Benchmark only correct, supported
   paths. Report backend-specific limits and evidence before enabling broader use.

Demonstrated engine defects found while adapting the battery (2026-10-22, static
reading only; none was fixed here and none was inferred from a statistical
result alone):

- **Freed-from-net recovery differs (vectorized).** The modular contract frees the
  victim and stands it in the same recovery: `modular/rounds.py:552-565` sets
  `KNOCKED_DOWN` and records `freed_from_net`, and
  `modular/aftermath.py:125-134` stands any `KNOCKED_DOWN` in that own-turn
  recovery. `vectorized/_driver.py:863-876` excludes those rows from `stood2`
  (`~netted2`), so the candidate leaves the freed fighter knocked down. Observed
  in `v09-netted`: `condition[second]` standing 45.6 % modular vs 0 % candidate,
  `winner[first]` 52.1 % vs 75.1 %. Close when one netted row shows the same
  recovery stance in both engines.
- **Helpless damage over-subtracts wounds (vectorized).** For a helpless
  close-combat hit the modular returns `OUT` with `damage=1` and leaves `wounds`
  untouched (`modular/attacks.py:741-747`); the vectorized marks `OUT` and still
  subtracts the full damage (`vectorized/_attacks.py:757-764`, `:776-786`), so it
  publishes negative wounds where the modular keeps the pre-hit value. This is
  the located asymmetry behind the systematic excess at `wounds[-1]` with
  matching `condition`/`winner` (q04/c04/v02/v03/v06/v08/v12 families). The
  battery does **not** normalise it; close when the helpless rows stop being
  subtracted in the candidate.
- **Black Hunger backlash resolves against stale rows (vectorized).**
  `_driver.py:711-722` computes `active` once, before the three hit groups, never
  re-filters after a hit takes the bearer out, and rescues Force of Will inside
  the backlash. The modular resolves one hit at a time on the updated state and
  breaks as soon as the bearer is inactive (`modular/aftermath.py:243-258`), with
  no rescue there. The candidate therefore lands hits 2..n on a bearer the
  oracle stops hitting: `q11-black-hunger` reports `condition[first]` standing
  52.9 % → 23.1 % and out of action 36.1 % → 52.0 %, the same direction and order
  as the observed `winner[second]` 35.7 % → 51.1 %. Close when a fixed backlash
  count stops resolving hits on a row already out of action.
- **A cancelled charge does not cancel engagement (vectorized).** After a failed
  round-0 Stupidity test the modular clears the charge and recomputes
  `engaged = engaged and any(charges)` (`modular/psychology.py:126-131`), so
  `modular/rounds.py:674-677` exchanges no blows. The vectorized computes
  `engaged` once before Psychology (`_driver.py:799-801`), rebinds only
  `first_charges`/`second_charges` from the Stupidity outcome (`:986-1021`) and
  recomputes `engaged` only for Fear (`:1040-1041`), so the duel keeps making
  contact without the charge bonus. Observed in the `v14-*` winner cases, e.g.
  `v14-slave-absent` 98.9 % unresolved modular vs 38.7 % second wins candidate.
  Close when a forced Stupidity failure leaves the round without contact.
- **Bear-hug rows reach wound resolution unsorted (vectorized).** `hug_rows`
  accumulates across prepared attacks (`vectorized/_attacks.py:1147-1161`), so
  attack 1's rows follow attack 0's and `won_rows` is not monotonic;
  `_prepare_weapon_attack` keeps that order (`:1168-1172`, the filter at `:202`
  is order-preserving) and `_resolve_weapon` re-derives positions with
  `np.searchsorted(active, hit_rows)` (`:465`), which requires sorted input and
  returns `len(active)` otherwise. `c05-bear-hug` raises `IndexError: index 4891
  is out of bounds for axis 0 with size 4891` — the index equals the array size.
  No battery input is implicated. Close when the case resolves and the sorted
  rows produce identical positions.
- **Black Lotus decision key does not carry the round key (vectorized).** The
  main pool calls `_resolve_weapon` without `key`, so it stays at the default
  `test` (`vectorized/_attacks.py:392,433`) and asks `test.lotus-critical`,
  while the modular composes `round.{r}.{side}.attack.{i}.lotus-critical` from
  its own key (`modular/attacks.py:556`). `v03-poison` only reaches comparison by
  declaring the extra `test.lotus-critical` entry, which keeps the same refusal
  instead of changing the rule. Close when the candidate asks under the round
  and attack key the catalogue declares.
- **Admission refusals are engine-side, not battery-side.** The received run's
  25 `INCOMPATIBLE:construction` rows (now reported as
  `INCOMPATIBLE:admission`) come from `require_optimized_support(...,
  backend="numpy")` on the real NumPy batch entry point
  (`vectorized/_driver.py:761-767` → `kernel.py:257-266`), whose gate is the
  snapshot at `kernel.py:122-182` minus `NUMPY_CONNECTED_TAGS` (`:216-220`). They
  clear only when a port group connects the behaviour.

**Close when:** the statistical adaptation is connected, its later campaign has
applicable evidence, and remaining backend-specific work has its own results and
limits. Do not infer native support from NumPy or reopen completed motor work
because the renewed battery is still pending. None of this expands into the
deferred domains below.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Resolve hireling `unresolved_references` | As canonical skill, prayer, rune, equipment, mount, companion or procedure catalogues become available, replace the resolved references with validated canonical links. Keep genuinely unresolved references explicit. |
| Define composite-entity schemas | Establish the schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae to the hiring catalogue. |
| Review Trading Post price differences | Review the live price-collation queue and record source-backed decisions in the maintained resolutions CSV. |
| Make unsupported item-to-engine mappings explicit | Record intentionally unsupported mappings so catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing interface messages and remove unused message keys. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md) for the owning
contracts and procedures.

## Human decisions

No unresolved human decisions are currently listed here. Record new questions
with the affected source or contract and the work they block. Move accepted
answers to [Design rulings](docs/decisions/design-rulings.md).

## Deferred product scope

These domains are deliberately outside the current duel runtime, rather than
missing requirements for modular closure. Implementation requires an approved
scope change in
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml):

- group psychology and warband-wide proximity effects;
- shooting and missile weapons;
- movement, terrain and falling;
- magic in battle;
- mounts and ridden combat;
- scenario table mechanics beyond progression rewards.

## Sources of truth

| Question | Maintained source or command |
| --- | --- |
| Which rule consequences are in scope? | Each rule's `runtime` block and the runtime-scope registry linked above. |
| Are admitted clauses pending? | `python -X utf8 tools/knowledge/clause_registry.py query --pending` |
| What semantic obligations remain? | `python tools/mordheim-utils.py verify --inventory` |
| Where is the rule-review inventory? | `python tools/mordheim-utils.py report rules` |
| Which hireling references are unresolved? | `unresolved_references` in the hireling YAML. |
| Which prices need review? | `python tools/knowledge/maintenance/price-collation.py`, its generated `outputs/knowledge/` report and the [maintained resolutions CSV](tools/knowledge/maintenance/price-collation-resolutions.csv). |
| Which decisions are binding? | [Design rulings](docs/decisions/design-rulings.md). |

When updating this backlog, keep the observed symptom, evidence date, remaining
uncertainty, next action and closure condition together. Remove resolved entries
when their evidence is available; retain permanent decisions in their owning
reference rather than turning this file into a completion log.
