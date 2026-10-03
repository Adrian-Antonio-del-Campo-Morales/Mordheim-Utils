# T13 — R2/R3 Fimir and Boglar save thresholds

Execution delivery for the lot reserved as **R2/R3 — Fimir and Boglar save
thresholds** in the [initiative checklist](../README.md), and for the two
registered findings it targets:
[T13-F011](T13-execution-follow-ups.md) (Fimir Warriors compile natural armour
6+ instead of the printed 5+) and [T13-F012](T13-execution-follow-ups.md)
(Boglars compile regeneration 4+ instead of the printed 5+).

Both mismatch classes are repaired in production, with specification cases that
read their expectations from the source clauses and with real modular saves.
The executor does **not** accept or close anything: F011, F012 and T13 keep
their status, and T13-F013 (Curse of the Revenant) was not touched — its source
contract is still unresolved and `survivors-of-strigos-sylv/strigoi-vampire`
keeps the generic 4+ binding.

The delivery has one out-of-reservation necessity that the coordinator must
review explicitly: the two mirrored band documents under `sources/2B/…` were
edited as well, because the maintained staging-promotion invariant requires the
canonical KB to be the *exact* promotion of the 2B tree (section 2.2).

## 1. Entry state and hashes

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, unchanged at
  closing. The shared working tree already carried other lots' modifications
  (198 dirty entries at entry; other writers kept editing during the lot). None
  of them was touched.
- Entry revalidation (`entry-check.py`, 2026-10-01T16:37:14Z): every dispatched
  input hash matched the working tree, `all_inputs_match: true`, and the five
  byte-for-byte backups reproduce the dispatched hashes,
  `backup_hashes_match: true`. The dispatch entry
  (`build/cache/t13-parallel/profile-save-thresholds-dispatch/entry.json`,
  coordinator-owned, read-only here) reserves exactly these five inputs:

| Reserved input | Entry SHA-256 | Outcome |
| --- | --- | --- |
| `packages/python/roster-construction/mordheim_construction/compiler.py` | `e0609525f55918b9ef218984b2a5b8d011648856410d0c7e32064d4f55bc4588` | changed (+17 lines) |
| `packages/python/roster-construction/mordheim_construction/selection.py` | `70cf27c135b47321f7b9ecb1fee82de251ac15101801958b7011fe583dcabd69` | untouched |
| `packages/python/roster-construction/mordheim_construction/contracts.py` | `f9b6b9963452f4c4009d6a02cd90f119d06be21fe19390a63f0ef89ee8dc6429` | untouched |
| `sources/knowledge/bands/mordheim/lords-of-the-marsh-mim/special-rules.yaml` | `d28be86a8923881ac9d722e12f7d34bd495d66c00c64f8024b2bb3e6110faac1` | changed (+4 lines) |
| `sources/knowledge/bands/mordheim/underworld-alliance-mim/special-rules.yaml` | `65a961ead9aca194714a4ef327de86b0976300178582d236f25a6bbda463b9de` | changed (2 replaced lines) |

- The mutable shared inputs (the follow-up register, the reservations README,
  the automatic-grants research, the plans and the specification/code tools)
  were read but never written; `closing-check.txt` records their current
  hashes next to each HEAD hash so the coordinator can attribute every dirty
  byte.
- The dispatch's `compiled_baseline` (Fimir 6+, Young Nobles 6+, Boglars
  regeneration 4+ with the fire block, Warpstone Troll 4+) was reproduced
  before any write and again from the backups at closing: section 5.

## 2. Scope, authorization and the mirror necessity

### 2.1 Authorization

Authorized writes, and only these:

1. the two canonical band documents (binding parameters only) and the narrow
   compiler override in `compiler.py`;
2. `selection.py` and `contracts.py` were reserved *if needed* and were **not**
   needed: their hashes still equal the dispatched ones;
