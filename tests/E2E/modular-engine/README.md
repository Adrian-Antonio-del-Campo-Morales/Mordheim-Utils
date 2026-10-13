# Modular engine E2E tests

The independent test battery lives under the [implementation plan](plan.md).
The reusable support, modular combat loop, declarative corpus loading and
pytest collection, inventory reconciliation and a CI execution step exist.
The current milestone is source-derived corpus authoring: do not execute the
engine while its implementation is unfinished. New scenarios are authored from
scratch, with a single authorized exception: the one-time move of the already
developed pilot scenarios into their per-ID files (*Migrated pilot scenarios*
below). Declarations and empty files do not certify semantic coverage.

## Current files

| Path | Current role |
| --- | --- |
| `dice.py` | Local copies of strict dice, decisions, exact enumeration and the mismatch exception. |
| `runner.py` | Copied helpers plus a real-driver combat loop and checkpoint/event checks. |
| `corpus.py` | Declarative YAML corpus loading and structural validation. |
| `generate_skeletons.py` | Engine-free generator of one source-linked authoring scaffold per admitted ID. |
| `test_generate_skeletons.py` | Standalone unittest checks for generation, preservation, source drift and CLI behavior; no combat execution. |
| `__init__.py`, `conftest.py` | A local Python package named `mordheim_modular_e2e`, loaded for pytest from the hyphenated directory. |
| `test_runner.py` | Copied strict-support checks, helper smoke checks and real-pipeline runner proofs. |
| `test_cases.py` | Collects every declared scenario and runs it through the production pipeline; loader checks. |
| `test_inventory.py` | Reconciles the corpus with the audit register, prints the coverage report and runs the opt-in completeness gate. |
| `test_non_regression.py` | Compares the live corpus with the reviewed accepted-evidence reference set-wise, and demonstrates that the control detects a lost scenario, clause reference or identity. |
| `test_variants.py` | Proves that sibling scenarios share variant data through YAML anchors and that running or editing one variant leaves its siblings intact. |
| `evidence/coverage-baseline.yaml` | Reviewed accepted coverage evidence (identity, protected scenarios and their clause references) with the register revision it was accepted against. Read-only for the tests. |
| `cases/core`, `cases/mechanics`, `cases/grants` | One YAML authoring document per admitted ID, named from that ID by `generate_skeletons.relative_path()` and carrying that identity in its header. A file holds that ID's scenarios, or an empty scaffold body while the ID is unauthored; empty scaffolds contribute no collected scenarios or coverage. |

The pytest package loader avoids generic top-level `dice` or `runner` imports
and does not change production import paths. All copied support is local; it
imports production compiler, engine and domain types rather than importing the
old verification runner.

## Generate the authoring files

Run from the repository root:

```powershell
python tests/E2E/modular-engine/generate_skeletons.py --dry-run
python tests/E2E/modular-engine/generate_skeletons.py
python tests/E2E/modular-engine/generate_skeletons.py --check
python tests/E2E/modular-engine/test_generate_skeletons.py -q
```

The generator uses only the Python standard library, never the production
compiler or combat engine. Its checks use standalone unittest and the existing
YAML dependency rather than pytest collection of the runtime suite.

The generator uses explicit `clause_scope: YES` rows in the semantic register
and complete `core/`, `mechanic/` and `rule/` IDs. It creates one YAML authoring
file for each admitted ID. Every file starts at TODO. All new cases are authored
from scratch using the rule and accepted contract; the only exception is the
one-time migration of the pilot scenarios recorded under *Migrated pilot
scenarios* below, after which no older scenario is copied or referenced.
The body is `[]`; all guidance is commented, so no placeholder is
collected as a passing test. Rule IDs use bounded readable filenames with a
hash suffix to avoid collisions and long Windows paths; the full identity is
always retained in the header.

Comments copy the printed rule, recorded semantic contract and analysis state,
origin, parameters, conditions, dependencies and notes. Excluded clauses of an
admitted ID remain visible without becoming test TODOs. Pending analysis stays
pending; the generator does not decide interpretations, scenarios or outcomes.
Original record-level source fingerprints are preserved alongside separate
whole-file SHA-256 snapshots. They have different granularity and are not
compared as equivalent hashes. Missing sources retain a source-review TODO;
changes to the captured files or register definitions make existing scaffolds
stale on the next check. Register notes are context, not behavioral authority.

