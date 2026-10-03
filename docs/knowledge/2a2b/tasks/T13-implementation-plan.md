# T13 — Combat Lab implementation plan

This document expands [T13](T13.md). It is an implementation plan, not a
completion report or authorization to start work before its dependencies are
accepted. The [initiative checklist](../README.md) remains the sole source of
task status and file reservations. T14 independently validates the accepted
T13 delivery; T15 owns the final phase review and local commit.

Current execution routing after the accepted partial deliveries and eligibility
extraction is recorded in the [remaining T13–T15 plan](T13-T15-remaining-plan.md).
Read its 2026-10-02 efficiency revision for current priorities, complete
functional-family deliveries and user-launched external work. This document
retains the governing implementation contracts, not the old dispatch sequence.

Execution findings that cannot be resolved inside their originating step belong
in the [execution follow-up register](T13-execution-follow-ups.md), with evidence,
an accountable owner, a resume condition and a closure criterion. Consult it
before dispatching a lot and reconcile its entries before accepting that lot.
It supplements this plan without repeating its ordinary unimplemented obligations.

## Shared construction baseline — 2026-10-02

The [shared eligibility module](../../../reference/eligibility.md#construction-boundary-for-phased-implementation)
is implemented and consumed by Warband Manager and Combat Lab. T13 does not
rebuild T09 construction/validation or create Python eligibility rules. The
remaining T13.2 work separates three boundaries: reuse accepted F035 current
decision/adapter dispositions, supply missing source-backed KB/bindings, and
compile legal choices into actual combat effects. Runtime availability is not
tabletop legality; engine behavior belongs to T13.3–T13.6.

Old construction findings are not automatically outstanding implementation jobs.
F035's accepted per-finding dispositions govern any eligibility repair. The
user reports the separate shared construction-centralization agent is active;
reuse its actual handoff and preserve its ownership rather than dispatching a
second constructor. A reproduced shared
decision defect is repaired once in TypeScript with both consumers tested;
an effect projection defect is repaired in the Combat Lab compiler. Source
questions and existing exclusions keep their identities and authority.

## 1. Agreed objective and product boundary

Implement the included 2A/2B combat obligations in **Combat Lab**, with
deterministic evidence and equivalent behaviour in every applicable backend.
Use existing mechanics first; extend the responsible layer when the written
rule requires additional behaviour.

Combat Lab and Warband Manager are independent applications. Their shared
product input is the canonical KB, not campaign documents, services or state.
As of the user's 2026-10-01 extraction, they also share a pure
[equipment/skill eligibility implementation](../../../reference/eligibility.md).
Combat Lab calls its generated JavaScript through a local Python adapter; this
does not introduce campaign state or calls to Warband Manager services.
The Combat Lab path is:

```text
sources/knowledge
  -> knowledge loaders
  -> shared eligibility through the local Python adapter
  -> Python fighter/effect compilation
  -> modular / NumPy / native combat engines
  -> Combat Lab analysis, CLI and UI
```

Simulation inputs are configured combatants, simulation options, explicit
context, injected dice and decisions. Outputs are simulation outcomes and
observations. Identities refer to canonical KB entities or participants local
to the simulation. T13 must not introduce roster-row IDs, `member_ids`,
`battle_number`, campaign-file imports, campaign-service calls or a bridge to
Warband Manager.

The agreed extension is **the minimum explicit context needed for complete
coverage of the included T13 obligations**. Distances, terrain, charge facts,
contacts, nearby allies and opponent counts may be supplied where relevant.
The engine resolves the rule from those facts; it does not build an autonomous
tabletop, placement system or movement strategy.

The initiative's exclusions remain: deployment, hiding, shooting and battle
spell resolution. Preserve their rule text and concrete limitations. The
absence of an existing duel operator is not, by itself, an exclusion reason.
Acquiring a mutation or retiring a roster member belongs to Warband Manager;
the mutation's combat modifier or a simulated combatant's change of condition
may belong to Combat Lab. Separate these clauses without transferring product
state between the applications.

The user's parallel interface and language changes remain outside each lot's
ownership. T13.0/T13.1 entry records identify their historical revisions; each
remaining lot fixes its current inputs and preserves concurrent changes.
Implementing this plan does not authorize pushes, deployment or changes to `main`.

## 2. Required consultation material

Read the implementation procedure before designing new contracts. Consult
the specific source rules, existing consumers and specifications for each
mechanism; this table is the entry map, not a substitute for that tracing.

| Material | How it governs T13 |
| --- | --- |
| [Initiative coordination](../README.md), [T13](T13.md), [T14](T14.md), [T15](T15.md) | Dependencies, ownership, independent review, evidence and phase closure. |
| [T06](T06.md) and [effect matrix methodology](T06-effects.md) | Initial allocation, compound obligations, identities and accepted exclusions. The allocation is heuristic and must be reconciled clause by clause. |
| [T09](T09.md), [T10](T10.md), [T11](T11.md), [T12](T12.md) | Later dispositions and the accepted entry baseline. Audit transfers against the independent-product boundary rather than treating them as integration contracts. |
| [Implement and verify rules](../../../guides/implement-and-verify-rules.md) | Mandatory mechanism classification, layer ownership, context preparation, injected dice/decisions and regression procedure. |
| [Architecture](../../../reference/architecture.md) | Package boundaries, compiler responsibility and modular/NumPy/native ownership. |
| [Shared warrior eligibility](../../../reference/eligibility.md) | Maintained TypeScript decisions, Python fact projection/embedded runtime, bundle generation and direct/embedded validation. |
| [Verification](../../../reference/verification.md) and [develop/release procedure](../../../guides/develop-and-release.md) | Deterministic evidence, orchestration checks, coverage, mutation, certificates and proportional certification runs. |
| [Knowledge-base reference](../../../reference/knowledge-base.md), [KB modification guide](../../../guides/modify-knowledge-base.md), [editorial contract](../../../../contracts/knowledge-editorial-v1/README.md) | Canonical identities, explicit equivalence, data ownership, schemas and runtime metadata. |
| [Runtime classification](../../../../sources/knowledge/registry/runtime-schema.yaml), [runtime scope](../../../../sources/knowledge/registry/runtime-scope.yaml), [binding registry](../../../../sources/knowledge/registry/bindings.yaml) | Scope versus implementation, effect-level bindings, pending vocabulary and exclusions with reasons. |
| [Implemented canonical families](../../../../sources/knowledge/catalog/rules/implemented-canonical-families.yaml) | Existing shared families and their declared members. This tracker is not proof that a rule or backend is semantically verified. |
| [Execution contract](../../../../sources/knowledge/catalog/mechanics/execution.yaml), [close-combat mechanics](../../../../sources/knowledge/catalog/mechanics/close-combat.yaml), [item mappings](../../../../sources/knowledge/catalog/mechanics/simulation-mappings.yaml) | Available executable operators, parameters, triggers, applications, stacking and item-to-engine connections. |
| [Core combat rules](../../../../sources/knowledge/catalog/rules/core-combat.yaml), [resolution contracts](../../../../sources/knowledge/catalog/rules/resolution.yaml), [shared rule text](../../../../sources/knowledge/catalog/rules/special-rules.yaml) | Written semantics and existing numeric contracts. Follow referenced source text when an obligation restates another rule. |
| [Specification conventions](../../../../tests/specs/README.md), [phase contract](../../../../tests/specs/structural/phase-verification.yaml), [interaction policy](../../../../tests/specs/interaction-policy.yaml), [higher-order interactions](../../../../tests/specs/interactions.yaml) | Required case roles, consumers, sequence evidence, interaction risk and reviewed overrides. Consult the applicable files in `tests/specs/semantic/{rules,grants,interactions}/`. |
| [Permanent design rulings](../../../decisions/design-rulings.md) and [project backlog](../../../TODO.md) | Adopted interpretations and remaining product limitations. An unresolved source question must remain explicit. |

The executable inventory and reports determine current status. Do not rely on
old totals, a tracker entry, `runtime.implemented: YES`, or a prose statement
that a gate is complete.

### Product-boundary correction and remaining reconciliation

- The [product-boundary decision](../README.md#frontera-de-producto-vigente-2026-09-30) corrects T10/T11 withdrawal ownership. Earlier campaign-producer assignments are superseded; the withdrawal operation and its typed adapter remain internal to Warband Manager.
  Existing tests supply explicit roster IDs. The adapter has no production Web
  caller; detection and UI capture are not established by those tests and are
  not T13 obligations. Only comments and documentation change in this correction.
- Review all other T09–T11 transfers for the same issue. A clause describing
  combat is not automatically an instruction to implement campaign lifecycle
  or a complete warband battle in Combat Lab.
- `runtime-scope.yaml`, reference pages and the backlog currently describe
  movement, psychology and proximity as outside the duel runtime. Replace
  those blanket statements with the actual contextual support as it is
  implemented, retaining specific unsupported clauses.
- Revisit pending vocabulary such as `trait.spectral-touch` against current
  compiler and engine consumers. Registration or promotion alone does not
  establish execution.

This plan's independent-product boundary supersedes the conflicting handoff
language. Document corrections must not silently claim that previously
unimplemented campaign triggers have been completed.

## 3. Entry baseline and obligation reconciliation

After T12 is accepted and the parallel changes are settled, the coordinator
records the entry revision, relevant diff, reserved files, environment and
available backends. Separate failures already present at entry from failures
introduced by T13. The historical semantic errors recorded in T12 remain
identified for T14; a fresh entry baseline is still required.

Reconcile the full T06 obligation list, including secondary clauses of
compound effects, with later accepted dispositions and canonical KB targets.
Use later source-backed decisions to refine the heuristic allocation; do not
blindly add transfer counts or filter only an effect's primary destination.

Each obligation needs the following traceability:

| Field group | Required information |
| --- | --- |
| Identity and authority | Origin effect, canonical target, source/section/page where available, applicable ruling and allocation correction. |
| Behaviour | Clause, mechanism, recipients, activation, exceptions, phase, duration, consumption and observable consequence. |
| Inputs | Required context, dice requests, decisions and missing-source questions. |
| Existing support | Binding, compiler projection, real consumer, callers, specification, cases and demonstrated backend coverage. |
| Delivery | Owning lot, reserved files, applicable backends, acceptance cases, evidence revision and remaining limitation. |

Classify separately: demonstrated coverage, implementation required, evidence
missing, source decision pending, another product's responsibility, or an
agreed excluded system. Keep source ambiguity distinct from implementation
debt. Existing behaviour receives targeted revalidation when its source,
context or shared operator changes.

Reuse the existing inventory, rule report and verification infrastructure.
Keep detailed regenerated evidence under ignored output paths, and record
durable dispositions and a reproducible recipe in T13. The work must be
recoverable without depending exclusively on scripts or matrices left in
`build/cache`. Do not create a second audit framework or copy volatile totals
into maintained reference pages.

**T13.0 exit:** every candidate clause has a justified disposition, included
obligations have a mechanism and acceptance criterion, cross-product handoffs
are corrected, and source questions have explicit owners. A blocked source
does not stop unrelated lots, but it prevents closing its included obligation.

## 4. Implementation contracts and responsibility

Follow [Implement and verify rules](../../../guides/implement-and-verify-rules.md)
for every mechanism:

| Mechanism class | Owning responsibility |
| --- | --- |
| Eligibility and legal selection (existing) | Reuse shared TypeScript decisions for equipment/skill access, variants, recipients and loadouts. Repair only a reproduced current defect; prove direct and embedded consumers. |
| Combat compilation and activation | `mordheim_construction` projects facts/resolves profiles and turns legal selections and canonical bindings into characteristics, weapons and effects exactly once. Supported-effect diagnostics do not define legality. |
| Modifier/composition | `mordheim_core.effects`: explicit effect composition; no YAML, UI or campaign dependency. |
| Local resolution | `mordheim_combat.phases`: real hit, wound, save, injury or other local operator. |
| Stateful flow | `mordheim_combat.modular`: contexts, state, pools, reactions, rounds and duel sequencing. |
| Optimized execution | `mordheim_combat.vectorized` and `mordheim_combat.native`: the same agreed mechanism through their actual execution paths. |
| Product access | Combat Lab application/CLI/UI: catalogue availability, configuration and analysis, without duplicating rule resolution. |

Trace YAML -> loader -> shared eligibility (direct or embedded) ->
grant/selection adapter -> combat compiler -> prepared context ->
operator/sequence -> state -> observable result. Trace all callers, including
batch and process-pool paths, before changing a shared responsibility. Reuse
fitting operators and bindings; equivalence must be explicit and backed by
the source, not guessed from names.

### Minimum context and state

- Transport the canonical characteristics and classifications actually needed
  by an obligation, including Movement or Leadership when applicable. Keep
  existing positional construction APIs compatible. Custom builds must
  supply required facts rather than receive guessed statistics.
- Extend existing request/context boundaries only for facts demonstrated by
  the reconciled obligations. Context represents simulation facts, not
  campaign history or persisted rosters. Group or proximity effects can use
  explicit local participants/facts without autonomous group movement.
- Use the same context preparer in orchestration and verification. A required
  missing or contradictory fact produces an explicit validation failure; an
  irrelevant fact must not activate a rule.
- Keep transient conditions, resources and duration in simulation state.
  Define whether they last for an attack, combat phase, player turn or duel
  from the written rule. Retain the existing player-turn convention unless a
  reviewed mechanism requires a specific extension.
- Inject `DiceSource` and `DecisionPolicy`. The engine must not read global
  randomness, UI state or campaign services.
- Preserve existing duel semantics when new context-dependent mechanics are
  absent. An explicit charge/context path must not silently change the
  established context-free simulation contract.

### Compiled and observed interfaces

Any added compiled field must survive kernel planning, NumPy preparation,
native folding and native memory layout. Update capacity/compatibility checks
with the contract; a backend must not silently ignore a new field or tag.

Extend observations only enough to prove relevant outcomes: phase ordering,
attack results, wounds, conditions, resources, duration, decisions and logical
dice consumption. Observations are Combat Lab diagnostics and verification
outputs, not campaign events. Preserve ordinary counting/analysis interfaces
where their meaning is unchanged.

## 5. Lots, ordering and synchronization

| Lot | Implementation outcome | Exit evidence |
| --- | --- | --- |
| T13.0 — Inventory and documentation | Reconciled obligations, reused mechanisms, corrected product boundary and source decisions. | Complete disposition matrix and assigned lots. |
| T13.1 — Shared contracts and proof path | Minimum context/state/compiled contracts and sufficient deterministic observation for all applicable engines. | Contract tests, legacy compatibility and a small real-engine replay proof. |
| T13.2 — Shared-decision reconciliation and combat compilation | Reuse existing construction/validation. Reconcile old findings through F035, supply missing canonical facts/bindings and make legal profiles/choices reach combat mechanisms exactly once. | Per-finding current disposition; current bundle/direct/embedded evidence; recipient, absence and end-to-end compiled-effect cases. |
| T13.3 — Local combat resolution | Hit, wound, defenses, weapon profiles and local exceptions, including Spectral Touch. | Source-derived deterministic operator and real attack cases. |
| T13.4 — Stateful sequences | Priority, attack pools, replacements, reactions, consumables and expiry. | Minimal sequences proving timing, choices, consumption and continuation. |
| T13.5 — Psychology and proximity | Included fear, hatred, stupidity, immunity, leadership and proximity clauses using explicit simulation context. | Correct filters, thresholds, interactions and state changes. |
| T13.6 — Movement/charge and product access | Included movement, charge, terrain and action clauses; usable catalogue/configuration/analysis paths in Combat Lab. | Context boundaries, unchanged legacy runs and real product-flow checks. |
| T13.7 — Integration and delivery | Required cross-lot compositions, coherent data/documentation and exact T14 handoff. | Final obligation/case/backend reconciliation and reviewed diff. |

Group work by mechanism rather than implementing the same rule independently
for each warband. T13.1 precedes mechanisms that need its contracts; a local
mechanism with no such dependency need not wait for unrelated contextual
work. Product access can be checked once each mechanism's inputs are stable.

For each mechanism family: reuse source/rulings, author necessary cases,
implement the modular path and canonical projection/product connection together,
then port stable optimized consumers in coherent batches. Isolated fixtures may
support development while pending bindings remain unavailable in production;
acceptance still requires the canonical path and every applicable backend.
Never expose unsupported behavior on an optimized path merely because the
modular milestone passed. Data, implementation, tests and documentation belong
in one functional delivery; small follow-ups are bundled with their owner.

Only after the common mechanism is stable may NumPy and native work proceed
in parallel on disjoint files. Models, compiler, kernel, scope, verification
adapters and canonical data each have one owner per shared file. The
coordinator assigns and records reservations before any implementation;
semantic/data changes receive an independent review under the initiative
protocol. Negative mutations run in isolated fixtures/processes when needed.

### Spectral Touch pilot

Use `trait.spectral-touch` to prove the complete data-to-combat path. Establish
from the source the natural-hit-six trigger, immediate additional wound and
continuation of the ordinary hit. Explicitly resolve its relationship with
parry, saves, wound reactions, criticals and an already-removed defender before
coding; do not borrow another extra-wound rule's interpretation automatically.
Cover a natural six, a non-six, an automatic hit without a fabricated natural
six, absence of the grant and a relevant defensive/stateful composition.

## 6. Documentation and KB integration per lot

Documentation is part of each mechanism's acceptance, not a final cleanup.
Maintain the existing sources of truth:

- Rule runtime blocks and item mappings describe classification and executable
  connections. Split mixed clauses as needed under the existing contract.
- The family tracker and binding registry describe reviewed equivalence and
  vocabulary. Add or update members only when their execution is demonstrated.
- Semantic specifications keep source references, independent interpretation,
  questions/rulings, exact cases, interactions and behavioural mutations.
- Permanent rulings record new interpretations with lasting cross-mechanism
  impact. Preserve established critical, priority, turn and reaction decisions
  unless the written source justifies an explicit reviewed change.
- Scope, references, the implementation guide and backlog describe the actual
  contextual capability and remaining limitations. Distinguish supplied facts
  from behaviour the simulator computes automatically.
- T13 records allocation corrections, lot deliveries, tested revisions,
  commands, reproducible evidence and the T14 handoff. The initiative README
  remains the task-status authority.

Changing `registry/runtime-scope.yaml` changes the fingerprint checked by
**every** semantic specification. Schedule scope edits serially, review their
impact on all pinned assumptions and update `scope_digest` only after that
review. The existing source-digest refresher does not update scope pins; any
necessary tooling extension must remain small and report the exact reviewed
targets. Do not refresh unrelated source pins or suppress errors to obtain a
green report.

Keep T12's historical source mismatches identifiable for T14. T13 owns the
review of fingerprints legitimately invalidated by its own contract changes
and must leave no unexplained new mismatch. Refresh the entry baseline after
the user's settled edits rather than treating historical counts as current.

Canonical data changes require explicit file ownership. Preserve IDs,
variants, source text and staging. Use the existing normalization/promotion
procedure to keep applicable staging and canonical contracts consistent; do
not edit ingestion tooling merely to make a check pass. Regenerate affected
artifacts through their owner and generator, never manually. Shared-KB edits
receive targeted consumer regression checks where their contracts changed;
this does not introduce an application integration or reopen unrelated UI work.

## 7. Deterministic proof and backend certification

Apply the [current proportional-validation policy](T13-T15-remaining-plan.md#6-proportional-validation-and-progress),
revised 2026-10-03. The dimensions below describe mechanism-level proof at the
appropriate checkpoint, not a requirement to add multiple test layers for every
new item, skill or binding. Reuse existing evidence, add only uncovered or
risk-specific cases, and batch broad checks and external reviews over stable
deliveries. Required certification gates remain at their planned milestones.

Every included mechanism needs source-derived expectations and tests of:

- activation and non-activation, with correct and incorrect recipients;
- thresholds, limits and ties when applicable;
- accepted/rejected decisions and requests not made outside their condition;
- single consumption, repetition, expiry and recovery when applicable;
- an observable consequence through the real consumer, not just metadata;
- a relevant composition and all interactions required by the existing risk
  policy;
- a behavioural mutation detected by the evidence.

Use the smallest phase test or meaningful sequence. Declare exact rolls and
decisions, reject unexpected/unconsumed requests, and use exact fractions for
finite distributions. The modular engine is checked against the source; its
output does not generate expected values. Construction-only coverage does not
prove combat resolution.

### Native proof gap

The existing specification adapter path compares modular and NumPy execution.
T13 must extend that infrastructure to exercise the compiled native mechanism
deterministically when applicable. The native source contains a callback seam,
but the current duel driver initializes production RNG directly and some
draws bypass the seam. Audit and connect the required draw sites, including
initialization and charge, rather than treating callback existence as proof.

Compare identical logical dice and decisions, phase consequences and relevant
state. Normalize semantic roles where physical batch extraction order differs,
without hiding an extra or missing logical draw. Running the same seed in
engines with different RNG implementations is not deterministic equivalence.
Native adapters must execute compiled operators/sequences; calling the
modular engine from an adapter cannot certify the native backend.

Rebuild the extension through the existing package build procedure after
native source changes; do not hand-edit generated C/C++. Validate in a fresh
process and record source revision/hashes, build command, binary path/hash and
the backend actually executed. A field-count compatibility check alone does
not prove that the binary contains a semantic source change. Explicit native
execution must not pass through an unnoticed fallback or skipped test.

Applicability must have a technical explanation per mechanism/case. Shared
preparation can be proved once with backend entry-path checks; a runtime
mechanism supported by an optimized flow needs real evidence in that flow.
Unavailable backends or missing adapters remain pending and block their
required acceptance.

### Validation schedule

Use the relevant source review, mechanism and architecture checks during each
lot. Expand testing only when a changed shared contract invalidates more
evidence. Discover current arguments through `--help` before certification.
Use affected cases in the edit loop and accept each stable family with one
proportional coordinator review. Matching evidence is reused; another review
requires a real discrepancy, changed inputs or the T14 separation requirement.

Representative commands from the repository root:

```powershell
python tools/mordheim-utils.py doctor
python tools/mordheim-utils.py report rules
python tools/mordheim-utils.py verify --inventory
python tools/mordheim-utils.py verify --structural
python tools/mordheim-utils.py tests --scope construction -q
python tools/mordheim-utils.py tests --scope architecture -q
python tools/mordheim-utils.py tests --scope deterministic -q
python tools/mordheim-utils.py tests --scope native -q
python -m pytest tests/python/verification/test_semantics.py -q
python tools/mordheim-utils.py verify --json
python tools/mordheim-utils.py parity --require-complete
```

At stable engine-family/batch checkpoints, additionally run the existing coverage
gate, applicable engine-mutation catalogue and truncation certification in the
verification reference. Record exact seeds, selected pairs, budgets and
backend availability. Deep statistical runs remain targeted certification
work, not the ordinary mechanism-development loop or a substitute for exact
evidence. T15 owns the final integral gate; do not rerun unrelated Web suites
for every Combat Lab mechanism. This changes run scheduling, not required
coverage, semantic, parity or phase-closure standards.

## 8. Acceptance and handoff to T14

T13 is ready for independent validation when:

- every included obligation maps to a canonical source, implemented consumer,
  specification, cases and justified backend applicability;
- no included behaviour is backed solely by a marker, tracker or compiled
  field, and no required source decision is unresolved;
- logical dice consumption, decisions, timing, duration, resources and
  observable state agree in all applicable executable backends;
- new contextual support is usable from Combat Lab's own configuration and
  analysis paths, with legacy behaviour preserved;
- independence from Warband Manager holds in inputs, services, persistence,
  outputs and corrected task documentation;
- KB contracts, staging, scope, rulings and documentation describe the same
  delivered behaviour, with fingerprints reviewed and artifacts generated;
- historical failures are distinguished from new defects and pending native
  validation is never reported as acceptance.

Deliver the tested revision and exact diff, obligation/case/backend matrix,
source decisions, commands and exit codes, deterministic vectors, native
build identity, exclusions, limitations and released file reservations.
T14 checks this exact delivery and returns defects to the owning lot. T15
checks the final phase diff and creates the local phase commit after acceptance.
Do not mark T13 complete or create a phase commit merely because this plan
has been written.