3. the new specification files `tests/specs/semantic/grants/t13-fimir-scaly-skin.yaml`
   and `tests/specs/semantic/grants/t13-boglar-regeneration.yaml`;
4. the new test modules under `tests/python/construction/` and
   `tests/python/combat/modular/`;
5. this document and evidence under
   `build/cache/t13-parallel/profile-save-thresholds/**`.

No engine, combat-kernel, eligibility, port, historical-pin, source-prose or
shared-register edit was made. The two named documents are the **only**
`sources/knowledge` paths this lot wrote — `git status --porcelain
sources/knowledge` lists exactly them — and the closing whole-tree hash
(`913096ae…`) is recorded in `closing-check.txt` for the coordinator's
attribution of any other drift.

### 2.2 The `sources/2B` mirror (out-of-reservation necessity)

`sources/2B/…` was **not** in the five reserved inputs. It had to be edited
anyway because
`packages/python/knowledge/mordheim_knowledge/staging_promotion.py` defines the
invariant that the canonical KB equals the promotion of the 2B tree: a second
promotion of an unchanged tree is a no-op
(`tests/python/knowledge/test_staging_promotion.py::test_a_second_promotion_of_the_same_tree_changes_nothing`),
and `_promote_bands` refuses a destination document whose content differs from
the promoted one with `ACTION_CONFLICT` (“the KB already keeps this band
document with different content”).

Without the mirror, the canonical edit alone breaks that maintained invariant:
before the mirror, the staged promotion of the two bands produced a document
that differed from the KB, and the promotion test suite failed
(`pytest-knowledge-c` first attempt: 1 failed / 38 passed / 2 errors). With the
mirror in place the same suite is green (chunk C: 41 passed; focused staging
run: 9 passed) and the band documents are identical between `sources/2B` and
`sources/knowledge` after promotion, including rule order.

The mirror is exactly the same edit in the staged copies — 4 added lines in
`sources/2B/bands/mordheim/lords-of-the-marsh-mim/special-rules.yaml` and
2 changed lines in
`sources/2B/bands/mordheim/underworld-alliance-mim/special-rules.yaml` — with
no other byte touched (`closing-check.txt`). The coordinator should confirm
this path expansion or require a different repair; no other staged document
was modified.

### 2.3 Test module naming

The dispatched modular module name `test_t13_profile_save_thresholds.py` was
renamed to `tests/python/combat/modular/test_profile_save_thresholds.py`. The
repository keeps test basenames unique and has no `__init__.py` in test
directories, so the dispatched name would collide with the construction module
`tests/python/construction/test_t13_profile_save_thresholds.py` during pytest's
rootdir-relative import. An empty `tests/python/combat/modular/__init__.py` that
existed untracked in the shared tree was removed for the same reason; it was not
part of the dispatch and no tracked file was affected. The specification files
keep their dispatched `t13-` names.

## 3. Sources, clauses and decision

The clauses are the printed band rules already published in the canonical KB
(`effect`/`effect_i18n`; no prose was changed):

1. **Lords of the Marsh / Scaly Skin** (`band--scaly-skin`, one printed
   sentence, band-wide):
   *“Fimir have a 6+ armour save that cannot be modified beyond 6 by Strength;
   a 'no save' result on the Critical Hit Charts negates it. Light armour adds
   +1. **Fimir Warriors have a 5+ armour save.**”*
   The band clause keeps the shared 6+ default with its 6+ Strength floor, the
   critical “no save” negation and the stacking behaviour; the named-profile
   clause prints 5+ for Fimir Warriors **only**. Young Nobles and every other
   Fimir profile keep 6+.
2. **Underworld Alliance / Boglars / Regeneration** (`boglars--regeneration`):
   *“Whenever an enemy successfully inflicts a wound on a Boglar, roll a D6; on
   a result of 5 or more the wound is ignored and the Boglar is unhurt. Boglars
   may not regenerate wounds caused by fire or fire-based magic.”*
   Warpstone Troll's 4+ regeneration (`warpstone-troll--regeneration`) is a
   separate, correct case and keeps the generic mechanic.