Search `# authoring_status: TODO` for IDs to author, or `# TODO[` for clause
work. Update authoring status manually as work progresses; the generator never
infers progress from older scenarios or `covers` declarations. Review the rule
and its required variants and replace the empty list with unique, independently
authored declarative scenarios. Only manual semantic review can justify
`authoring_status: REVIEWED`; execution status
remains separate and unexecuted during authoring.

Regeneration creates missing files only. It never rewrites existing comments
or scenario bodies, and never deletes retired files. Preserve the `audit_id`
and `scaffold_fingerprint` header when authoring. `--check` writes nothing and
returns exit 1 for missing, stale, conflicting or retired scaffolds; it checks
file presence, identity and snapshot integrity, not scenario bodies, semantic
sufficiency or engine behavior. Source changes require manual review of owned files before updating
their snapshot; there is deliberately no force-overwrite mode.

`--register`, `--knowledge-root` and `--output-dir` accept alternative inputs
and destinations for isolated generation checks. `--dry-run` previews missing
files without creating directories or files.

## Author by semantic family

Use family-based data generation for repeated contracts. Keep one YAML file per
audit ID and the existing loader and runner. This workflow adds no runtime
template language, new test framework or editorial register. The scaffold
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
| [verification/dice.py](../../../apps/combat-lab/mordheim_combat_lab/verification/dice.py) | `StrictDice`, `StrictDecisions`, `_NeedRoll`, `_PrefixDice`, `enumerate_exact`. |
| [verification/reports.py](../../../apps/combat-lab/mordheim_combat_lab/verification/reports.py) | `EvidenceMismatch`, placed in the local `dice.py`. |
| [verification/scenarios.py](../../../apps/combat-lab/mordheim_combat_lab/verification/scenarios.py) | `_plain`, `_lookup`, `_build`, `_state`. |
| [test_semantics.py](../../python/verification/test_semantics.py) | The five strict dice, decisions and exact-enumeration test functions. |

The dice classes, enumeration helpers, `_plain`, `_lookup`, `_build` and the five
copied test functions retain their original bodies. Module headers and imports
use local support and local `EvidenceMismatch`; the old verifier is not a
dependency. `_state` now delegates override normalization to `_apply_state`,
which the full loop applies to already initialized fighters. Additional checks
exercise the new real-driver loop and its validation boundaries.

| Source snapshot | SHA-256 |
| --- | --- |
| `apps/combat-lab/mordheim_combat_lab/verification/dice.py` | `b7437e6ae88b131cb50bc213e9b5bd7f4ce30fa73d2c3ce95bdb21f251d05740` |
| `apps/combat-lab/mordheim_combat_lab/verification/scenarios.py` | `621073679b00807f6feda8620c59e83a23a802fdcb9e0a04c3507828484079af` |
| `apps/combat-lab/mordheim_combat_lab/verification/reports.py` | `ff6e8658698ef6a2b90a674ad1006b6737e10bb7a84742d0a057c73cb373e761` |
| `tests/python/verification/test_semantics.py` | `c74c20bd00ff81d01e1d4f1f05c90af4c150cdebc1f5b117a7ea2966e75905bd` |

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
under `initial_state`. `duel_context` accepts the production `DuelContext` fields;
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
Case metadata such as `id` and `covers` is carried by the future corpus; this
loop does not certify requirement coverage or inventory completeness.

## Declarative corpus

Every `cases/**/*.yaml` document is a list of scenario mappings using the runner
vocabulary plus two corpus metadata fields:

| Field | Purpose |
| --- | --- |
| `audit_id` | The admitted `core/`, `mechanic/` or `rule/` identity that owns the scenario. |
| `covers` | Admitted clause ids of that identity that the scenario demonstrates. |

