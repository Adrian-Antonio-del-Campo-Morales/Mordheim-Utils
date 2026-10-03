# T13.0 — Source reconciliation and entry baseline

This is the source review and work register for
[T13](T13.md), under the [implementation plan](T13-implementation-plan.md).
It records planning dispositions, not implementation certificates. The
[initiative checklist](../README.md) owns phase status and file reservations.
The [product boundary](../README.md#frontera-de-producto-vigente-2026-09-30)
applies throughout: Combat Lab and Warband Manager share KB data, not campaign
state or services.

Current ownership (2026-10-02): both products also consume the implemented
[pure eligibility module](../../../reference/eligibility.md#construction-boundary-for-phased-implementation).
This inventory's original support/candidate-file columns capture its examined
revision; references to Python selection/restriction paths identify retained
adapters, not permission to implement duplicate decisions. F035 reconciles
affected findings through current shared decisions and actual transport before
repairs are dispatched. Question/origin IDs and source dispositions remain;
an inventory construction clause does not mean the shared module is missing.

## Entry and ownership

- Entry revision: `eb85e954d36ebc257e32494d31fa6ea719c4253b`, branch `2A2B`.
  The local product-boundary corrections and implementation plan are part of
  the documentary entry; they have not been committed.
- T12 is accepted and its local phase closure exists. T13 starts with inventory
  and source review; no engine mechanism is implemented by this lot.
- The user's concurrent Warband Manager interface and language changes are
  outside this lot. No application, engine, KB, schema or semantic specification
  is edited by T13.0 while collecting this evidence. Concurrent Combat Lab
  changes observed in `ui/tabs/equipment.py` and `ui/tabs/weapons.py` are also
  preserved; they are not part of this lot's implementation or validation.
- Inventory may use the live canonical English source and record its hashes.
  Production acceptance must use a new fixed revision after the concurrent
  work settles. This entry is not a frozen production baseline.
- The coordinator owns this document, T13's delivery, the authored obligation
  register and the checklist. Source reviewers own disjoint ignored evidence
  files; their source, consumer and test reads do not authorize code changes.

## Consultation and identity rules

The procedure is [Implement and verify rules](../../../guides/implement-and-verify-rules.md):
classify construction, modifiers, local resolution and stateful flow; reuse
the responsible layers; share context preparation; inject dice and decisions;
then prove activation, absence, boundaries and consumption with real operators.

Read [T06's matrix methodology](T06-effects.md) together with
[T09](T09.md), [T10](T10.md), [T11](T11.md) and [T12](T12.md). Their totals
are historical allocations, not extra independent implementation obligations.
Resolve sources through the canonical band/catalogue records and T04/T05's
explicit promotion decisions. Follow `rule_ref` into the
[shared-rule catalogue](../../../../sources/knowledge/catalog/rules/special-rules.yaml).
Do not classify a blank local `effect` as missing text before resolving that
reference.

An origin effect is identified by **source file + owner record + effect ID**.
Effect IDs such as `trait.poison-immune` are shared by different source records;
deduplicating solely on an effect or binding ID loses recipients and source
obligations. Compound clauses remain one origin effect with distinct consumers;
the register must split their behavioural acceptance, not count the same source
again when another task transfers it.

Catalogue identities follow the existing tables in
[`staging_promotion.py`](../../../../packages/python/knowledge/mordheim_knowledge/staging_promotion.py)
and [`hireling_promotion.py`](../../../../packages/python/knowledge/mordheim_knowledge/hireling_promotion.py).
In particular, the Miracle Workers Priest of Morr, Warrior Priest of Sigmar
and Wolf Priest of Ulric keep the `-miracle-workers` variant IDs, including
their nested rule prefixes. They must not acquire the Town Cryer profiles'
rules through a name match.

### Historical candidate reconciliation

The accepted T06 matrix is joined by origin identity with the T09 clause
ledger and the T10 disposition ledger. All origin rows remain available for
review, including historical noncandidates, because a heuristic can miss a
combat clause as well as admit an excluded one.

| Historical input | Result of the identity join |
| --- | ---: |
| T06 origin effects | 1,692 |
| T06 clauses allocated to T13, after expanding compound lists | 784 |
| Distinct origin effects containing those clauses | 734 |
| T09 transfers to T13 | 32; 31 already present, 1 additional origin |
| T10 transfers to T13 | 137; 80 already present, 57 additional origins |
| Union of historical candidate origins | 792 |
| Other origins retained for false-negative review | 900 |

The historical union contains 613 band-rule effects, 81 items, 77 spells and
21 hireling-rule records. **792 is a candidate count, not the admitted scope.**
For example, spell resolution is still excluded even if a spell's text contains
melee modifiers. The 476 primary combat effects and 409 compound clauses cited
by earlier deliveries are different measures; neither adding them nor adding
the 32/137 transfers produces the current implementation scope.

## Verification baseline

Historical T13.0 baseline: the copied HEAD below was `eb85e95`, before the
snapshot commit `1b7f7cf`. The accepted [R0 source/fingerprint review](T13-source-fingerprint-review.md)
reconciles the current working/committed error sets and supersedes that split
for current routing. This table remains entry evidence, not present validation.

The existing verification and audit commands were run without refreshing
digests or editing specifications. A second run used a read-only KB copy
extracted from `HEAD`, keeping the engine and specifications identical. No
checkout, reset or restoration of the user's working files was involved.

| Observation | Working KB | KB copied from `HEAD` |
| --- | ---: | ---: |
| Structurally complete | yes | yes |
| Profiles compiled | 1,050 | 1,050 |
| Semantic obligations inventoried | 718 | 718 |
| Verified obligations | 171 | 563 |
| Pending obligations | 547 | 155 |
| Reported errors | 455 | 30 |
| Error category | source digest changed only | source digest changed only |
| Command exit | 1 | 1 |

Both semantic runs are incomplete. The isolated run reproduces the 30
historical source errors recorded by T12. The working tree has 321 parsed YAML
documents differing from `HEAD`; 301 differ only in `*_i18n` fields, and 20
also differ outside those fields. This comparison identifies entry drift; it
does not adjudicate or repair the user's concurrent work.

The working audit has 3,232 rows: 718 `YES`, 1,450 `NO` and 1,064 `LATER`.
Its review statuses are 171 `verified`, 510 `ready`, 37
`blocked_by_dependency` and 2,514 `not_applicable`. It currently reports no
`needs_ruling` rows. That does not mean the new contextual rules have no source
questions: existing semantic inventory excludes `NO`/`LATER` clauses, so it
cannot be the complete T13 source work list.

### What existing coverage demonstrates

| Existing resource or consumer | Reuse and limit |
| --- | --- |
| [`EffectSet` and compiled models](../../../../packages/python/core/mordheim_core/models.py), [`execution.yaml`](../../../../sources/knowledge/catalog/mechanics/execution.yaml) | Numeric modifiers, tags and many existing close-combat contracts. The ordinary characteristics contain WS/S/T/W/I/A, not Movement/Leadership or a battlefield context. Extend only what included clauses require. |
| [`compiler.py`](../../../../packages/python/roster-construction/mordheim_construction/compiler.py), [`selection.py`](../../../../packages/python/roster-construction/mordheim_construction/selection.py), [`contracts.py`](../../../../packages/python/roster-construction/mordheim_construction/contracts.py) | Legal construction, recipient selection and executable bindings. Automatic traits skip rules whose `runtime.implemented` is not `YES`; construction success is not proof of every printed rule. |
| [`core.effects`](../../../../packages/python/core/mordheim_core/effects.py) | Composition of executable effects; do not add YAML, campaign or UI dependencies. |
| [`modular/contexts.py`](../../../../packages/python/combat-engine/mordheim_combat/modular/contexts.py), [`phases.py`](../../../../packages/python/combat-engine/mordheim_combat/phases.py) | Real hit, wound, armour, special-save, injury and parry operations. Hatred already has a first-round reroll consumer; this does not implement all psychology, allegiance filters or nearby-leader rules. |
| [`modular/pools.py`](../../../../packages/python/combat-engine/mordheim_combat/modular/pools.py), [`rounds.py`](../../../../packages/python/combat-engine/mordheim_combat/modular/rounds.py), [`aftermath.py`](../../../../packages/python/combat-engine/mordheim_combat/modular/aftermath.py) | Attack allocation, replacement and timed reactions. Extend explicit state and consumption at their real orchestration sites. |
| [`DiceSource` and `DecisionPolicy`](../../../../packages/python/core/mordheim_core/dice.py) | Injected semantic rolls and choices. New tests must assert missing and excess consumption, not only a seed or an outcome distribution. |
| [`consumers.py`](../../../../apps/combat-lab/mordheim_combat_lab/verification/consumers.py), [phase contract](../../../../tests/specs/structural/phase-verification.yaml) | Locate actual phase consumers; update their classification when a new operator is integrated. A declared consumer is not itself behavioural evidence. |
| [Semantic specifications](../../../../tests/specs/README.md), [permanent rulings](../../../decisions/design-rulings.md) | Reuse source interpretations and tested mechanism cases, but revalidate a new grant's recipients and compositions. Preserve established poison, synthetic-hit, priority and recovery timing. |
| [Canonical family tracker](../../../../sources/knowledge/catalog/rules/implemented-canonical-families.yaml) | Lists shared implementation families, not an exhaustive per-source or per-backend certificate. No automatic equivalence inference from names. |

### Backend availability and proof gap

Python 3.10.6 can import the native extension, and `available_backends()` returns
`native` and `numpy`. The extension and kernel both advertise 55 effect fields.
Its binary SHA-256 is
`6eff7014bfc1e88df1b5daf1593ff273be4b4878f694fee3f14bda72370a4d38`.
It was not rebuilt or certified in T13.0; matching layout and successful import
do not prove that its sources and behaviour are current.

The existing [specification parity runner](../../../../apps/combat-lab/mordheim_combat_lab/verification/parity/_specifications.py)
classifies cases through shared construction or vectorized adapters. It does
not, by that route alone, exercise the native Cython operator. T13.1 must
establish strict replay and observable state for every applicable backend.
Inspect the callback and direct PCG draws in the
[native source](../../../../packages/python/combat-engine/mordheim_combat/native/_combat_native.pyx)
before claiming injected RNG works through the production native flow.

### Spectral Touch and Banshee probes

- `call-of-the-night-haint-mim/spirit-hosts` compiles with `weapon.fist`.
  Its printed `trait.spectral-touch` remains `implemented: NO`; the automatic
  trait path skips it, `TRAIT_TYPES` has no `spectral_touch`, and the compiled
  tags have no Spectral Touch grant. No execution consumer was found in the
  current combat engines. The existing compilation is not an implementation;
  the future representation should reuse tags/effect contracts where sufficient
  rather than presupposing a new numeric field.
- The [printed rule](../../../../sources/knowledge/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml)
  requires a natural hit six, one immediate additional wound, then ordinary
  wound resolution for the original hit. Before implementation, resolve and
  specify parry, saving throws, wound reactions, criticals and the already
  removed defender; do not copy Disease Dagger's interpretation automatically.
- `necrarchs-mou/banshee` is rejected by the existing explicit profile exclusion.
  It has no numeric Initiative in the source. A valid Banshee contract must
  represent the source faithfully, including its actual Cold Steel/Wailing
  rules, rather than inventing a statistic to pass compilation.
- Gyrocopter and River Boat retain the accepted vehicle/transport exclusions
  in [runtime scope](../../../../sources/knowledge/registry/runtime-scope.yaml).
  Their records do not supply an individual fighter statline.

## Planning dispositions and acceptance

The authored [obligation register](T13-obligations.csv) keeps every origin
identity, its canonical target and the source reviewers' dispositions.
Each entry separates combat, construction, campaign, excluded-system and
source-blocked clauses. Mechanisms are planning groups, not new executable
bindings or claims of semantic equivalence.

### Reviewed totals and register use

Three disjoint source deliveries reviewed 564 origins each. The coordinator
joined them by origin identity, checked exact coverage and canonical targets,
and challenged source-specific recipient, timing and resource constraints.
The follow-up review removed invented once-per-game limits, universal
standing-provider requirements and overbroad immunity assumptions. These
corrections change planning expectations, not execution or source data.

| Disposition | Origins | Meaning |
| --- | ---: | --- |
| `included` | 712 | Applicable local combat or its independent construction; includes existing mechanisms needing grant/recipient evidence. |
| `mixed` | 266 | Applicable combat/construction plus separately retained campaign, excluded-system or data clauses. |
| `construction` | 35 | Independent Combat Lab selection/grants; no additional local resolution clause in this disposition. |
| `campaign` | 354 | Campaign lifecycle; no Combat Lab service, persisted input or event. |
| `excluded` | 269 | Concrete agreed excluded system or accepted profile limitation. |
| `data-only` | 22 | Source/catalogue data without a standalone executable clause. |
| `source-blocked` | 34 | Missing/contradictory source or essential profile contract; recover it before admitting dependent behaviour. |
| **Total** | **1,692** | **Every original effect accounted for exactly once.** |

The 978 `included`/`mixed` origins contain 564 historical candidates and
**414 historical noncandidates** restored by full-clause review. They are not
978 new operators or certificates. The 35 construction rows are counted
separately; unresolved source rows must not be silently added to proved scope.
An origin can depend on multiple lots, so lot membership totals overlap:
T13.2 1,045; T13.3 458; T13.4 377; T13.5 476; T13.6 535. These memberships also
include preparatory construction/source/data work and are not additive scope.

Read the UTF-8 CSV with its header. Structured cells use compact JSON where
the review provided arrays/objects. Filter by `lots`, `disposition`,
`origin_owner` or `question_id`; retain `origin_key` when joining other reports.
`reviewed_text_sha256` identifies the reviewed canonical text, while the source
reference identifies the original material. Check recipient/runtime/reference
drift separately at each lot's entry; an unchanged text hash alone is not enough.

`existing_audit_status` is observed entry metadata, not this register's planning
scope. `reuse_evidence` identifies existing consumers, source/specification
pointers or an explicit missing-consumer trace. `responsible_layers` assigns
existing files for later extension; it does not assert that they already
implement the mechanism. All rows have `planning_only=true`. Per-clause
specifications, executable caller tracing and backend certification remain
implementation work.

An included or mixed combat clause must have a owning lot, required inputs,
timing and duration, dice/decisions, a concrete observable acceptance criterion
and a reuse/evidence pointer. A source block needs an exact question and an
owner. Do not replace either condition with a generic "duel unsupported"
exclusion. A missing test is implementation/evidence debt, not automatically
a missing-source question.

No row may declare an application bridge. Warband Manager owns recorded table
withdrawal and registered campaign participants. Combat Lab may independently
calculate an included Rout threshold or test from supplied local participants,
casualty weights, eligible Leadership providers and decisions. It produces a
simulation observation, not a table result, roster update or campaign event.
This does not introduce an autonomous full-warband battle. Local fear, All
Alone, Hatred, Stupidity, immunity and leadership/proximity clauses follow the
same boundary. Buying a mutation is campaign work; configuring its combat
effect from KB data is Combat Lab construction/combat work.

Mazzalupo Commands need source-specific treatment: the
[band rule](../../../../sources/knowledge/bands/mordheim/mazzalupo-web/special-rules.yaml)
and the `lore.commands` note in the
[magic catalogue](../../../../sources/knowledge/catalog/campaign/magic.yaml)
explicitly say they are not spells. Their included local morale, melee, movement
or escape effects do not require a general spell-resolution system. Preserve
the recovery-phase activation, difficulty roll, hearing/recipient restrictions
and one-command-per-participant limit; reconcile the common six-inch rule
against the individual command's explicit range before accepting cases. An
individual command whose only consequence is missile targeting stays excluded
with that concrete reason. File location alone does not decide scope.

The current runtime scope/backlog describe current duel capabilities. The
approved contextual extension in the implementation plan governs T13's future
scope; it does not mean those capabilities already execute. Keep current
runtime marks until the corresponding operator, production input path and
backend evidence exist. Mounted-only weapon modifiers that already use
`CompiledFighter.mounted` are distinct from a complete rider/steed contract.

The reviewed register is maintained planning material, not an auto-generated
audit or a runtime catalogue. Change a disposition only with source evidence;
when implementation reaches acceptance, add canonical specification and
backend evidence without deleting the origin trace.

### Assigned questions and dependent work

The initial T13.0 register recorded **185 distinct questions across 216 origins**;
current resolutions are recorded in the deliveries/follow-ups rather than by
erasing these planning identities:
79 source questions assigned to the coordinator and a designated KB source
owner, and 106 interpretation/contract questions assigned to the coordinator
and the dependent mechanism owner. Repeated source questions share a question
ID. Missing operators or tests alone are not source blocks. Questions on an
included/mixed record gate the uncertain clause; they do not certify its
behaviour or necessarily stop unrelated clauses of that record.

| Question/dependency examples | Work required | Dependent lot |
| --- | --- | --- |
| Q006/Q025 — Black Sheep/Crooked Moon Troll Stupidity; Q041 — High Elf Loremaster | Recover exact source references instead of copied Rat Ogre/Skaven or Necromancer/Liche text. | T13.2/T13.5; spell acquisition source only, casting remains X4 |
| Q037 — Bloated No Pain/Squishy | Resolve contradictory Injury transformations from the same source page. | T13.3 |
| Q019 — Spirit Host Spectral Touch; separate Spirit Knife Q146 | R1–R4 human-accepted; [permanent ruling](../../../decisions/design-rulings.md#spectral-touch-q019), F007 review and F008/L03 canonical activation complete at their modular boundary. [L06 separately reviews Q146](T13-local-weapons.md#spirit-knife-separate-q146-disposition) and activates the knife with its own recipients, weapon-local effect and save modifier; no inherited item certificate. Applicable ports remain L19/L20. | T13.3/T13.4 |
| Q018 — Ghostly Howl; Siren Song | Establish sampling, repeated-test/expiry and stacking contracts. | T13.4/T13.5 |
| Q066 — Banshee Wailing | Represent the printed priority and reach without inventing Initiative or suppressing the special attack. | T13.1/T13.4/T13.6 |
| Q127/Q147 — Field Trebuchet/Mortis Engine; mounted/companion questions | Recover actual component/profile and recipient contracts; retain accepted Gyrocopter/River Boat exclusions. | T13.2/T13.4/T13.6 |
| Q158 — Mazzalupo Commands, shared across five Commands | Reconcile common and individual range/recipient clauses before activation cases. | T13.4/T13.5/T13.6 |
| Equipment/save/reroll questions in the register | Recover named equivalences, variants, save stages and exact resource/decision ownership. | The row's assigned lots |

The CSV uses full identifiers `T13-Qnnn`; the abbreviated IDs above refer to
those rows. Resolve questions in the relevant existing specifications or
permanent rulings, with source evidence and a reviewed answer, then update the
planning row. Source repairs require the KB modification guide and exclusive
ownership. Do not request a blanket user ruling on all questions or invent a
rule to unblock a gate. Escalate only a concrete source ambiguity remaining
after consultation; independent mechanisms may proceed.

### Psychology source gate

The general [condition catalogue](../../../../sources/knowledge/catalog/rules/conditions.yaml)
cannot currently be treated as normative execution text. Its Fear summary
orders fleeing on a failed charged-by-Fear test; its Hatred summary adds a
compulsory-charge test and omits the first-combat-turn restriction. These
conflict with the original [Games Workshop rulebook, Leadership and psychology,
printed pages 22–23](https://broheim.net/downloads/rules/Mordheim%20-%20Part%201%20-%20Background%20%26%20Rules.pdf)
(consulted 2026-09-30): that Fear failure requires hit sixes for that round,
whereas Hatred rerolls misses in the first turn of each combat. Do not adopt
the erroneous summaries or silently refresh their semantic digests.

| Dependency | Source review required before the affected mechanism | Accountable owner |
| --- | --- | --- |
| `condition.fear`, `condition.hatred` | Restore complete charge-direction, failure and duration semantics from the primary rulebook; trace any affected references/specifications. | Coordinator; reserved KB source owner before T13.5 |
| `condition.cold-blooded` | The summary says two dice/discard highest; the canonical [Lizardmen source](../../../../sources/knowledge/bands/mordheim/lizardmen-lus/special-rules.yaml) explicitly says three dice/keep lowest two, with test/provider restrictions. Preserve the source variant. | Coordinator; reserved KB source owner before T13.5 |
| `condition.animosity` | Resolve the appropriate band's table and recipients; do not replace it with the catalogue's generic Leadership test. | Coordinator; reserved KB source owner before the Animosity lot |
| `condition.terror`, `condition.stubborn`, `condition.immune-to-psychology` | Recover specific authoritative variants and their exceptions; page-zero generic references do not establish a universal Mordheim rule or blanket immunity. | Coordinator; reserved KB source owner if an included clause needs them |

These are global source dependencies in addition to row questions. T13.0
records them without editing the KB. Corrections need exclusive file ownership,
the existing editorial procedure, affected-reference checks and source-backed
cases before implementation relies on them. Existing correct engine behaviour
must not be changed merely to match an incorrect catalogue summary.

## Lots and shared-file ownership

| Lot | Responsible owner | Reserved implementation families when activated | Acceptance before the next lot relies on it |
| --- | --- | --- | --- |
| T13.1 — contracts and proof | Coordinator | Core models/dice, compiled layout, context/state contracts, shared preparers and deterministic replay adapters | Existing duel compatibility, explicit local identities/context, no campaign state; a real modular/NumPy/native replay with correct choices and observable state. |
| T13.2 — shared-decision reconciliation and combat compilation | Coordinator, then assigned mechanism owner | Existing shared eligibility and its adapters; canonical grants, compiler projections, item mappings and catalogue access under exclusive ownership | F035 disposition of historical findings; reuse matching legal/illegal-choice evidence; prove exact recipients, no double grants, canonical loading and actual combat consequences separately. |
| T13.3 — local resolution | Coordinator; executor assigned at activation | Hit/wound/defense/injury/parry consumers and focused specifications | Activation, absence, threshold/tie, immunity/material filters and defensive composition on the real attack path. |
| T13.4 — stateful sequences | Coordinator; executor assigned at activation | Attack pools, replacements, rounds and aftermath; consumption/state projection and replay | Exact timing, chosen attack/target, once/expiry, interrupted or removed participants and remaining prepared attacks. |
| T13.5 — psychology and proximity | Coordinator; executor assigned at activation | Explicit recipient/opponent classification, Leadership tests, immunity and local-neighbour context | Thresholds and range boundaries, correct affected participants, permitted/forbidden actions and interactions with immunity/state. |
| T13.6 — movement/charge and product access | Coordinator; executor assigned at activation | Movement/action calculations from supplied terrain/distance/contact facts; Combat Lab catalogue/editor/analysis integration | Correct tests, failure and follow-up consequences; legacy input defaults; actual visible Combat Lab configuration and analysis workflow. |
| T13.7 — reconciliation and delivery | Coordinator | Cross-lot compositions, final KB/runtime documentation, reviewed obligation/spec/backend register | No lost source clause, no unproven implementation mark, applicable backends demonstrated, explicit source blocks and T14 delivery. |

These are ownership families, not simultaneous write authorization. The core
models, compiler, context preparers, phase operations, scope and each canonical
file have one active owner. Stabilize the modular contract before assigning
NumPy/native ports on disjoint files. The checklist records the actual reserved
paths before activation. Source blocks stop their dependent mechanisms, not
the whole phase.

T13.1 is the next implementation dependency for new context and replay. Local
mechanisms using existing contracts can be prepared independently. No lot's
assignment permits editing the user's Warband Manager interface or language
work. Changes to runtime metadata and scope wait for demonstrated behaviour.

## Evidence and reproduction

Ignored entry evidence lives in `build/cache/t13/`:

| Evidence | Purpose |
| --- | --- |
| `audit/rules-audit.csv` | Existing executable per-rule audit, not edited manually. |
| `verify.json`, `verify.stderr.txt` | Working-KB verification and diagnostics. |
| `verify-head.json`, `verify-head.stderr.txt`, `head-knowledge/` | Isolated HEAD-KB comparison, no mutation of the user's files. |
| `backend-and-pilot.json` | Environment, binary identity and focused compilation probes; not native certification. |
| `kb-entry-diff.json` | Parsed KB entry drift, separating translation-only and other differences. |
| `source-register.json`, `candidates.csv`, `summary.json` | Join of historical origin identities to live canonical sources, source/audit metadata and input SHA-256s. |
| `review-a.json`, `review-b.json`, `review-c.json` | Disjoint source review deliveries for consolidation. |
| `review-summary.json`, `delivery-validation.json` | Final reviewed totals, register SHA-256, exact origin coverage, canonical identities and documentary link checks. |

The authored register and this document retain the dispositions and methodology
if ignored evidence is removed. Recreate live audit/verification with existing
commands; the original inventory recipe is documented in T06/T06-effects.
Reapply the documented identity join and reviewed register rather than deriving
new dispositions from keyword matches. Temporary evidence scripts are not a
new production audit framework or a required runtime dependency.

```powershell
python tools/mordheim-utils.py report rules --output build/cache/t13/audit
python tools/mordheim-utils.py verify --json
```

For the HEAD comparison, extract `sources/knowledge` with `git archive HEAD`
into an ignored workspace directory and pass that directory to
`verify --knowledge <copied-KB-root> --json`. Keep current engine/specs identical
between runs. Preserve exit codes and the complete error identities; neither
run being structurally complete makes its semantic result complete.

At each future lot's entry, check whether canonical English, runtime metadata,
recipients or source references changed since this review. Revisit only
affected dispositions, then fix a tested revision after concurrent work settles.
Do not suppress a source change by blindly refreshing digests. T14 owns the
historical certification cleanup; T13 must supply evidence for its new behaviour.

## T13.0 exit conditions

- Every original effect is accounted for once by its origin key, including
  historical noncandidates checked for missed combat clauses.
- Included clauses have source-backed dispositions, concrete acceptance,
  mechanism/lots and required context; compound sources retain other consumers.
- Exclusions name the actual agreed system or accepted profile limitation;
  no generic movement/psychology/proximity exclusion or campaign bridge remains.
- Every unresolved source/contract question is identified, assigned and kept
  separate from ordinary missing implementation or evidence.
- Mechanism consumers, shared-file ownership, backend proof gaps and the entry
  drift are recorded without changing canonical implementation marks.
- The coordinator reviews the source deliveries and resulting register before
  accepting T13.0. T13 itself remains in progress for T13.1–T13.7 and T14/T15.

## T13.0 delivery — 2026-09-30

**Accepted as an inventory/documentation lot.** The 1,692 reviewed origins have
unique identities, canonical references, dispositions and planning acceptance;
included/mixed rows have inputs, timing, dice/decisions and assigned lots.
Unresolved questions have accountable owners and block their dependent clauses.
The entry evidence separates structural validity from semantic digest errors,
and native availability from native certification. No KB implementation marks,
engine code, specifications or concurrent interface/language files changed in
this lot. The authored register, links and documentary diff were checked.

Delivery checks passed: 1,692 unique rows equal the original identity set;
every canonical target resolves across 91 files; 114 local documentation links
and their fragments resolve; included/mixed acceptance fields and question
ownership are complete; documentary whitespace is clean. No referenced
canonical file changed between the captured review and this check. The
register SHA-256 is
`2a3b962e59bf65eba61191dffbf20f3fcdb44a68c7bc56863594913b20d9a6d6`.
The earlier live and HEAD semantic verification runs both returned exit 1
for source digest errors, as reported above; delivery validation does not
convert them into passing semantic certification.

T13.1 may start with shared context and deterministic replay contracts after
its files are reserved. It must use the preserved existing duel behaviour and
settled production entry; the Spectral Touch expectation cannot be finalized
until Q019 has a sourced, reviewed interpretation. T13.0 completion does not
close T13 or the open questions, and does not satisfy T14's semantic gates.