Decisions taken (all narrow, no rule invention):

- **Fimir**: express the printed per-profile value as binding *parameters* on
  the existing shared compiler contract, and validate them on the single
  consumer. The schema of
  `contracts/knowledge-editorial-v1/defs.schema.json` closes
  `binding.parameters` to `allowed_skill_lists, bonuses, categories, category,
  characteristics, exempt_profile_ids, forbids, ignore_penalties,
  max_missile_weapons, profile_ids, required_tag, skills, value`, so
  `profile_ids` + `value` are the only legal way to name recipients and a
  threshold in this document.
- **Boglars**: use the existing, already-verified
  `skill.regeneration-5-plus` mechanic from
  `catalog/mechanics/execution.yaml` (regeneration 5+,
  `blocked_by_fire: true`) instead of the generic `skill.regeneration` (4+,
  also fire-blocked). This is a binding change only; it also removes the
  pre-existing precedent mismatch — `trollheim/lustria-savage-goblins/zomblintua--regeneration`
  already used `skill.regeneration-5-plus`.
- **F013**: deliberately untouched. Strigoi's contract still needs the Q013
  source decision.

## 4. Solution implemented

### 4.1 Canonical bindings

`sources/knowledge/bands/mordheim/lords-of-the-marsh-mim/special-rules.yaml` —
the shared contract gains its per-profile clause:

```yaml
      binding:
        kind: compiler
        id: compiler.lizardmen-scaly-skin
        parameters:
          profile_ids:
          - fimir-warriors
          value: 5
```

`sources/knowledge/bands/mordheim/underworld-alliance-mim/special-rules.yaml` —
`boglars--regeneration` now points at the printed threshold, both in the effect
id and in its binding:

```yaml
    - id: skill.regeneration-5-plus
      scope: 'YES'
      binding:
        kind: mechanic
        id: skill.regeneration-5-plus
```

Both staged copies in `sources/2B/…` carry the same bytes (section 2.2).

### 4.2 Compiler override with validation

`packages/python/roster-construction/mordheim_construction/compiler.py`, inside
the existing `compiler.lizardmen-scaly-skin` block (+17 lines, no other change):
the block keeps its shared default (`4` for Kroxigor, `5` for `saurus*`, `6`
otherwise) and its `natural_armour_stacks`/`natural_armour_worst_save: 6`
traits. Afterwards, for each compiler binding:

- only a binding whose `id` is `compiler.lizardmen-scaly-skin` **and** whose
  `parameters.profile_ids` contains the built profile is applied — every other
  band or species value is ignored;
- the `parameters.value` must be an `int` (bools refused) in `2..7`, otherwise
  a `ValueError` names the profile and the malformed value instead of silently
  compiling a wrong save;
- the applied value becomes `natural=value` once; there is no second
  contribution, no arithmetic and no mutation of shared contract state.

Because the override is keyed by `profile_ids`, the value is bound to the
canonical recipient list of the band, not to a string prefix: Fimir Warriors
receive 5+, `young-nobles`, `shearls` and `daemon-fimm` stay at the shared 6+,
and the unrelated Lizardmen collections keep their species values untouched.

## 5. Traceability: source → binding → compilation → behaviour

`behaviour-compare.py` (fresh process per render, byte-verified restore) shows
the entry → current compiled state for all 13 monitored profiles and proves
that the entry render still equals the dispatch `compiled_baseline` while the
live render equals the recorded target (`failures: 0`, EXIT=0). Changed cases
are exactly three; the other ten are byte-identical before and after:

| Compiled case | natural armour | armour save | regeneration | fire block |
| --- | --- | --- | --- | --- |
| `lords-of-the-marsh-mim/fimir-warriors` | **6 → 5** | **6 → 5** | 7 → 7 | false → false |
| `lords-of-the-marsh-mim/fimir-warriors` + light armour | **6 → 5** | **5 → 4** | 7 → 7 | false → false |
| `lords-of-the-marsh-mim/young-nobles` (control) | 6 → 6 | 6 → 6 | 7 → 7 | false → false |
| `underworld-alliance-mim/boglars` | 7 → 7 | 7 → 7 | **4 → 5** | true → true |
| `underworld-alliance-mim/warpstone-troll` (control) | 7 → 7 | 7 → 7 | 4 → 4 | true → true |
| `underworld-alliance-mim/goblin-bully` (control) | 7 → 7 | 7 → 7 | 7 → 7 | false → false |
| `lizardmen/skink-priest`, `lizardmen/saurus-braves`, `lizardmen/kroxigor`, `lizardmen-lus/saurus-braves`, `lizardmen-lus/kroxigor`, `trollheim/lustria-lizardmen/saurus-totem-warrior`, `trollheim/lustria-lizardmen/kroxigor` | unchanged | unchanged | 7 | false |

The construction suite additionally pins `lords-of-the-marsh-mim/shearls` and
`daemon-fimm` at the band-wide 6+; they are not part of the 13-case render.

Behaviour beyond compilation, derived from the clauses and exercised through
the real pipeline:

- **Specification cases** (canonical `grant`/`compile`/attack witnesses run by
  `verify_semantics`, `spec-check.py` EXIT=0):
  `mordheim-fimir-warriors-scaly-skin` — 8 cases (`recipients`,
  `compiled-warriors`, `compiled-young-nobles-control`, `warriors-save-holds`,
  `warriors-save-fails`, `strength-floor`, `light-armour-adds-one`,
  `critical-no-save-denies-the-save`) and 3 mutations
  (`restore-shared-six-plus`, `remove-band-strength-floor`,
  `remove-scaly-skin`), all killed.
  `mordheim-boglars-regeneration` — 7 cases (`recipient`, `compiled`,
  `compiled-warpstone-troll-control`, `all-faces`, `four-fails`, `five-saves`,
  `fire-denies-roll`) and 2 mutations (`wrong-threshold`,
  `allow-fire-regeneration`), all killed. Both targets report
  `verified: true`, `pending: false`, `fixtures_with_errors=0`,
  `uncertified_targets=0`.
- **Construction suite** (`tests/python/construction/…`): the printed 5+ and the
  6+ Strength floor, the light-armour composition, the other Fimir profiles,
  11 unrelated Lizardmen species values, the fire-blocked 5+ regeneration for
  Boglars, the untouched 4+ for Warpstone Troll and the cross-compilation
  stability in both orders.
- **Modular suite** (`tests/python/combat/modular/…`): real attack
  resolution and the whole-round duel driver. Fimir save only on 5+ (and 4+
  with light armour), S6 stops at the 6+ floor, the critical “no save” result
  negates the natural armour without requesting an armour die, and the
  isolated armour context reports `natural_armour_save == 5`. Boglars ignore
  the wound on 5+ and go out on a 4; a fire weapon (`weapon.brazier-iron`, the
  only canonical `attack.fire` producer) never requests the regeneration die,
  while an ordinary attack with the same wound does; the fire block belongs to
  the Boglar clause and does not leak to other defenders.

## 6. Before/after evidence

### 6.1 Behaviour

- `behaviour-compare.py` EXIT=0: `live render equals recorded target: True`,
  `entry render equals dispatch baseline: True`, `changed cases` = the three
  above, `restored hashes match pre-swap: True`, `untouched inputs still match
  entry: True`, `live render stable after restore: True`, `failures: 0`.
  The temporary backup swap used for the entry render was byte-exact and
  auto-restored; the live inputs were re-hashed after it.
- Red state before the production edits: the new suites failed 18 tests out of
  56 (`red/pytest-new-suites-pre.txt`), one for each clause violation
  (Fimir 6+, missing override, doubled band value, Boglar 4+ and the fire
  cases); they pass 56/56 afterwards.

