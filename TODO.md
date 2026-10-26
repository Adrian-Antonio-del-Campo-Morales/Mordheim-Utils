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
| [Combat Lab popover](#combat-lab-checklist-popover-closes-during-layout) | Reproduced; cause unknown | Establish why the popover closes during layout and correct its lifecycle. |
| [Optimized engines](#statistical-parity-adaptation-and-backend-verification) | Follow-on work to scope | Complete modular verification before defining the porting delta. |
| [Knowledge and translations](#knowledge-gaps) | Open follow-ups | Use canonical references and the live review queues. |

## Pending verification and reported defects

### Close modular integrated verification

**Status:** the implementation queue is recorded as closed. On 2026-10-21 the
default E2E battery (5,254 scenarios), the modular and construction suites
(1,975 passed, 9 skipped), the clause-registry tool tests and the
shared-eligibility checks pass, and `clause_registry.py query --pending` is
empty.
`verify` reports `structural_complete=True` (1,054 profiles compile with their
default construction — the 1,056 web profiles include the two vehicle profiles
the runtime scope excludes); it is a structural gate, and the retired semantic
specification layer is not a second certification surface.
The TypeScript typecheck and `build-eligibility.mjs --check` pass, and the
register keeps its 4,556 keys with `--pending` empty. Integrated verification
stays open because the E2E coverage gaps below remain. Follow the
[closure procedure](docs/reference/verification.md#modular-integration-closure).

- Run the existing modular combat, construction and E2E checks together on one
  integrated revision. Include the E2E scenarios, coverage inventory and
  accepted-evidence non-regression checks from `tests/integration/e2e/`.
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
- Optimized backends stay outside this closure and are tracked under
  [Optimized engines](#statistical-parity-adaptation-and-backend-verification):
  the armour operator matches `phases.armour_target` and its seven exact parity
  checks pass, while 248 vectorized obligations (244 tags, 4 fields) are still
  pending in the follow-on port. In that recorded run the two parity report
  tests and the family/roster coverage checks on the grown catalogue did not
  pass (14 failures in `tests/engines/vectorized`, measured 2026-10-21).
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
  completeness or positive behavioural evidence.
- Carry the modular whipcrack priority correction into optimized-backend parity
  work. The vectorized proposal was deferred; this integration verifies only
  the modular path and does not establish optimized parity.

**Close when:** the applicable integrated checks, including the modular E2E
battery, pass on the delivered revision, the admitted E2E coverage gaps are
closed under `MORDHEIM_E2E_REQUIRE_COMPLETE=1`, all admitted consequences have a
usable configuration-to-consumption path, no known executable or composition
defect remains, and register integrity is preserved. A closed CSV alone does not
certify the modular engine.

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
([`mutations.test.ts`](tests/applications/warband_manager/domain/campaign/mutations.test.ts), 9
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
[`test_checklist_popover.py`](tests/applications/combat_lab/ui/test_checklist_popover.py),
`test_popover_body_matches_the_dark_theme` and
`test_popover_shows_a_visible_scrollbar`, fail after `root.update()`: the
popover's scrollbar path is already destroyed (`TclError: bad window path
name`), so the widget tree is torn down during layout. Both failed before and
after the UI ownership move.

**Next step:** determine why the popover closes during layout and correct its
lifecycle or the test's focus setup as appropriate.

**Close when:** both focused cases pass with the theme, width and scrollbar
assertions preserved.

## Statistical parity adaptation and backend verification

Parity battery renovation, scope revised 2026-10-22: adapt the existing scenario
catalogue and profiles to statistical comparison of real modular/candidate duel
results, preserving historical tolerances and the existing command entry points.
One runner (`run_parity`) serves the deep pair matrix, the battery and the
round-truncation horizons; no per-layer execution adapters remain. Remove
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
[verification reference](docs/reference/verification.md) for the execution workflow.

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
| Make unsupported item-to-engine mappings explicit | Record intentionally unsupported mappings so catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing interface messages and remove unused message keys. |
| Bind the Night Goblin Netter to `mechanic.netter` | `night-goblins-mic/band--night-goblin-special-skills-netter` binds only `condition.netted`, while `mechanic.netter` is the family id and the tag the modular, native and vectorized engines consume (`modular/aftermath.py`, `native/_combat_compile.py`, `vectorized/_attacks.py`, `_driver.py`); selecting the skill never grants it. Add the `mechanic.netter` binding (scope YES) beside `condition.netted`, then verify the compiled tag and the netter checks. Closes `tests/knowledge/combat/test_canonical_family_catalogue.py::test_all_implemented_canonical_families_are_executable_for_every_member` and `::test_unique_effect_members_share_the_family_binding_parameters`. |
| Classify the Moulder mutations authorization | `skaven-of-clan-moulder-web/band--mutations` declares `runtime.scope: YES` with no binding (`implemented: NO`) — the only such rule in either collection — while its own reason states that each printed recipient carries the admitting clause and its quantity. Declare it outside the duel runtime (`scope: NO` on runtime and effect), or give it a compiler binding if band-level purchase validation is intended. Closes `tests/knowledge/test_runtime_bindings.py::test_in_scope_knowledge_rules_have_known_bindings`. |

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
| Which editorial rule obligations are inventoried? | `python tools/mordheim-utils.py check verify --inventory` |
| Where is the rule-review inventory? | `python tools/mordheim-utils.py check report rules` |
| Which hireling references are unresolved? | `unresolved_references` in the hireling YAML. |
| Which decisions are binding? | [Design rulings](docs/decisions/design-rulings.md). |

When updating this backlog, keep the observed symptom, evidence date, remaining
uncertainty, next action and closure condition together. Remove resolved entries
when their evidence is available; retain permanent decisions in their owning
reference rather than turning this file into a completion log.
