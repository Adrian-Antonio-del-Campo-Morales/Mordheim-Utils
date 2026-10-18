# Modular engine E2E test implementation plan

Problems encountered during implementation that agents cannot resolve are recorded in
[Remaining modular engine problems](../../../docs/knowledge/2a2b/REMAINING_MODULAR_ENGINE_PROBLEMS.md);
unresolved authority choices in
[Remaining human decisions](../../../docs/knowledge/2a2b/REMAINING_HUMAN_DECISIONS.md).
This document retains the authoring/execution procedure, not another issue queue.

Status: the file structure, reusable support copies, the full combat loop,
declarative YAML loader, pytest collection, inventory reconciliation, declaration
report and a CI execution step already exist. The pilot is a starting point for
source review, not proof of semantic completeness. The current assignment is to
author and review the complete corpus while the engine implementation is still
in progress. Execution against the engine is deferred until that implementation
is complete for the admitted scope. Previous passing runs do not constrain new
expectations or establish engine certification.

## Objective

Build an independent deterministic test battery in `tests/E2E/modular-engine`.
Use the full audit identity as the logical test identity, with independently
defined scenarios beneath it. Derive the executor inputs and expected initial,
intermediate and final observations from rule descriptions and accepted rulings.
Prepare all admitted IDs and applicable clauses for later execution through the
production compiler and modular combat pipeline.

The battery must distinguish scenario success from complete coverage of an ID's
required behavior. A finished battery can expose genuine engine defects;
certification additionally requires complete coverage and passing behavior.

This plan does not by itself launch agents or authorize changes to combat
semantics. The existing runner remains reusable infrastructure; completing the
test definitions does not require a working engine or a passing E2E run.

## Authoring philosophy and execution boundary

The rules are the behavioral specification. For each ID, read its complete
source description, applicable accepted rulings and clause relationships before
choosing configurations, initial state, context, dice, decisions and outcomes.
Include activation, absence, boundaries, exceptions, recipients, timing,
duration, resources and meaningful interactions where the rule requires them.

Do not infer intended behavior, expected values or required scenarios from the
current engine implementation, traces or existing passing tests. Author all new
semantic scenarios from scratch; do not copy, seed or reference older scenarios
in the generated authoring files. The single authorized exception is the one-time
migration of the existing pilot scenarios into their per-ID files (*Migrated
pilot scenarios* below); after it, no older scenario is copied or referenced.
Source-derived family models may be shared as described in *Family-based data
authoring* below; this does not authorize copying legacy expectations. Reusable
runner support remains independent of semantic case content. Consult the executor's documented input and
observation contract to encode a rule-derived scenario; technical field names
and request keys are adapter details, not semantic authorities.

Dice values and player choices must distinguish the source-defined behavior
from plausible errors. Assert event order where the accepted rule requires it.
Do not turn incidental ordering in the unfinished engine into a rule. If a
required fact or observation cannot yet be represented, retain the authored
semantic scenario and record the precise adapter gap; do not exclude the ID or
weaken its expectation to fit the current implementation.

During corpus authoring, do not execute the combat pipeline, runtime runner
proofs, E2E scenarios or engine fault probes. Validate fixture syntax, structure,
IDs, clause references, duplicates and parameter expansion without invoking the
engine. Static validation and semantic review are the acceptance conditions for
this stage. Engine readiness is not a prerequisite for writing another ID.

Distinguish these outcomes in delivery and reporting:

- A defined scenario has source-derived inputs and independent expectations.
- A reviewed ID has sufficient scenarios for all its admitted requirements.
- Static validation confirms fixture integrity, not correct combat behavior.
- An unexecuted scenario has no behavioral result; it is not a pass or a failure.
- A later executed scenario has an actual result at a recorded engine revision.

The current milestone is the complete authored and reviewed corpus, with any
genuine unresolved semantic decisions and adapter gaps explicit. Functional
validation and engine certification are a separate later milestone. Missing
engine behavior must never cause an author to delete a case, copy actual output
into its oracle, or mark it as an expected failure.

## Scope and governing sources

- Copy the necessary existing test helpers into the new directory. Record their
  source paths and source revision; the copies have their own maintenance and
  regression checks.
- Keep later execution independent of the old scenario runner. In phase 7, call
  the production compiler, `initialize_duel` and `resolve_round` as the system
  under test.