### 6.2 Verification identities

`verify --json` before → after (`compare-verify.py`, EXIT=0):

- errors **30 → 30** (retained 30, removed 0, added 0) — the two repaired
  targets never appeared as errors, they were `pending` obligations;
- obligations 718 → 718; **verified 563 → 565**; **pending 155 → 153**;
- structural_complete `true` → `true`; profiles 1050; pending/verified
  interactions 258/229 and 482 assessments unchanged;
- obligation identity added
  `rule/mordheim/underworld-alliance-mim/boglars--regeneration/skill.regeneration-5-plus`,
  removed `…/skill.regeneration`; `verified_added` are exactly the two targets
  with their live digests
  (`4469e090…` for `…/band--scaly-skin/compiler.lizardmen-scaly-skin`,
  `b77614d9…` for `…/boglars--regeneration/skill.regeneration-5-plus`),
  `verified_removed: []`, `pending_added: []`;
- `verify --structural --json` EXIT=0, `structural_complete: true`, 1050
  profiles, no structural errors.

### 6.3 Suites

| Suite | Result |
| --- | --- |
| `pytest tests/python/construction -q` | 455 passed |
| `pytest tests/python/combat/modular -q` | 297 passed |
| new suites only (`-k` the two modules) | 56 passed |
| focused semantics `-k "mordheim-fimir-warriors-scaly-skin or mordheim-boglars-regeneration"` | 15 passed, 3783 deselected |
| knowledge chunk A (source audit, staging, fidelity, translation parity, registries, catalogues, loaders) | 2 failed, 133 passed, 3 skipped — both inherited |
| knowledge chunk B (catalog, editorial schemas, absence, cotejo, references, i18n, names, printed) | 1 failed, 424 passed, 10 skipped — inherited |
| knowledge chunk C (remaining knowledge files + `test_staging_promotion`) | 41 passed |
| focused `test_staging_promotion.py` | 9 passed |
| CI-rest (`web`, `contracts`, `campaign`, `architecture`, shared eligibility) | 2 failed, 1372 passed — both inherited |
| `generate_knowledge_web.py` and `--check` | EXIT=0 both; artefact up to date |

The complete `pytest tests/python/verification` run exceeded the 600-second
budget twice (with and without `-k "not test_authored_semantic_case"`); the
focused semantics run and `spec-check.py` (which executes `verify_semantics`
in-process for both fixtures) are the retained evidence for that tree.

### 6.4 Inherited failures (not caused by this lot)

All five reproduce with the entry backups restored and are independent of the
two edited documents (A/B evidence in `ab-backups-pytest.txt`,
`ab-artefact-counts.txt`, `ab-generate-entry.txt`, `ab-generate-current.txt`):

1. `tests/python/knowledge/test_campaign_catalogs.py::test_band_rules_reference_racial_maximums_without_inlining_statlines`
   — `band--human-maximum-characteristics mentions a max profile without ref`
   in `amazons-mordheim`, `sisters-of-sigmar`, `tileans`, `witch-hunters`.
2. `tests/python/knowledge/test_campaign_catalogs.py::test_hired_swords_eligibility_resolves_and_grammar_is_valid`
   — `campaign.hireling.hired-sword.albino-stormvermin` carries an unexpected
   `note_i18n` key (assertion at line 808).
3. `tests/python/knowledge/test_editorial_schemas.py::test_the_contract_is_strict_about_the_committed_documents`
   — `equipment-access.yaml.schema.json#/$defs/equipment_list.applies_to.profile_types`
   declares `str:animal`, `str:henchman`, `str:summoned` as unused by
   `mordheim/underworld-alliance-mim/equipment-access.yaml` (line 368).
4. `tests/python/web/test_kb_artefact_performance.py::TestKbArtefactPerformance::test_size_metrics_are_stable_and_reported`
   — the pin records `items=388`, `campaign_sections=16`; the shared tree now
   generates `items=449`, `campaign_sections=17` (bands 161, profiles 1056,
   skills 82 do match). Identical counts with the entry backups restored.