All other fields are exactly the runner's scenario contract (`fighters`,
`initial_state`, `duel_context`, `maximum_rounds`, `rolls`, `decisions`,
`expect_initial`, `expect_rounds`, `expect_final`, `expect_events`,
`expect_error`). Unknown
fields, a missing `audit_id`/`covers`, a missing assertion, a duplicate
`audit-ID::scenario-ID` and a non-list document all raise `CorpusError` naming
the file and the offending scenario. `corpus.py` validates structure only;
reference checking against the register belongs to `test_inventory.py`.

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
templating layer. `test_variants.py` verifies that the sharing is real (an alias
reaches the same object), that executing the whole corpus does not mutate a
shared declaration, that a sibling's result does not depend on the order its
siblings ran in, and that editing one variant leaves the others intact. Every
variant keeps its own identity, dice, decisions and expectations; sharing data
never shares an outcome.

## Inventory, coverage and completeness

`test_inventory.py` reads the canonical register
(`docs/knowledge/2a2b/tasks/T13-semantic-analysis.csv`) read-only. It requires
every scenario to name a registered identity, an admitted `core/`, `mechanic/`
or `rule/` identity and one of that identity's in-scope clauses; a shared
executable binding never admits an excluded clause.

`coverage()` and `report.render()` distinguish, per admitted identity, complete
coverage, partial coverage with its pending clauses, and no scenarios. Ordinary
runs reconcile the corpus and print that report (visible with `-s`). The strict
gate that fails on any admitted identity without scenarios or any uncovered
admitted clause runs only when `MORDHEIM_E2E_REQUIRE_COMPLETE=1` is set,
mirroring the existing `verify --require-complete` convention; there is no skip
or expected failure. This evidence is E2E coverage and never replaces the
maintained `semantic_status` of the reference suite.

## Accepted coverage evidence and the non-regression control

`evidence/coverage-baseline.yaml` is a reviewed test artefact, not another
editorial rules register. For every identity the corpus had already accepted it
records the protected scenario identities and the clause references each
scenario demonstrates, with the register revision it was accepted against. The
tests never rewrite it; extending it is a reviewed edit that follows the corpus
review.

`test_non_regression.py` compares that reference with the live corpus set-wise.
An identity, a scenario, a clause reference inside a scenario, or a clause that
left the admitted scope is a regression even when every total is unchanged, so a
reviewed scenario cannot be substituted by another one. A moved register
revision is reported rather than trusted, and every accepted clause is re-checked
against the register's current scope. An isolated control test doctors a corpus
to demonstrate that each kind of loss is detected.

The reference is deliberately separate from the opt-in global completeness gate:
the gate lists every pending identity and admitted clause and fails when
completeness is requested, while the reference only protects what has been
accepted so far and never claims completeness.

## Running the battery after engine completion

These commands belong to the deferred execution milestone. Do not run them
during family authoring, even to discover technical request keys or repair
fixtures. Use the engine-free structural validation described above instead.

The central repository launcher selects this battery with `tests --scope e2e`.
It runs pytest from the repository root with the current Python interpreter,
forwards pytest arguments and preserves its exit code:

```powershell
python tools/mordheim-utils.py tests --scope e2e -q
python tools/mordheim-utils.py tests --scope e2e -q -k 'core/combat-order'
```

The direct pytest commands are also available:

```powershell
python -m pytest tests/E2E/modular-engine -q                      # the whole battery
python -m pytest tests/E2E/modular-engine/test_cases.py -q         # the declared scenarios
python -m pytest tests/E2E/modular-engine/test_variants.py -q      # shared variant data and isolation
python -m pytest tests/E2E/modular-engine/test_non_regression.py -q
python -m pytest tests/E2E/modular-engine/test_inventory.py -q -s  # the coverage report
```

CI runs the battery and the non-regression control as separate steps so a
coverage loss is not hidden among unrelated E2E output.

## Deferred runtime validation

The following commands also belong to the later engine-execution milestone. Do
not run them during source-derived corpus authoring; use the engine-free
structural validation in *Author by semantic family* instead.

```powershell
python -m pytest tests/E2E/modular-engine/test_runner.py -q
python -m pytest tests/E2E/modular-engine/test_cases.py -k 'core/combat-order' -q
python -m pytest tests/E2E/modular-engine -q
```

Passing these checks proves the support, the full-loop paths and the declared
pilot scenarios they exercise. They do not establish complete per-ID coverage:
run `test_inventory.py -s` for the current reconciliation, and set
`MORDHEIM_E2E_REQUIRE_COMPLETE=1` to make the gaps fail.
