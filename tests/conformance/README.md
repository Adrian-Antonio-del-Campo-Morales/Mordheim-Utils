# Rules-conformance suite

This directory holds the rules-conformance suite and its conformance corpus:
declarative conformance scenarios, each owned by one admitted knowledge-base
identity, that the conformance runner executes with strictly scripted dice
through the production compiler and modular engine. Every expectation is
derived independently from the printed rules and adopted rulings.

| | Rules-conformance suite |
| --- | --- |
| Question answered | Does the KB -> compiler -> modular engine path follow the printed rules, clause by clause? |
| Oracle | The printed rules and adopted rulings (independent, source-derived expectations). |
| Dice | Scripted, strict (every roll and decision declared). |
| Unit of accounting | Admitted KB identity / clause (`audit_id`, `covers`). |
| Runs | pytest; in CI (two steps); launcher `tests conformance`. |
| Lives in | `tests/conformance/` |

The statistical comparison of the NumPy and native engines with the modular
engine is chartered separately in
[`tests/engines/parity/README.md`](../engines/parity/README.md); the map of all
suites is in
[Test suites at a glance](../../docs/reference/verification.md#test-suites-at-a-glance).

Unresolved defects and authority questions are recorded in the
[project backlog](../../TODO.md); accepted rule interpretations belong in
[Design rulings](../../docs/decisions/design-rulings.md).
This document retains the authoring/execution procedure, not another issue queue.

The reusable support, modular combat loop, declarative corpus loading and
pytest collection, inventory reconciliation and CI execution steps exist.
Source-derived authoring, semantic review and execution are separate stages.
Executing this suite is part of
[modular integration validation](../../docs/reference/verification.md#modular-integration-closure).
New scenarios are authored from scratch, with a single authorized exception:
the one-time move of the already developed pilot scenarios into their per-ID files (*Migrated pilot scenarios*
below). Declarations and empty files do not certify semantic coverage.

From the repository root, select this suite explicitly with
`python tools/mordheim-utils.py tests conformance -q`. During authoring, prefer
a single affected file or node ID; the complete corpus is a full-pipeline run.

## Current files

| Path | Current role |
| --- | --- |
| `execution/dice.py` | Local copies of strict dice, decisions, exact enumeration and the mismatch exception. |
| `execution/runner.py` | Copied helpers plus a real-driver combat loop and checkpoint/event checks. Every 50 checked scenarios it asks the eligibility JavaScript engine for a full garbage collection (`eligibility.collect_garbage`), which otherwise holds 150-190 MB of garbage per process. |
| `corpus.py` | Declarative YAML corpus loading and structural validation. `shared_corpus()` loads the real corpus once per process for every test module (read-only); `load_corpus(directory)` still loads a fresh copy. |
| `generate_skeletons.py` | Engine-free generator of one source-linked authoring scaffold per admitted ID. |
| `integrity/test_generate_skeletons.py` | Standalone unittest checks for generation, preservation, source drift and CLI behavior; no combat execution. |
| `__init__.py`, `conftest.py` | Load the directory for pytest as the local package `mordheim_conformance`, a stable import name that keeps support modules such as `corpus` and `execution.runner` out of the generic top-level namespace. |
| `integrity/test_runner.py` | Copied strict-support checks, helper smoke checks and real-pipeline runner proofs. |
| `integrity/test_cases.py` | Proves collected scenarios are real assertions: a wrong expectation and a mismatched refusal fail, and the loader rejects unknown fields, missing identity/observation, duplicates and a non-list document. |
| `execution/test_cases.py` | Collects every declared scenario and runs it through the production pipeline. |
| `integrity/test_corpus_contract.py` | Engine-free contract checks for `corpus.py` using synthetic documents; it imports no combat package. |
| `integrity/validate_corpus.py` | Engine-free structural report and CLI for the corpus, with exit codes `0` (integrity clean), `1` (integrity failure) and `2` (incomplete under `--require-complete`). |
| `integrity/test_inventory.py` | Reconciles the corpus with the knowledge-base clause inventory, prints the coverage report and runs the opt-in completeness gate. |
| `integrity/test_non_regression.py` | Compares the live corpus with the reviewed accepted-evidence reference set-wise, and demonstrates that the control detects a lost scenario, clause reference or identity. |
| `integrity/test_variants.py` | Proves that sibling scenarios share variant data through YAML anchors and that running or editing one variant leaves its siblings intact. |
| `integrity/removal_probe.py` | Rule-removal probe and CLI: re-runs each identity's scenarios with its rule taken away and reports whether the evidence depends on the rule (see *Rule-removal probe*). Executes the modular engine; reads, never writes, the corpus and the KB. |
| `integrity/test_removal_probe.py` | Self-contained checks that the probe tells discriminating, non-discriminating, inert and baseline-failing evidence apart. |
| `integrity/evidence/coverage-baseline.yaml` | Reviewed accepted coverage evidence (identity, protected scenarios and their clause references) with the clause-inventory digest it was accepted against. Read-only for the tests. |
| `cases/core`, `cases/mechanics`, `cases/grants` | One YAML authoring document per admitted identity, named from it by `generate_skeletons.relative_path()` and carrying it in its header. A file holds that identity's scenarios, or an empty scaffold body while it is unauthored; empty scaffolds contribute no collected scenarios or coverage. |

The pytest package loader avoids generic top-level `dice` or `runner` imports
and does not change production import paths. All copied support is local; it
imports production compiler, engine and domain types rather than importing the
old verification runner.

## Generate the authoring files

Run from the repository root:

```powershell
python tests/conformance/generate_skeletons.py --dry-run
python tests/conformance/generate_skeletons.py
python tests/conformance/generate_skeletons.py --check
python tests/conformance/integrity/test_generate_skeletons.py -q
```

The generator reads the knowledge base through `mordheim_knowledge.clauses`
and never imports the production compiler or combat engine. Its checks use
standalone unittest and the existing YAML dependency rather than pytest
collection of the runtime suite.

The generator uses the identities and clauses declared on the knowledge-base
records (`mordheim_knowledge.clauses.iter_identities`). For the conformance
kinds, admission is decided per kind: every `core/` identity is admitted; a
`mechanic/` identity is admitted unless it is listed under `mechanic_exclusions`
in `sources/knowledge/registry/runtime-scope.yaml`; a `rule/` identity (one runtime effect) is
admitted when the effect's own `scope` is `YES` or any of its clauses has
`scope: 'YES'`. One `rule/` kind is never admitted: a catalogue skill whose
record, effect and `mechanic` binding ids are the one same id prints the text of
`mechanic/<id>` rather than stating an obligation of its own, so its scenarios
belong to that mechanic (see *Identities and clauses* in
[the KB reference](../../docs/reference/knowledge-base.md)). An undivided identity (no clauses) is a single obligation.
`item/` identities are tracked by the knowledge base but are not conformance
kinds. The generator creates one YAML authoring file for each admitted ID. Every file starts at TODO. All new cases are authored
from scratch using the rule and accepted contract; the only exception is the
one-time migration of the pilot scenarios recorded under *Migrated pilot
scenarios* below, after which no older scenario is copied or referenced.
The body is `[]`; all guidance is commented, so no placeholder is
collected as a passing test. Rule IDs use bounded readable filenames with a
hash suffix to avoid collisions and long Windows paths; the full identity is
always retained in the header.

Comments list the clauses of a split identity with their scope and point at
the knowledge-base record that holds the printed text; the scaffold copies
nothing, so the knowledge base stays the single place to read and edit the
rule. What a scenario observes is written in the scenario's own comments: the
retired clause register's contract phrasing, which used to carry that sentence,
is a historical record in
[`docs/archive/clause-register/clause-contracts.csv`](../../docs/archive/clause-register/clause-contracts.csv)
and may be read for wording, never copied into the knowledge base.
Excluded clauses of an admitted ID remain visible
without becoming test TODOs. The generator does not decide interpretations,
scenarios or outcomes.

Search `# authoring_status: TODO` for IDs to author, or `# TODO[` for clause
work. Update authoring status manually as work progresses; the generator never
infers progress from older scenarios or `covers` declarations. Review the rule
and its required variants and replace the empty list with unique, independently
authored declarative scenarios. Only manual semantic review can justify
`authoring_status: REVIEWED`; execution status
remains separate and unexecuted during authoring.

Regeneration creates missing files only. It never rewrites existing comments
or scenario bodies, and never deletes retired files. Preserve the `audit_id`
header when authoring. An identity counts as present when a file is headed by
it or a scenario declares it, so a file may host scenarios of several
identities when the knowledge base splits one printed rule across effects.
`--check` writes nothing and returns exit 1 for missing or retired scaffolds
(a header identity the knowledge base no longer declares, or a file not at the
path its identity derives); it checks presence and identity, not scenario
bodies, semantic sufficiency or engine behavior. A scaffold of a declared but
unadmitted identity is kept, because its scenarios may document a `NO`/`LATER`
effect; when such a file is left with an empty body it carries nothing and is
retired by hand (thirteen `profile.natural-attacks` scaffolds were removed this
way on 2026-11-18, their behaviour evidenced by the sibling
`profile.equipment-restrictions` files). A changed clause contract is reviewed
in the knowledge base (`git log` on the record), not through a scaffold snapshot.

`--knowledge-root` and `--output-dir` accept alternative inputs and
destinations for isolated generation checks. `--dry-run` previews missing
files without creating directories or files.

## Author by semantic family

Use family-based data generation for repeated contracts. Keep one YAML file per
audit ID and the existing loader and runner. This workflow adds no runtime
template language, new test framework or second clause inventory. The scaffold
generator still creates empty files only; an authoring helper expands a
source-derived family model into ordinary scenario declarations.

### Inventory and establish the common model

Read the assigned directory once, including empty bodies, existing scenarios,
clause markers and authoring states. Group pending requirements by equivalent
semantic contract, not just binding or filename. Cache repeated source text and
documented adapter vocabulary during the session; revisit them when their
relevant source changes.

For each family, derive and review one model from the printed rules and accepted
rulings. List the required activation, absence, boundaries, exceptions, timing,
resources and interactions, as applicable. Define the explicit scenarios and
independent expected observations for those requirements. Check representative
IDs and every distinct contract variant before expanding the model. Existing
source-derived family models may be reused after this source comparison; a
legacy fixture or a passing engine run is not an oracle.

For each member ID, confirm the source contract and identify the data that vary:
recipient and non-recipient builds, grant selection, conditions, parameters,
initial state and any additional printed abilities. Treat extra clauses,
different restrictions and exceptions separately. One Fear test does not exhaust
a general Psychology immunity contract. Every admitted clause of the member ID
must remain accounted for, including clauses outside the common family model.

### Expand ordinary YAML declarations

Use a small temporary script with the existing Python/YAML tools to instantiate
the model for the compatible IDs. Keep helper files outside the repository when
only case files are authorized. Inputs and expectations must be explicit data or
independent source-derived calculations. Do not import or execute production
combat modules, probe request order or derive values from engine output.

Record the family model and source/ruling references in concise case comments.
Each generated scenario retains its own stable `audit_id`, `id`, `covers`, build,
dice, decisions and expectations. Transform request keys and observation paths
consistently with the participant positions and the documented adapter contract.
Use only meaningful variants, avoiding an unrestricted Cartesian product.

Generation must preserve the normative headers, fingerprints, existing scenario
identities, useful comments and accepted coverage. Fill empty bodies or merge
missing scenarios without overwriting existing work. Remove a top-level empty
`[]` when replacing it with a scenario list; never leave both YAML documents
joined together. Keep anchors unique and aliases self-contained in each file,
and isolate mutable generated data between IDs.

Before writing, compare the destination with the snapshot read by the helper.
If another author changed it, defer or merge after inspection rather than
overwrite it. Track actual writes, including untracked files; Git's list of
tracked files alone cannot establish ownership or preservation.

### Review exceptions and validate proportionately

Review the generated members for their ID-specific parameters and exceptions.
Common oracle reasoning is reviewed once per equivalent contract; recipient
eligibility, conditions, additional clauses and model applicability are checked
for every ID. Generation never advances an ID to `REVIEWED` automatically.

| Marker | Meaning |
| --- | --- |
| `TODO` | The requirement or ID still needs authoring. A file may already contain migrated scenarios. |
| `PARTIAL` | Some requirements have scenarios; remaining requirements or representation gaps are named explicitly. |
| `AUTHORED` | All applicable requirements are represented by scenarios; semantic review remains separate. |
| `REVIEWED` | Source comparison and scenario sufficiency have been reviewed for all applicable requirements of the ID. |

An absent consumer or `implemented=NO` does not itself block authoring an
admitted rule. Source ambiguity, normative incompatibility and a missing adapter
input or observation must be distinguished. Keep those gaps explicit and
continue independent family members and other families. New scenarios remain
`UNEXECUTED`; generation and static checks establish no behavioral result.

Validate changed files once after each batch: YAML structure, header identities,
unique scenarios, admitted `covers`, explicit expectations, parameter expansion,
status consistency and self-contained aliases. Use an engine-free loading path;
check its imports before use. Obtain a focused inventory from the assigned
directory. At final handoff, attempt one full corpus structural validation,
reporting concurrent or out-of-scope failures without repairing others' files.
Repeat checks only after relevant edits, failures or dependency changes. Do not
rerun scaffold generation tests for every case batch when their implementation
and inputs are unaffected. Source snapshot checks remain distinct from body
validation and require review when the sources changed.

A family batch is an internal checkpoint, not completion of the assignment.
Continue across the assigned directory until no resolvable requirements remain.
Send short progress updates with counts and specific gaps; reserve the detailed
inventory for final handoff. Report files with scenarios separately from counts
by authoring status, since a `PARTIAL` file may still have an empty body.

### Before recording a blocker

A `PARTIAL` note is a claim about what the code cannot do today, and nothing
re-checks it when the code changes. In the 2026-11-18/19 pass, every one of the
then-remaining PARTIAL blockers turned out stale or misclassified once it was
tested. So test the concrete claim before writing it: compile the build, run the
would-be scenario through `execution/runner.py::check_case`, and grep the engine
for the consumer. Record a blocker only when that probe fails. When probing
refusals, catch `ValueError` only: a mistyped profile id raises `KeyError` and
otherwise looks like a refusal.

Routes that settled blockers once believed impossible:

- An unengaged round inside the duel: a failed Danse Macabre test
  (`condition.danse-macabre-controlled`) clears `engaged` mid-round
  (`modular/rounds.py`), before that round's recovery and form checks. Herb Lore
  and The Bitten's reversion are authored this way.
- A non-Psychology Leadership test: the opponent's `mechanic.crude-belch-ogre`
  request calls `resolve_local_leadership` without `psychology=True`, while
  `mechanic.automatic-leadership` auto-passes after the psychology and fear
  short-circuits. This isolates automatic Leadership from Psychology immunity.
- A blessed attack: `condition.blessed-weapon` with
  `trait_overrides: {blessed_weapon_slots: [main]}` emits `attack.blessed`.
- Seeded state: `initial_state` accepts any `FighterState` field (for example
  `transformed`).
- A second attack for an Attacks 1 recipient: an off-hand weapon.
- Diagnostics: search `eligibility/index.ts` before calling one missing (for
  example "at most two mutations are allowed", "Big Bully may only be taken
  once").

A face that no legal build can reach is a disposition, not a gap. Examples: a
restriction vacuous in a one-against-one duel, a printed exception with no
recipient in the band's lists, or an exclusion enforced by construction (hired
swords compile from their own packages). Record it as such and author the file.
A rule pre-empted by a sibling rule of the same profile is `covered.elsewhere`
(the Poltergeist precedent in design rulings).

### New authoring backlog

When the knowledge base admits new identities, the completeness gate lists them.
`tools/conformance/backlog_batches.py` divides them into batches by printed-rule
group, route and effort (`--table`, `--batch <id>`, `--out <work-dir>` for probe id
lists). A unit is one printed-rule group, the uncovered rules that share a binding.
The mechanics of one printed source section form one family and are never split.
Triage the identities with a recorded blocker first; triage is a decision pass
(author, rule, or withhold with the blocker named). Batches own disjoint files and
may run in parallel. Verify each with `validate_corpus.py` (0 metadata
conflicts), the affected `execution/test_cases.py` selection and
`removal_probe.py --identities-file <ids> --show non-discriminating`.

### Hireling recipients

The hireling catalogue (`catalog/hirelings/`) is compiled through its own route and
the first hireling batch (psychology, 2026-11-17) fixed these conventions; the
`catalog--hired-swords--*` and `catalog--dramatis-personae--*` files under
`cases/grants/` show them in full.

- **Recipient build.** `collection: mordheim`, `band_id: hirelings.<hired-sword|dramatis-personae>.<grade>`,
  `profile_id: hireling.<kind>.<slug>`, `characteristics: {weapon_skill: 3, strength: 3,
  toughness: 3, wounds: 2, initiative: 5, attacks: 1}` (fixture facts; the printed
  Leadership stays). A `grant: profile` rule applies by itself, so nothing is selected;
  a `selectable` hireling skill is selected with `special_rule_ids: [<rule id>]` on the
  real profile. Omit `main_weapon_id` to take the printed kit's default; name a kit
  weapon when the kit lists a firearm first (pistols fire in close combat) or when the
  recipient's own wound matters. An active item outside the printed kit is refused by
  the kit resolver, so hand-built equipment is not an option.
- **Opponent.** Hand-built: `main_weapon_id: weapon.mace`, `characteristics: {weapon_skill: 3,
  strength: 3, toughness: 3, wounds: 3, initiative: 2, attacks: 1, leadership: 7}`, plus the
  one fact the rule reads (`trait_overrides: {causes_fear: true}`, `{species: orc}`,
  `{elf_kind: dark}`, `{creature_kind: undead}`, `{spellcaster: true}`).
- **Control.** The grade-1b Bard (`hirelings.hired-sword.1b` / `hireling.hired-sword.bard`,
  `main_weapon_id: weapon.dagger`, same fixture): a hireling without any psychology rule,
  compiled through the same route, so the request the rule removes (or the re-roll it
  grants) is shown present without it. For a selectable skill the control is the same
  profile without the selection.
- **Refusal.** The Bard with `special_rule_ids: [<rule id>]` and
  `expect_error: "special rule is not available to hirelings.hired-sword.1b"`. A rule of the
  Bard's own package is refused by the eligibility gate (`<band>/<profile>`), one of another
  package by the compiler (`<band>` only); the fragment is their common prefix.
- **Dice.** The strict tape is consumed in request order, not by key: declare the rolls in
  the order the engine asks (all hits of a side before its wounds; Lightning Reflexes strikes
  before the charger). Silence a side with `initial_state: {<side>: {attacks: 0}}`; a
  frenzied recipient doubles a supplied `attacks: 1`. Fear: `round.<i>.<side>.fear.charged.{0,1}`
  for the charged side, `.fear.charge.{0,1}` for the charger (a failed charge test ends in
  `termination_reason: disengaged`); observe `state.<side>.fear_hit_sixes` and
  `attacks.<n>.hit_target`. Hatred re-roll: `round.0.<side>.attack.0.hit.reroll`. Fear re-roll:
  decision `round.0.<side>.fear.charged.reroll`, then `.reroll.{0,1}`. A D3 die declares
  `sides: 3`. The profile's other printed rules add their own requests, which are declared
  with a comment naming the rule (the Djinn's powers are declined with
  `djinn-power.curse|luck: false`; Snorri needs `trait_overrides: {snorri_drunk_result: 3}`;
  Belandysh's Inconsistency rolls `characteristic.<stat>.<n>` when first needed; a dagger
  grants its target a 6+ save). A merge key (`<<: *recipient`) is overridden by an explicit
  `trait_overrides`, so restate companion traits when adding one.
- **Identity.** A hireling's combat identity is its profile's `combat_traits`; Fear and other
  effects come only from its printed rules. Five profiles do not compile today (`TODO.md`,
  *Hireling profiles that do not compile*): their identities stay `PARTIAL` with the blocker
  named and an empty body.

## Migrated pilot scenarios

The pilot scenarios were authored before the one-file-per-ID organization and
lived in a few grab-bag documents: `cases/core/critical-hits.yaml`,
`injury-states.yaml`, `order.yaml`, `parry.yaml` and `two-weapons.yaml`,
`cases/mechanics/defences.yaml`, and `cases/grants/warband-grants.yaml`. Several
of those spanned more than one admitted ID. Each scenario now lives in the
single per-ID file that `generate_skeletons.relative_path()` derives from its
`audit_id`, and the grab-bag documents were deleted so the loader never sees a
duplicate `audit-ID::scenario-ID`.

This move is a one-time, explicitly authorized exception to the "author from
scratch" rule above. It is a move, not a review: every field, sequence order,
useful comment and clause reference was carried over unchanged, anchors shared
between the scenarios of a split destination were re-declared inside it so no
document depends on another, and the destination scaffolds' normative headers
were preserved. A migrated scenario still carries no behavioral result and
establishes neither its interpretation nor complete coverage of its ID; only
manual semantic review can advance `authoring_status`.

## Copy provenance

Copied on 2026-10-08 from the working-tree snapshot at repository HEAD
`e06c183a84d9c69e8219a8242ee9cc8c1921c885` on branch `2A2B`.
The SHA-256 values identify the actual source-file bytes read during the copy;
they do not certify unrelated uncommitted work or future source revisions.

| Original source | Copied symbols |
| --- | --- |
| [verification/dice.py](../../apps/combat-lab/mordheim_combat_lab/verification/dice.py) | `StrictDice`, `StrictDecisions`, `_NeedRoll`, `_PrefixDice`, `enumerate_exact`. |
| [verification/reports.py](../../apps/combat-lab/mordheim_combat_lab/verification/reports.py) | `EvidenceMismatch`, placed in the local `execution/dice.py`. |
| Historical `verification/scenarios.py` (retired) | `_plain`, `_lookup`, `_build`, `_state`. |
| Historical semantic support tests (retired) | The five strict dice, decisions and exact-enumeration test functions. |

The dice classes, enumeration helpers, `_plain`, `_lookup`, `_build` and the five
copied test functions retain their original bodies. Module headers and imports
use local support and local `EvidenceMismatch`; the old verifier is not a
dependency. `_state` now delegates override normalization to `_apply_state`,
which the full loop applies to already initialized fighters. Additional checks
exercise the new real-driver loop and its validation boundaries.

The original semantic verifier has since been removed. This snapshot table and
the hashes below record historical provenance; the rules-conformance suite retains its own local runner
and does not depend on the retired files. The copied strict-support checks live
in `integrity/test_runner.py`.

| Source snapshot | SHA-256 |
| --- | --- |
| `apps/combat-lab/mordheim_combat_lab/verification/dice.py` | `b7437e6ae88b131cb50bc213e9b5bd7f4ce30fa73d2c3ce95bdb21f251d05740` |
| `apps/combat-lab/mordheim_combat_lab/verification/scenarios.py` | `621073679b00807f6feda8620c59e83a23a802fdcb9e0a04c3507828484079af` |
| `apps/combat-lab/mordheim_combat_lab/verification/reports.py` | `ff6e8658698ef6a2b90a674ad1006b6737e10bb7a84742d0a057c73cb373e761` |
| `tests/integration/test_semantics.py` | `c74c20bd00ff81d01e1d4f1f05c90af4c150cdebc1f5b117a7ea2966e75905bd` |

These are owned copies, not forwarding imports. Review relevant upstream helper
changes before applying them; preserve the independent support checks.

## State helper boundary

The full loop calls production `initialize_duel` exactly once, then applies
declared overrides through `_apply_state`. Initialization dice are preserved
in the same strict script as combat dice and are not repeated between phases.
`_state` remains a standalone helper that initializes one fighter and applies
the same normalization; the full loop does not call it.

`_plain` serializes dataclass fields. Snapshots also expose `first_player_turn`,
`initial_charge_flags` and the local ID of `active_participant`. The loop records
the combined order of actual dice and decision requests.

## Loop API and observations

`check_case(case, knowledge_root())` executes a strict scenario and returns its
observations after checking every declared expectation. It calls production
`compile_fighter`, `initialize_duel` and `resolve_round`. No combat operator is
implemented in the test harness.

Builds use `fighters.first` and `fighters.second`. Overrides use those same keys
under `initial_state`. A supplied `wounds` above the fighter's compiled maximum is
rejected: the engine would clamp it silently, so the scenario would assert a
different starting state than it declares. `duel_context` accepts the production `DuelContext` fields;
each nearby provider declares `participant_id`, `side_id`, a `fighter` build and
an optional supported `condition`. Production context validation remains active.

`maximum_rounds` is a positive integer and defaults to one. Each round is one
combat phase in an alternating player turn. Execution stops at the horizon,
when a combatant is out, or when the local engagement ends.

| Observation | Expectation field | Meaning |
| --- | --- | --- |
| `initial` | `expect_initial` | State after duel initialization and declared overrides. |
| `rounds[index]` | `expect_rounds[index]` | State and attack outcomes after that executed phase; index starts at zero. |
| `final` | `expect_final` | State, `rounds_executed` and `termination_reason`. |
| `events` | `expect_events` | Optional exact ordered list of roll and decision events. |
| `fighters` | `expect_fighters` | Compiled snapshot of the `first` and `second` builds. |

Initial and final expectations are nonempty mappings of dotted observation paths
to independent expected values. Intermediate expectations map zero-based
indices to such mappings. A round entry records the active participant during
that phase; its state snapshot records the active participant for the next
phase. Nonexistent paths or unexecuted checkpoints fail.

Termination reasons are `horizon`, `first_out`, `second_out`, `both_out` and
`disengaged`. Roll events contain `kind: roll`, `key`, `sides` and `value`;
decision events contain `kind: decision`, `key` and `value`.

`execute_case(case, root, dice, decisions)` is the lower-level observation API
for explicit injected sources. The normal test entry point is `check_case`,
which enforces complete consumption of strict scripts and requires an assertion.
Case metadata such as `id` and `covers` is carried by the conformance corpus; this
loop does not certify requirement coverage or inventory completeness.

### expect_fighters

`expect_fighters` reuses the compiled-build snapshot that `execute_case` already
returns; the harness computes no armour or derived rule values of its own. It is
a nonempty mapping of nonempty dotted paths (values that exist in the compiled
fighter snapshot) to independent expected values, compared with the same
pure assertion as every other observation channel, so a `True` expectation is
distinguished from the integer `1`:

```yaml
- audit_id: mechanic/armour.heavy-armour
  id: heavy-armour-shows-on-the-compiled-fighter
  covers: [validation-of-armour-fields]
  fighters:
    first: {collection: ..., band_id: ..., profile_id: ...,
            equipment: [heavy-armour]}
    second: {}
  expect_fighters:
    first.armour.roll_requirement: 5
    second.off_hand_id: null        # only paths that exist are legible
```

A case whose only observation is `expect_fighters` is legitimate — the
observation requirement is satisfied by that channel alone. It cannot be
combined with `expect_error`, which governs a refusal and forbids every
observation. Structural checks for the field (nonempty mapping, nonempty
dotted paths, first/second-only participants for the builds it observes) are
part of the loader's static contract; deferred runtime validation follows the
documented boundary for every other observation.

### Harness capacities and external dependencies (2026-10-14 contract revision)

Facts the runner vocabulary already admits may be declared or observed through
the existing channels without any new format; naming a lasting `FighterState`
field is declaring what the production model already carries, never injecting
an expected result. Two capacities matter for pending second-pass authoring:

- Lasting fire state: `on_fire` is a real `FighterState` field, so a
  scenario declares it normally under `initial_state.<side>` (a boolean, like
  every other supplied lasting state) and observes `state.<side>.on_fire`
  through `expect_initial`/`expect_rounds`/`expect_final`. The fire recovery
  phase exposes only protocol request keys — the extinguishing die
  `round.<i>.<side>.fire.extinguish` and the resulting S4 non-critical hit
  reaching the `attacks` ledger under that `round.<i>.<side>.fire.hit` family —
  documented strictly as a technical protocol: the concepts (whose fire state
  it is, which combat-phase attempts the recovery) live in the case, never
  thresholds, dice or results taken from an engine run.
- Compiled single-model projection pairs: `expect_fighters` observes the
  compiled fighter — `armour_save`, `helmet_save`, `characteristics.*` and the
  rule/gift tags the engine compiles — so an admitted printed quantity that the
  compiler already materializes is asserted by pair (bearer/bearer-without),
  never recomputed in the harness.

Still external (must be specified, never implemented here): an observation of
the opponent-attack pool *before* the printed minimum is not in any dataclass
nor in the runner output — a `state.<side>.pool_size` pre-floor path stays
impossible until the engine exposes that pre-floor fact behind an exact
signature (to its owner, with the signature and the assertion it unlocks), and no catalog id or harness build field materializes
`attack.blessed` on an attacker's incoming effect today. These
dependencies unlock their consumers without touching this vocabulary, so no
author re-authors for them in advance and no author fakes a pre-floor or a
blessed label into the state.

## Declarative corpus

Every `cases/**/*.yaml` document is a list of scenario mappings using the runner
vocabulary plus two corpus metadata fields:

| Field | Purpose |
| --- | --- |
| `audit_id` | The `core/`, `mechanic/` or `rule/` identity that owns the scenario. |
| `covers` | Only for an identity split into clauses: the clause ids the scenario demonstrates. An undivided identity is covered by any scenario naming it. |

All other fields are exactly the runner's scenario contract (`fighters`,
`initial_state`, `duel_context`, `maximum_rounds`, `rolls`, `decisions`,
`expect_initial`, `expect_rounds`, `expect_final`, `expect_events`,
`expect_fighters`, `expect_error`). Unknown
fields, a missing `audit_id`, a missing assertion, a duplicate
`audit-ID::scenario-ID` and a non-list document all raise `CorpusError` naming
the file and the offending scenario. `expect_events` may be the empty list; it
asserts that no event occurred. Observation maps are nonempty mappings of
nonempty dotted paths (checkpoint expectations included), `maximum_rounds` is a
positive integer that may not be a boolean, roll values are integers inside
die faces (no boolean values, nonempty keys, positive side counts), and
decision values are booleans.
`corpus.py` validates structure only;
reference checking against the clause inventory belongs to `integrity/test_inventory.py`.

`tests/conformance/integrity/validate_corpus.py [corpus_directory] [--require-complete]`
is the global structural report: it reuses the loader above plus the clause-inventory reading in
`integrity/test_inventory.py` (nothing from a combat package), reports integrity
(unknown references, duplicates, unloadable files), the authoring-metadata
grammar per file (`# authoring_status` markers vs. declared clauses), and the
declared coverage with its gaps. Retirement from the inventory is reported
separately, never mistaken for pending authoring. Exit codes: `0` when nothing failed (gaps
stay reported and do not pretend completeness), `1` on integrity problems, `2`
when `--require-complete` was requested and coverage is still incomplete.
Run it directly, engine-free, as a companion to the pytest contract tests;
do not patch a case's expectation because this report names it.

One scenario is one collected test whose identity is `audit-ID::scenario-ID`, so
a failure never stops its siblings. Parameterization is inline in the data: a
repeatable contract (a save threshold, a chart band) becomes one more scenario
with different rolls and expectations, not another Python test function.

### Evidencing a refusal

A scenario that must be *refused* declares `expect_error` instead of an
observation. It asserts that the declared build is rejected and that the
diagnostic names the authored reason fragment, so an unrelated failure cannot
satisfy it and a case that runs fails with `but the case ran`:

```yaml
- audit_id: rule/<collection>/<band>/<rule>/<binding>
  id: another-profile-of-the-band-is-refused
  covers: [whole]
  fighters:
    first: {collection: ..., band_id: ..., profile_id: necromancer,
            special_rule_ids: [<binding>]}
  expect_error: "special rule is not available to <band>/necromancer"
```

This is how an absent recipient is evidenced: an ineligible build must fail
rather than silently gain the effect. `expect_error` cannot be combined with
another expectation, and the loader rejects a blank value.

### Sharing variant data

Sibling scenarios share declaration data with the YAML features the loader
already supports — anchors, aliases and merge keys — rather than a second
templating layer. `integrity/test_variants.py` verifies that the sharing is real (an alias
reaches the same object), that executing the whole corpus does not mutate a
shared declaration, that a sibling's result does not depend on the order its
siblings ran in, and that editing one variant leaves the others intact. Every
variant keeps its own identity, dice, decisions and expectations; sharing data
never shares an outcome.

## Inventory, coverage and completeness

`integrity/test_inventory.py` reads the knowledge-base clause inventory
read-only through `mordheim_knowledge.clauses` (`load_identities`,
`declared_clauses` and `admitted_clauses`, built from the `clauses` declared on
every classified record). It requires every scenario to name a declared
identity, an admitted `core/`, `mechanic/` or `rule/` identity and one of that
identity's in-scope clauses; a shared executable binding never admits an
excluded clause. `python tools/knowledge/clauses.py coverage` prints the same
reconciliation together with the deterministic tests' `covers` markers.

`coverage()` and `report.render()` distinguish, per admitted identity, complete
coverage, partial coverage with its pending clauses, and no scenarios. Ordinary
runs reconcile the corpus and print that report (visible with `-s`). The strict
gate that fails on any admitted identity without scenarios or any uncovered
admitted clause runs only when `MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1` is set,
mirroring the existing `verify --require-complete` convention; there is no skip
or expected failure. This evidence is conformance coverage, not behavioural proof: the
scenarios must also run and pass.

## Accepted coverage evidence and the non-regression control

`integrity/evidence/coverage-baseline.yaml` is a reviewed test artefact, not another
editorial rules register. For every identity the corpus had already accepted it
records the protected scenario identities and the clause references each
scenario demonstrates, with the clause-inventory digest it was accepted against.
The tests never rewrite it; extending it is a reviewed edit that follows the
corpus review.

`integrity/test_non_regression.py` compares that reference with the live corpus set-wise.
An identity, a scenario, a clause reference inside a scenario, or a clause that
left the admitted scope is a regression even when every total is unchanged, so a
reviewed scenario cannot be substituted by another one. A moved inventory
digest is reported rather than trusted, and every accepted clause is re-checked
against the knowledge base's current scope. An isolated control test doctors a
corpus to demonstrate that each kind of loss is detected.

The reference is deliberately separate from the opt-in global completeness gate:
the gate lists every pending identity and admitted clause and fails when
completeness is requested, while the reference only protects what has been
accepted so far and never claims completeness.

## Rule-removal probe

A passing scenario does not by itself prove that it tests its rule: it may pass
equally with the rule removed, because its dice never reach the rule's boundary,
because another rule of the same setup already decides the outcome, or because
the KB delivers the same effect twice. `integrity/removal_probe.py` measures this
by re-executing every scenario of an identity with that identity's rule taken
away:

- `rule/` identities: when a build selects the rule (`special_rule_ids`) it is
  un-selected; otherwise the identity's effect binding is filtered out of
  `runtime_bindings` for the compiler and the eligibility engine, so the build
  compiles as if the KB did not bind that effect.
- `mechanic/` identities: the mechanic id is deleted from every id list of every
  build. When no list holds it — a weapon, armour, material or poison sits in a
  scalar slot such as `main_weapon_id` — the mechanic's `execution.yaml` entry is
  neutralised instead: the id still resolves, so the build stays legal, but the
  entry contributes no tag, bonus or flag. An entry that carries nothing but its
  own tag (most body armour, `material.normal`) delivers its effect from the item
  catalogue, which the probe does not substitute, so a scenario surviving its
  neutralisation is reported `inert`. Such a tag may still be read by another
  rule's operator (heavy armour by Armour Specialist); that evidence belongs to
  the other identity.
- `core/` identities are not probed.

| Scenario outcome | Meaning |
| --- | --- |
| `fails` | An `EvidenceMismatch`: a die, a decision, an observation or a declared refusal changed. |
| `refused` | The build is now refused by construction, so behaviour is never shown with and without the rule. |
| `survives` | The scenario still passes without the rule. |
| `inert` | The removal never reached a build: the scenarios never exercise the identity's KB grant (for example a hand-built fighter with the shared mechanic injected through `skill_ids`). |
| `baseline-fails` | The scenario already fails with the rule present; it is not counted. |

An identity is `discriminating` when one scenario `fails`, `construction-only`
when none fails but one is `refused`, `inert` when every scenario is inert,
`untested` when every scenario fails at baseline, and `non-discriminating`
otherwise. For construction rules (skill access, equipment restrictions) a
refusal is the rule's own effect, so `construction-only` is expected there.

```powershell
python tests/conformance/integrity/removal_probe.py                                  # whole corpus, about a minute
python tests/conformance/integrity/removal_probe.py --identity rule/mordheim/sons-of-hashut/band--hard-head/trait.concussion-immune --show discriminating
python tests/conformance/integrity/removal_probe.py --identities-file ids.txt --json outputs/removal-probe.json --show non-discriminating
python tests/conformance/integrity/removal_probe.py --fail-on non-discriminating      # exit 1 when any identity has that verdict
```

`--workers N` (default 4; `1` runs serially) uses forked worker processes.
`--json` writes every scenario outcome per identity.

Use the probe after authoring or repairing scenarios, and after a KB change that
moves where an effect is encoded. A `non-discriminating` identity needs one of
two things. If a legal build can reach the rule's boundary, it needs a better
scenario. If no build can isolate the rule, the KB encodes the effect twice and
should keep a single source: when an effect is legitimately delivered by another
rule or convention, mark it `covered.elsewhere`
(see [the KB reference](../../docs/reference/knowledge-base.md)); otherwise name
the duplicate in a dated `# Discrimination note` in the file header. A verdict
is measurement, never an oracle: do not change an expectation to satisfy the
probe, and do not count a probe run as conformance coverage.

## Derived artefacts

Two artefacts are derived from this corpus and owned elsewhere; neither is an
oracle for it, and neither is edited here.

- Parity deliveries in `tests/engines/parity/deliveries/`: each derived from one conformance
  scenario, keeping only the combat configuration (fighters, context, initial
  state, auxiliary participants, original `maximum_rounds`) with the scripted
  dice, decisions and expectations stripped. Its `source.sha256` pins the
  scenario's YAML bytes, so editing a conformance scenario makes its delivery
  `stale` until it is re-translated. A delivery is never proof of the original
  expectations; see the [parity charter](../engines/parity/README.md).
- The frozen engine corpus `tests/engines/fixtures/compiled-cases.json`, used
  for isolated engine development. Its entries keyed `conformance/<audit_id>/<id>`
  (`origin.kind: conformance`) keep their scripted dice and expectations; their
  `origin.path` records the export-time location as provenance. The suite still
  loads its own YAML and uses the compiler and knowledge base; it has not been
  replaced by that corpus.

## Running the suite

The suite runs in CI (see below). During source-derived family authoring, do
not run it to discover technical request keys or repair fixtures; use the
engine-free structural validation in *Declarative corpus* instead.

The central repository launcher selects this suite with
`tests conformance`; the `scenarios` subsection runs `execution/` (the declared
scenarios) and `integrity` runs `integrity/` (support, contract, inventory and
non-regression checks); a bare run selects both. It runs pytest from the repository root with the
current Python interpreter, forwards pytest arguments and preserves its exit
code:

```powershell
python tools/mordheim-utils.py tests conformance -q
python tools/mordheim-utils.py tests conformance scenarios -q -k 'core/combat-order'
python tools/mordheim-utils.py tests conformance integrity -q
```

The direct pytest commands are also available:

```powershell
python -m pytest tests/conformance -q                        # the whole suite
python -m pytest tests/conformance/execution/test_cases.py -q         # the declared scenarios
python -m pytest tests/conformance/integrity/test_variants.py -q      # shared variant data and isolation
python -m pytest tests/conformance/integrity/test_non_regression.py -q
python -m pytest tests/conformance/integrity/test_inventory.py -q -s  # the coverage report
```

CI runs the suite and the non-regression control as separate steps ("Run the
rules-conformance suite" and "Check accepted conformance coverage has not
regressed") so a coverage loss is not hidden among unrelated conformance output.

## Runtime validation

The same authoring restriction applies to these commands: do not run them
during source-derived corpus authoring; use the engine-free structural
validation in *Declarative corpus* instead.

```powershell
python -m pytest tests/conformance/integrity/test_runner.py -q
python -m pytest tests/conformance/execution/test_cases.py -k 'core/combat-order' -q
python -m pytest tests/conformance -q
```

Passing these checks proves the support, the full-loop paths and the declared
pilot scenarios they exercise. They do not establish complete per-ID coverage:
run `test_inventory.py -s` for the current reconciliation, and set
`MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1` to make the gaps fail.