- Preserve complete `core/...`, `mechanic/...` and `rule/...` identities. A shared
  executable binding does not erase separate grants, recipients or parameters.
- Reuse canonical identity and scope definitions. Generated audit CSVs are
  reports, not an independent authority or a new editorial register.
- Preserve accepted interpretations and exclusions. Record ambiguous clauses
  as pending, and continue independent contracts.
- Keep excluded, deferred and unclassified identities visible with their reason;
  none constitutes a passing behavioral test.
- Defer engine defect reproduction to the execution milestone. Do not change
  expectations to match the engine or silently fix it as part of test authoring.
- This battery targets the admitted modular 1v1 combat scope. Nearby participants
  supply supported contextual facts; they do not acquire mutable combat states.

Relevant existing sources:

- [Semantic scenarios and adapters](../../../apps/combat-lab/mordheim_combat_lab/verification/scenarios.py).
- [Strict dice and decisions](../../../apps/combat-lab/mordheim_combat_lab/verification/dice.py).
- [Real-driver duel replay](../../../apps/combat-lab/mordheim_combat_lab/verification/parity/_replay.py).
- [Existing semantic specifications](../../specs/README.md).
- [Canonical runtime scope](../../../sources/knowledge/registry/runtime-scope.yaml).
- [Semantic clause register](../../../docs/knowledge/2a2b/tasks/T13-semantic-analysis.csv).
- [Permanent rulings](../../../docs/decisions/design-rulings.md).
- [Modular implementation boundary](../../../docs/guides/modular-engine-implementation.md).
- [Verification reference](../../../docs/reference/verification.md).

## Proposed layout

```text
tests/E2E/modular-engine/
  plan.md
  README.md
  __init__.py
  runner.py
  dice.py
  corpus.py
  conftest.py
  generate_skeletons.py
  test_generate_skeletons.py
  test_runner.py
  test_cases.py
  test_inventory.py
  test_non_regression.py
  test_variants.py
  evidence/
    coverage-baseline.yaml
  cases/
    core/
    mechanics/
    grants/
```

The local package is loaded by pytest as `mordheim_modular_e2e` because its
directory name contains a hyphen. `runner.py` and `test_runner.py` keep the
strict support checks and the loop proofs; `corpus.py` and `test_cases.py` load
and collect the declarative YAML corpus; `test_inventory.py` reconciles it with
the canonical register and prints the coverage report. `generate_skeletons.py`
creates one source-linked empty YAML authoring file per admitted ID. These
scaffolds contribute no scenarios or behavioral coverage; grant-to-recipient
cases still require independently authored concrete recipient builds.
`test_non_regression.py` compares the corpus with the reviewed
`evidence/coverage-baseline.yaml` set-wise; `test_variants.py` proves that
sibling scenarios really share declaration data and that running or editing one
variant leaves its siblings intact.

The declared full ID is authoritative; filenames only help navigation. One
logical definition per ID contains its requirements and scenarios. Shared
scenario data may be reused when the underlying contracts are actually equal.

## Per-ID authoring scaffolds

Generate the empty files mechanically from explicit admitted IDs in the
semantic register. Each header retains the full ID, printed rule text, recorded
contract and analysis state, admitted clause TODOs, excluded clause context,
origin, parameters, conditions, dependencies, notes and source fingerprints.
Missing sources and changes to captured snapshots require review; original
record fingerprints and whole-file hashes have different granularity and must
not be compared as equivalent values. Generation does not resolve
interpretations or invent expectations.

Every new file starts with `authoring_status: TODO`, `execution_status:
UNEXECUTED` and an active YAML body of `[]`. Do not include older scenarios or
references to them, except the one-time migration recorded under *Migrated pilot
scenarios* below. Authors work through the files and clause TODOs, deriving all
cases afresh from the governing rules. An empty file never counts as a
passing test or a covered ID. Keep authoring progress separate from later
functional results.

Use bounded readable filenames with deterministic hash suffixes where needed
for complete rule IDs and Windows paths. The full identity in the header is
authoritative. Generation must preserve every existing file; report stale,
conflicting or retired scaffolds rather than overwriting or deleting them.
Regeneration must not reset manually authored scenarios or review status.