5. `tests/python/web/parity/python_manifest_test.py::test_every_row_is_complete`
   — the manifest names `tests/web/features/campaign/test_equipment_tab.test.tsx`,
   which does not exist in the tree.

Follow-up proposals (the coordinator assigns the identifiers) are in section 8.

## 7. Commands, exit codes and results

Reproducible from the repository root with `python -X utf8`:

| Command | Exit | Result |
| --- | --- | --- |
| `build/cache/t13-parallel/profile-save-thresholds/entry-check.py` | 0 | 5/5 inputs match the dispatch, backups written and verified |
| `tools/mordheim-utils.py verify --json` (before) | 1 | 30 errors, 563 verified, 155 pending, 718 obligations, 1050 profiles |
| `…/behaviour-compare.py` | 0 | entry render = dispatch baseline, live render = target, 0 failures |
| `…/spec-check.py` | 0 | both targets `verified: true`, 8+7 cases and 3+2 killed mutations, 0 errors |
| `pytest tests/python/verification/test_semantics.py -q -k "mordheim-fimir-warriors-scaly-skin or mordheim-boglars-regeneration"` | 0 | 15 passed |
| `pytest tests/python/construction -q` | 0 | 455 passed |
| `pytest tests/python/combat/modular -q` | 0 | 297 passed |
| `pytest tests/python/knowledge/...` (chunks A/B/C) | 1 / 1 / 0 | 2+1 inherited failures / chunk C 41 passed |
| `pytest tests/python/web tests/python/contracts tests/python/campaign tests/python/architecture tests/python/construction/test_shared_eligibility.py -q` | 1 | 2 inherited failures, 1372 passed |
| `tools/knowledge/generate_knowledge_web.py` and `--check` | 0 / 0 | artefact regenerated and verified up to date |
| `tools/mordheim-utils.py verify --json` (after) | 1 | 30 errors (exact retained set), 565 verified, 153 pending |
| `tools/mordheim-utils.py verify --structural --json` | 0 | structural green, 1050 profiles |
| `…/compare-verify.py` | 0 | 30 → 30 with verified 563 → 565, pending 155 → 153 |
| `…/closing-check.py` | 0 | HEAD unchanged, attributable diffs exact, mirrors exact, 0 failures |
| `pytest tests/python/architecture/test_documentation.py -q` | 0 | document links checked after the last edit of this file |
| `git diff --check -- <the five edited tracked paths>` | 0 | no whitespace errors |

`verify` keeps exiting 1 because of the 30 historical pre-snapshot pins already
registered in F001; that debt is untouched by this lot.

## 8. Blockers, limits and follow-up proposals

- **Nothing blocked the two targets.** Both compile and save as printed.
- The two reserved-but-unused files were left untouched; `contracts.py` and
  `selection.py` still hash to their entry values.
- The full `tests/python/verification` tree has no global green run inside the
  budget; the structural result, the focused semantics run and the in-process
  semantic check are the substitutes. The coordinator may want a
  session-budgeted full run before closing F011/F012.
- The **`sources/2B` mirror is outside the written reservation** and needs an
  explicit coordinator decision (section 2.2). No other staged document
  changed.
- The whole-round duel evidence covers the modular backend; optimized ports
  were not exercised and no port work is implied.
- T13-F013 remains blocked on its source contract; the strigoi binding is
  unchanged on purpose.

Proposals for the coordinator to register (full fields, new identifiers to
assign):

1. **Racial-maximum reference check for four bands.** *Problem:* four canonical
  band documents mention a maximum profile without a reference, failing
  `test_band_rules_reference_racial_maximums_without_inlining_statlines`.
  *Reproducer:* `pytest tests/python/knowledge/test_campaign_catalogs.py -q`
  (also red with the R2/R3 backups restored). *Impact:* advisory-metadata gate
  only; no compiled behaviour changes. *Dependency:* knowledge/editorial owner;
  the failing documents are `amazons-mordheim`, `sisters-of-sigmar`, `tileans`
  and `witch-hunters` `special-rules.yaml`. *Moment:* before the next knowledge
  acceptance that re-runs chunk A. *Close when:* the four documents reference
  their maximum profile as the test requires and the test passes without
  weakening it.