`--dry-run` previews missing files; `--check` validates presence, identity and
source snapshot consistency without writing or invoking the engine. Scaffold
checks do not prove the sufficiency or execution of the scenarios later added.

## Family-based data authoring

Use the [family workflow](README.md#author-by-semantic-family) as the default
method for repeated contracts. Read the assigned inventory once, group IDs by
equivalent source semantics, derive and review the common scenarios once, then
expand member-specific data with a small temporary helper. Retain the existing
one-file-per-ID architecture and YAML vocabulary; do not introduce runtime
templates or another framework.

Confirm each ID's recipients, conditions, parameters, additional clauses and
exceptions before applying a family model. Preserve existing cases, headers,
identities and concurrent changes, including untracked files. Validate changed
files per batch and attempt one full corpus structural check at final handoff;
do not repeat unrelated generator checks or global sweeps for every member.
Source changes invalidate the affected comparisons and require review.

Common oracle reasoning may be reused only for equivalent contracts. Generation
does not prove per-ID sufficiency or automatically confer `REVIEWED` status.
Record source ambiguity, normative incompatibility and adapter gaps separately;
an unfinished consumer does not block definitions. Continue other resolvable
requirements and families without stopping at each batch. Execution remains
deferred, and progress reports stay short until the assignment's final handoff.

## Migrated pilot scenarios

The pilot scenarios were authored before the one-file-per-ID organization and
lived in a few grab-bag documents, some spanning several admitted IDs. Under an
explicit one-time authorization they were moved without semantic change into
their per-ID destination: the file `generate_skeletons.relative_path()` derives
from each `audit_id`, whose header identity must match. Multi-ID documents were
split; every field, sequence order, useful comment and clause reference was
preserved; anchors shared between the scenarios of a split destination were
re-declared inside it so no document depends on another; and each destination's
normative scaffold header was kept. The superseded grab-bag files were then
deleted so the loader never sees a duplicate `audit-ID::scenario-ID`.

This is the only exception to authoring from scratch. A moved scenario is
neither reviewed nor complete: it carries no behavioral result, and establishing
its interpretation or its ID's complete coverage still requires manual semantic
review.

## Scenario contract

Each ID definition records its audit identity, applicable source clauses,
accepted interpretation, rulings, dependencies, relevant source fingerprints,
and required behavior. Use existing `origin_id`, `current_id` and `clause_id`
relationships rather than inventing replacement editorial identities.

Each scenario declares:

| Field | Purpose |
| --- | --- |
| `audit_id` | Complete admitted audit identity that owns the scenario. |
| `id` | Unique scenario identity within the owning audit ID. |
| `covers` | Explicit requirement references intended to be demonstrated by this scenario; declaration alone is not evidence. |
| `fighters` | Production build inputs for `first` and `second`. |
| `initial_state` | Explicit state overrides applied once after duel initialization. |
| `duel_context` | Supported local facts, validated through the production context model. |
| `maximum_rounds` | Positive combat-phase execution limit. |
| `rolls` | Strict initialization and combat dice requests, values and sides. |
| `decisions` | Strict explicitly authored decisions. |
| `expect_initial` | Required observations before the first executed combat phase. |
| `expect_rounds` | Required observations after specific executed combat phases. |
| `expect_final` | Final state, phases executed and termination expectations. |
| `expect_events` | Optional ordered events required by the semantic or documented executor contract; an empty list asserts that no event occurred. |
| `expect_fighters` | Required observations on the compiled `first`/`second` build snapshot delivered by execution; the harness computes no armour or rule values itself, and it is incompatible with `expect_error`. |

The existing runner vocabulary is the encoding baseline. Phase 1 identifies
required contract extensions from the rules. Invalid field names, duplicate
identities and unknown requirement references must fail static validation.
Validate observation paths against the documented contract where possible;
runtime path resolution is checked in the later execution milestone.

Contract note (E07 revision, 2026-10-14): the harness class needs no new
vocabulary field. Lasting fire state (`on_fire`) is declared under
`initial_state.<side>` and observed through the state snapshots; the fire
recovery request keys (`round.<i>.<side>.fire.extinguish`, the governed S4
hit family) are technical protocol references. Still external, specified not
implemented: a pre-floor opponent-attack-pool observation (`state.<side>.pool_size`
and kin) is unavailable until the engine exposes the pre-floor fact behind an
exact signature; and no catalog id or harness build field produces
`attack.blessed` on an attacker's incoming effect. Both reach their consumers
without changing this table or case authoring.

The observation ledger also records attack outcomes and the combined order of
dice and decision requests. Declare event-order expectations where a contract
depends on a decision preceding a roll or another event.

`initial` means the prepared state after declared overrides. `rounds[0]` means
the result of the first executed combat phase. Each engine round is one combat
phase in an alternating player turn; it is not a complete pair of player turns.

For later execution, initialize fighters once, preserving initialization dice.
Carry the returned duel state unchanged into the next phase. Stop when the
engagement ends, a combatant is out, or the horizon is reached, according to the
reviewed combat contract and documented executor horizon. An expectation for an
unexecuted checkpoint fails.
Report the termination reason and number of phases actually executed.

Expected results come from accepted source contracts, reviewed tables or
independent formulas. Never generate the oracle from the engine being tested.

## Implementation phases

### Phase 1 — Inventory and test contract

Entry: implementation of this plan has been requested.

1. Inspect the checkout, applicable instructions, branch, worktrees, dirty files
   and existing file reservations. Preserve concurrent changes.
2. Record the entry revision and relevant fingerprints, including any included
   uncommitted source state.
3. Reconcile current audit identities with canonical scope and the semantic
   register. Preserve identity successions and original clause relationships.
4. Define the applicable requirements for each admitted ID: activation, absence,
   exceptions, boundaries, timing, duration, resources and relevant composition.
5. Finalize the scenario vocabulary, observation paths, status meanings and
   coverage aggregation rules. Identify adapter gaps from those requirements
   without consulting current engine behavior as a specification.

Deliverables: README contract, reproducible inventory comparison and requirement
references within the case definitions. Do not create another editorial CSV.

Exit: IDs and clause relationships are unambiguous; requirements have a source
or ruling; unresolved interpretation and unsupported scope remain explicit.

### Phase 2 — Independent infrastructure

Entry: phase 1 contract is stable.

1. Create the proposed package layout.
2. Copy strict dice, strict decisions, build conversion, state normalization and
   expectation lookup helpers as needed. Record their provenance in the README.
3. Add YAML loading, input validation and independent pytest parametrization.
   Generate source-linked empty per-ID authoring files with TODOs; do not seed
   them with the existing scenario corpus.
4. Collect scenarios as `audit-ID::scenario-ID`, preserving each individual
   result instead of stopping the entire ID after its first failure.
5. Add engine-free checks for malformed input, duplicate IDs, unknown
   requirements and observation declarations inconsistent with the documented
   contract. Do not use collection that imports or invokes combat as a substitute
   for static fixture validation.

Exit: the suite can collect valid definitions and rejects invalid fixtures with
specific diagnostics. No production combat behavior has been copied.

### Phase 3 — Source-derived pilot and oracle review

Entry: phase 1 contracts and phase 2 fixture encoding are available. Engine
implementation and passing runtime checks are not entry conditions.

Choose real IDs with accepted contracts covering:

- Basic attack, wound and injury flow.
- A save and its threshold boundaries.
- A charge-dependent effect.
- Acting order, including a suitable Shifty contract.
- Recovery and duration across multiple player turns.
- A once-only resource.
- A supported local context.
- A grant with concrete recipients and parameters.

For each scenario, derive the configuration, initial state, supported context,
dice and decisions from the source contract. Calculate expectations from the
rule, an accepted table or an independent formula. Record which observable
distinguishes the intended behavior from a plausible missing modifier, wrong
boundary, resource renewal or ordering error. This is manual oracle review;
engine mutation and execution probes belong to phase 7.

Author the new pilot entirely from the rules, independently of existing cases.
A `covers` label does not demonstrate a clause, and a successful isolated-phase
case or prior E2E run does not establish source conformity. A stacking scenario
must actually represent the multiplicity it claims, or retain an explicit
representation gap.

Exit: pilot expectations and meaningful variants are independently reviewed,
fixtures pass static validation, and missing executor capabilities are explicit.
Stabilize the format before scaling without requiring an engine run.

### Phase 4 — Parameterization from demonstrated repetition

Entry: the source-reviewed pilot format and contracts are stable.

1. Follow *Family-based data authoring*: group equivalent contracts and share
   explicit base configurations and variants for builds, equipment, participant
   position, charge facts, characteristics and decisions.
2. Add family templates only where the pilot demonstrates the same test
   contract, such as a threshold save or a conditional bonus.
3. Expand compatible IDs into their ordinary per-ID YAML files with a temporary
   authoring helper. Give every expanded variant a stable identity and visible
   dice, decisions, requirements and expectations; preserve existing work.
4. Select meaningful combinations rather than generating an indiscriminate
   Cartesian product. Include representative supported compositions.
5. Treat participant reversal as an explicit variant: transform its context,
   request keys and observations consistently, and do not presume symmetry.
6. Validate expansion, identity uniqueness and variant isolation without running
   combat. Expanded expected values must come from explicit data or independent
   source-derived formulas, never the engine.

Exit: at least two distinct IDs reuse each introduced family template without
losing their exceptions or parameters. Ordinary new scenarios need data rather
than a new Python test function. Special sequences can remain explicit cases.

### Phase 5 — Complete source-derived coverage batches

Entry: the scenario format is stable and the assigned sources and accepted
contracts are available. Unimplemented combat consumers are not blockers.

Cover every admitted ID, grouping by semantic contract: core mechanics; weapons
and defenses; skills and conditional effects; stateful mechanisms; grants and
relevant interactions. Follow semantic prerequisites and construction contracts,
not the current engine implementation order. Nearby context remains within the
admitted 1v1 scope.

For each batch:

1. Assign an explicit closed ID set and exclusive case-file ownership.
2. Map every applicable clause, variant and requirement to concrete scenarios.
3. Reuse a source-reviewed family model after checking each member's contract,
   recipient eligibility, conditions, parameters and additional clauses. Generate
   ordinary YAML declarations in batches; review distinct exceptions separately.
   Do not reuse legacy expectations as an oracle.
4. Review each clause's required behavior and its independent expected
   observations. Validate the focused batch statically; do not execute it.
5. Deliver reviewed scenario mappings, source provenance, unresolved semantic
   decisions and technical adapter gaps. Mark behavioral results as unexecuted.
6. Check source changes before accepting the batch; invalidate only the affected
   review when a relevant source or semantic dependency changed.
7. Continue to the next resolvable family within the assigned directory. A batch
   report is a short progress update, not the end of the directory assignment.

Exit per batch: all assigned requirements have reviewed definitions and static
validation results, or an explicit genuine semantic decision still needed.
A grant's scenarios cover concrete recipient configurations and conditions
separately from the granted mechanic's scenarios. An adapter limitation is
retained for later integration and never reported as an exclusion or a pass.

### Phase 6 — Corpus delivery, static reports and authoring gates

Entry: reviewed batches and explicit remaining gaps are available.

1. Produce a per-ID report separating declared clause references, reviewed
   scenario sufficiency, static validation, pending interpretation, exclusions,
   adapter gaps and unexecuted behavioral results. Do not call the union of
   `covers` references complete semantic verification.
2. Link definitions and review provenance to existing audit IDs without
   replacing the previous semantic verification status. Report relevant source
   fingerprints and review revision. Source changes must identify stale reviews.
3. Provide engine-free authoring checks for local use and CI. An E2E execution
   step already exists in the [CI workflow](../../../.github/workflows/ci.yml);
   alignment with the deferred execution boundary is a separate integration
   task. Editing this plan does not disable or change that step.
4. Make missing admitted IDs and missing required scenario definitions visible
   in the authoring completeness gate. Add a non-regression check for accepted
   scenario identities and ID/clause mappings, not merely total counts. Never
   conceal gaps with blanket skips or expected failures.
5. Validate static report aggregation, invalid-fixture diagnostics and gate exit
   codes without invoking the engine. Do not generate behavioral results during
   this milestone.
6. Document corpus authoring and the later execution handoff in the README.
   Preserve existing coverage budgets until a reviewed update is justified.

Exit: every admitted ID and applicable requirement has a source-reviewed test
definition, static validation is reproducible, and any unresolved semantic
decisions or adapter gaps remain explicit. Record the complete corpus as ready
for later execution only when those gaps have been resolved or precisely
delimited. Passing runtime tests are not an authoring acceptance condition.

### Phase 7 — Deferred functional validation and certification

Entry: engine implementation tasks are declared complete for the admitted
scope, the reviewed corpus is available, and required adapter gaps are resolved.
This phase must not run while the engine implementation remains unfinished.

1. Verify the reusable runner executes `compile_fighter -> initialize_duel ->
   declared initial state -> repeated resolve_round` through production code.
   Check supported nearby-provider compilation, single initialization, state
   persistence, observations, termination and strict dice/decision consumption.
2. Run the runtime runner proofs for incorrect expectations, extra or missing
   requests, ordering violations, missing checkpoints, early termination and
   lost state. Preserve the existing independent support rather than replacing
   the harness.
3. Align technical request keys and observation adapters with the documented
   executor contract. Any change to a semantic expectation requires a governing
   source or accepted ruling, not a mismatch with actual output.
4. Execute focused batches and then the full corpus, retaining actual
   per-scenario outcomes at the examined engine revision. Use proportionate,
   isolated fault probes where needed to verify semantic sensitivity.
5. Report behavioral failures and execution errors separately from authoring
   gaps. Preserve minimal engine-defect reproductions; do not weaken the oracle,
   delete unsupported cases or silently repair the engine within a test batch.
6. Integrate runtime results and explicit execution into CI and verification
   reporting. Require full reviewed coverage and passing behavior for engine
   certification; declared references and historical passing pilots cannot
   substitute for either condition.

Exit: reports distinguish corpus completeness from functional success, every
required scenario has an actual outcome, and defects remain visible. Only
complete reviewed coverage together with passing behavior establishes semantic
certification for the admitted engine scope.

## Ownership, dependencies and synchronization

| Responsibility | Owned paths | Start condition |
| --- | --- | --- |
| Infrastructure | Runner contract, dice, loading, parametrization and static validation | Phase 1 contract settled; no engine run required. |
| Case authors | Assigned YAML files and closed audit-ID sets | Source-reviewed pilot format stable; no engine completion dependency. |
| Semantic reviewer | Clause-to-requirement and expectation review | Accepted source contracts available. |
| Authoring integrator | Static reports, authoring gates, CI alignment and documentation | Reviewed definitions available. |
| Execution integrator | Runtime runner proofs, results and behavioral reporting | Phase 7 entry conditions satisfied. |

After the pilot, independent case batches may run in parallel when explicitly
assigned. The runner and schema have one owner. Shared-source or schema changes
must be coordinated before integrating further case batches. Inspect ownership
and dirty state before shared-file edits and each integration.

Each handoff includes entry revision, assigned IDs and clauses, authorized files,
dependencies, expected evidence and unresolved decisions. This plan itself does
not dispatch workers.

## Validation and delivery

### Current milestone: corpus authoring

Perform source-to-scenario review and engine-free validation only. Check YAML
syntax, supported declaration fields, full IDs, admitted clause references,
duplicate identities, explicit expectations, parameter expansion and variant
isolation. Check coverage reports against reviewed requirements; a list of
`covers` labels cannot replace review of the actual scenario.

Confirm that the validation path does not import or invoke the combat pipeline.
Do not assume pytest collection or an existing inventory command is engine-free
without checking its imports and fixtures. Isolate the static path where needed
and record that dependency as authoring infrastructure work.

The scaffold generator and its standalone checks are available now:

```powershell
python tests/E2E/modular-engine/generate_skeletons.py --dry-run
python tests/E2E/modular-engine/generate_skeletons.py
python tests/E2E/modular-engine/generate_skeletons.py --check
python tests/E2E/modular-engine/test_generate_skeletons.py -q
```

The accepted-evidence reference and the controls that protect it are also
available. Their pytest invocation belongs to the later execution milestone:
in particular, `test_variants.py` imports the runner and executes combat. During
authoring, compare scenario identities and clause references through the
engine-free corpus loading path without importing runtime test modules. Validate
the changed batch rather than repeatedly sweeping the entire corpus; attempt a
full structural check at final handoff and report unrelated concurrent failures.

`evidence/coverage-baseline.yaml` is a reviewed test artefact, not another
editorial rules register. It records, per identity, the accepted scenario
identities and the clause references each scenario demonstrates, together with
the register revision it was accepted against. The control compares it with the
live corpus set-wise and never rewrites it: a missing identity, a missing
scenario, a scenario that dropped a clause reference, or a clause that left the
admitted scope is a regression even when the totals are unchanged, so a reviewed
scenario cannot be substituted by another. Extending the reference is a reviewed
edit that follows the corpus review, never a generated side effect. The global
completeness gate stays separate: it still lists every pending identity and
clause and still fails when `MORDHEIM_E2E_REQUIRE_COMPLETE=1` requests it.

Current delivery includes the complete authored corpus, independent oracle
provenance, copied-helper provenance, reviewed requirement mappings, static
validation results, unresolved semantic decisions, adapter gaps and the later
execution handoff. Behavioral results remain explicitly unexecuted.

Authoring completion checklist:

- [ ] All admitted IDs and applicable clauses are accounted for.
- [ ] Required scenarios and meaningful variants have source-reviewed inputs
      and independent expectations.
- [ ] Static fixture validation passes without invoking the engine.
- [ ] Parameter expansion preserves stable identities and isolated variants.
- [ ] Reports separate declaration counts, reviewed sufficiency and execution.
- [ ] Missing cases, stale source reviews and semantic decisions remain visible.
- [ ] Adapter gaps and the execution handoff are explicit.
- [ ] Current authoring validation and CI alignment are accounted for.
- [ ] Concurrent work is preserved.

### Later milestone: engine execution

Only after phase 7 entry conditions are satisfied, use the runtime commands
below. These are deferred instructions, not current authoring checks:

```powershell
python -m pytest tests/E2E/modular-engine/test_runner.py -q
python -m pytest tests/E2E/modular-engine/test_non_regression.py -q
python -m pytest tests/E2E/modular-engine/test_variants.py -q
python -m pytest tests/E2E/modular-engine/test_cases.py -k 'core/combat-order' -q
python -m pytest tests/E2E/modular-engine/test_inventory.py -q -s   # prints the coverage report
$env:MORDHEIM_E2E_REQUIRE_COMPLETE = '1'
python -m pytest tests/E2E/modular-engine/test_inventory.py -q          # strict completeness gate
python -m pytest tests/E2E/modular-engine -q
```

The full gate must expose any remaining missing coverage. A selected passing
family does not imply complete reviewed coverage or a passing complete battery.
Run affected existing checks after runtime report or CI integration.

Later delivery adds actual per-scenario outcomes, the examined engine revision,
runtime runner proofs, behavioral failures, execution errors and minimal defect
reproductions. These results must not be invented during authoring.

Functional validation checklist:

- [ ] The independent runner exercises the production pipeline.
- [ ] The reviewed authored corpus is used without weakening its expectations.
- [ ] Initial, intermediate, final and relevant event-order observations work.
- [ ] Missing coverage, invalid fixtures and unconsumed requests fail explicitly.
- [ ] Reports distinguish coverage completeness from behavioral success.
- [ ] CI and local reporting include the intended E2E scope.
- [ ] Existing affected checks are validated and concurrent work is preserved.
- [ ] Defects, unsupported scope and pending decisions remain visible.

## Execution, review and resumption prompts

Authoring: complete the assigned source-derived definitions at the supplied
entry revision using the family workflow. Group equivalent contracts, review a
common model, generate member data into per-ID files and check individual
exceptions. Preserve concurrent files and accepted contracts. Stay within the
authorized paths, validate changed batches statically and continue all
resolvable families before final handoff. Do not read engine behavior as the
oracle or run combat to obtain expected values. An unfinished engine does not
block test definition; generation does not establish semantic review.

Review: check the source-to-clause-to-scenario mapping, independently derived
inputs and expectations, meaningful parameter variants, semantic sensitivity
and honest report status without executing the engine. Do not infer complete
coverage from scenario counts, `covers` labels or a binding alone.

Later execution: confirm phase 7 readiness, validate the real pipeline and run
the reviewed corpus. Preserve failures, report actual outcomes and distinguish
adapter errors from engine defects. Expected values change only with a justified
source contract or ruling change.

Resumption: inspect current ownership and source fingerprints, compare them
with the accepted handoff, preserve matching authored scenarios and reviews,
and continue the remaining assigned requirements. Check whether the active
milestone is authoring or deferred execution; do not introduce runtime checks
into an authoring assignment. Report changes and blockers without restarting
completed independent batches.