2. **Unexpected `note_i18n` key in a hired-sword catalogue row.** *Problem:*
  `campaign.hireling.hired-sword.albino-stormvermin` carries `note_i18n`,
  which the catalogue test's allowed-key assertion refuses. *Reproducer:* same
  test file, assertion at line 808. *Impact:* the catalogue contract check fails;
  this assertion alone does not establish a loader or product failure.
  *Dependency:* catalogue author plus the schema owner; either the
  key is moved under the allowed structure or the contract is extended.
  *Moment:* with the next catalogue edit. *Close when:* the row parses, the
  grammar test passes and the localized note is still published.
3. **Unused properties and enumeration values in the equipment-access schema.**
  *Problem:* the retained A/B failure reports unused equipment-list properties
  `notes`, `notes_i18n`, as well as `profile_types` values `str:animal`,
  `str:henchman`, `str:summoned`. *Reproducer:*
  `pytest tests/python/knowledge/test_editorial_schemas.py -q`. *Impact:*
  editorial strictness gate; no runtime effect today. *Dependency:* schema
  owner decides between using the values and removing them. *Moment:* before
  the next editorial-schema acceptance. *Close when:* schema and committed
  documents agree and the strict test passes unmodified.
4. **Stale KB artefact size pin.** *Problem:* the pin expects `items=388`,
  `campaign_sections=16` while the shared tree generates 449/17 (bands,
  profiles and skills still match). *Reproducer:*
  `pytest tests/python/web/test_kb_artefact_performance.py -q`; identical counts
  with the R2/R3 backups restored and with the current edits. *Impact:* the
  performance guard misreports drift and hides real regressions. *Dependency:*
  the web-artefact owner must re-pin from a stated revision, not from a dirty
  tree. *Moment:* at the next web-artefact acceptance. *Close when:* the pin is
  derived from a recorded revision and the test passes with real margins.
5. **Manifest row for a non-existent TypeScript test.** *Problem:*
  `python_manifest_test` requires
  `tests/web/features/campaign/test_equipment_tab.test.tsx`, absent from the
  tree. *Reproducer:* `pytest tests/python/web/parity/python_manifest_test.py -q`.
  *Impact:* parity manifest cannot be validated end-to-end. *Dependency:*
  TypeScript test owner (add the file or drop the row with a reason). *Moment:*
  with the next manifest refresh. *Close when:* every manifest row resolves to
  an existing test and the parity test passes.

## 9. Evidence, verification and next action

Evidence: `build/cache/t13-parallel/profile-save-thresholds/**` (ignored).
Scripts: `entry-check.py`, `behaviour-cases.py`, `behaviour-check.py`,
`behaviour-compare.py`, `spec-check.py`, `compare-verify.py`,
`line-endings-report.py`, `evidence-index.py`, `closing-check.py`. Data:
`entry-state.json`/`.txt`, `backup/` with `backup-hashes.txt`,
`behaviour-baseline.json`/`.txt`, `behaviour-comparison.json`,
`behaviour-compare.txt`, `verify-before/after.json` (+ exit codes and stderr),
`verify-after-precorrection.*`, `verify-comparison.json`/`.txt`,
`verify-structural.*`, `spec-check.json`/`.txt`, `diff-entry-to-current.txt`,
the pytest logs (`pytest-knowledge-{a,b,c}`, `pytest-construction`,
`pytest-combat-modular`, `pytest-ci-rest`, `pytest-staging-promotion`,
`pytest-new-suites-post`, `pytest-documentation`, `pytest-verification`),
`git-diff-check.txt`, the A/B evidence (`ab-backups-pytest.txt`,
`ab-artefact-counts.txt`, `ab-generate-*`, `ab-artefact-current/`,
`ab-artefact-entry/`), the pre-edit red state under `red/`, `generate-web.txt`,
`closing-check.json`/`.txt`/`.exit.txt` and `evidence-index.txt` (sizes and
SHA-256 for every retained file).

Next action for the coordinator: decide the `sources/2B` mirror path expansion,
confirm the two specifications and the three attributable diffs, re-run the
maintained verification at a session budget you control, then route the five
inherited failures above (sections 6.4 and 8) and record acceptance.
`docs/knowledge/2a2b/README.md` is **not** part of this lot's reservation and
was not edited: the status cell of the R2/R3 row is the coordinator's to update
with the link to this delivery. F011, F012, F013 and T13 stay open; nothing was
accepted, committed or pushed by this lot.

## 10. Independent coordinator acceptance — 2026-10-01

**Accepted for the modular source-to-save correction.** F011 and F012 are
resolved within their stated local construction/save boundaries. This is not
T13/T14 certification or optimized-backend acceptance.

Independent coordinator checks, without restoring files into the shared tree:

- Matched all five original backups to the dispatch hashes; reviewed the exact
  17-line compiler insertion and compared parsed canonical documents against
  originals with only the authorized runtime changes applied. `selection.py`
  and `contracts.py` remain byte-identical to their dispatched versions.
- Reviewed both staged mirrors against HEAD: only the same binding edits are
  present. The maintained `_promote_bands` invariant rejects differing published
  content. Accept these two necessary mirror writes as an explicit scope
  expansion; this does not authorize other staged edits.
- Re-ran the new construction/modular suites and staging-promotion suite:
  **65 passed**. Re-ran the maintained semantic cases for both specifications:
  **15 passed**, including mutation checks. Existing retained broad results are
  evidence from the executor, not additional coordinator reruns.
- Independently compiled six canonical controls: Fimir Warriors 5+, Young Nobles
  6+, Saurus 5+, Kroxigor 4+, Boglars regeneration 5+, Warpstone Troll 4+.
  Exercised 16 in-memory parameter probes: matching recipients reject booleans,
  floats, strings, missing values and out-of-range integers; excluded recipients
  retain 6+; valid endpoints 2/7 are accepted. No KB/cache mutation was used.
- A fresh maintained `verify --json` reproduces exactly the same 30 inherited
  error identities; structural complete with 1050 profiles, 565 verified and
  153 pending. No historical pin was refreshed.

Evidence and reproducer:
`build/cache/t13-parallel/profile-save-thresholds-coordinator-review/review.py`,
`independent-review.json`, `fresh-verify.json` and `coordinator-test-results.json`
(summaries of observed tool outputs).
The compiler/source hashes in that review identify the accepted production state.

Two reporting clarifications are incorporated into section 8: the `note_i18n`
failure is a catalogue test assertion, not demonstrated loader refusal; the
strict schema A/B log also reports unused `notes`/`notes_i18n` properties.
The five inherited failure classes are routed as **F042–F046** in the
[execution follow-up register](T13-execution-follow-ups.md).

The actual critical/no-save evidence is the modular real-attack test. The YAML
case named `critical-no-save-denies-the-save` instead uses Vomit Attack to prove
armour denial; its name does not establish a critical-chart witness by itself.
The correct critical witness passes independently in the modular suite.

The fire-weapon witness and incoming combined fire/magical-tag probe are accepted.
No canonical spell execution path was demonstrated; **F047 / T13.5** tracks that
remaining integration proof. Full verification-tree runs exceeded the executor's
budget, so no full-tree green result is claimed; F001 and T14 retain that gate.
F013, pilot reviews, optimized ports and phase closure remain separate.

The modular test basename change is accepted. The initiative reservation is
released after this review. No commit/push or agent launch was performed.
