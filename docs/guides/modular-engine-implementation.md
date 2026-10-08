# Modular engine implementation — agent guide

## Purpose and governing scope

Complete admitted Combat Lab effects in the **modular engine first**, while
preserving the interpretation needed for later NumPy/vectorized and native
ports. Interpret each clause once; make that contract reusable rather than
implementing three uncertain versions simultaneously.

This is the active T13 implementation boundary. It complements the
[remaining T13–T15 work](../knowledge/2a2b/2A2B-Knowledge.md) and
[general implementation guidance](implement-and-verify-rules.md). Optimized
implementation and parity steps in general or historical guidance belong to
later, separately authorized porting batches. **Do not start those ports in a
modular implementation assignment.**

Combat Lab simulates **1v1 duels**. It shares KB and construction/eligibility
with Warband Manager, not campaign identities, services or battle state.
Preserve the adopted exclusions: group Rout/psychology and All Alone counting,
independent third fighters, map/terrain/weather, shooting and spell-casting
resolution, campaign acquisition, and escape/withdrawal that ends the duel.
An explicitly admitted individual consequence may be supplied without
implementing its external producer; environmental switches remain excluded.
Use the [permanent rulings](../decisions/design-rulings.md) for precise limits.

## Read before editing

Read the relevant sections, not the complete historical archive:

- [Architecture](../reference/architecture.md), [KB](../reference/knowledge-base.md),
  [eligibility](../reference/eligibility.md) and
  [verification](../reference/verification.md).
- Your dispatch: revision, closed origin/clause set, authorized paths,
  reservations and output. The
  [2A/2B consolidated knowledge](../knowledge/2a2b/2A2B-Knowledge.md)
  governs coordination; this guide launches no agents or reserves files.
- The accepted clauses in
  [T13-semantic-analysis.csv](../knowledge/2a2b/tasks/T13-semantic-analysis.csv),
  plus the scope, clarifications and remaining work recorded in the
  consolidated document. Unaccepted partials are review inputs, not approved
  implementation contracts.
- Applicable clarifications (section 4), permanent rulings, source definitions,
  bindings and consumers cited by the assigned clauses. Consult the open
  follow-up findings (section 6) where referenced.

Inspect the actual branch/worktree, applicable `AGENTS.md` and dirty files.
Preserve parallel work. A dispatch controls ownership; an isolated checkout
does not authorize extra families or optimized-engine edits.

## What an implementation batch includes

Finish each effect end to end, grouping genuinely similar contracts. Split
only for a source blocker, dependency or concrete implementation benefit.

| Layer | Authorized responsibility, within the dispatched paths |
| --- | --- |
| Canonical KB and editorial/runtime contracts | Correct source-backed identities, recipients, parameters and bindings. Preserve required staging mirrors. |
| Shared construction and eligibility | Reuse the maintained shared decision for legality, grants, variants and recipients; change it only for an actual missing contract. Do not duplicate it in Python or either UI. |
| Duel compilation and shared models | Carry the facts and effects the modular consumer actually needs. Shared data changes do not declare optimized support. |
| Modular contexts, phases, pools and state | Implement complete admitted behavior, choices, timing, resource consumption and expiry. Use existing `DiceSource` and `DecisionPolicy`. |
| Combat Lab product paths | Supply necessary selection/configuration inputs and honest support diagnostics so the dispatched effect can actually be used. |
| Focused evidence and maintained tracking | Verify the changed behavior and preserve reusable contracts, exact origin coverage and remaining gaps. |

**Excluded from this batch:** implementing behavior in `vectorized/` or
`native/`, extending their execution adapters, rebuilding the native engine
for new behavior, adding positive optimized parity claims, or certifying
T13/T14/T15. Small ports remain ports even when they change only one line.

Existing unsupported-backend refusals must remain effective. A strictly
necessary refusal/support declaration may be maintained only when its path
is explicitly included in the dispatch; it must not enable the new behavior
or introduce a hidden modular fallback. Otherwise record the precise support
gap for coordination. Never publish a new choice as usable on an unsupported
default backend.

## Manual semantic work and implementation

1. **Check the assigned clauses manually.** Read resolved source text and
   apply adopted rulings. Compare trigger, timing, consequence, recipient,
   duration, stacking and exceptions for every origin before reusing a family
   conclusion. Same name, binding or test expectation is not equivalence.
2. **Resolve contradictions before coding from them.** A test/specification
   describes the interpretation it exercises; passing it does not settle a
   conflicting source, an omitted choice or an untested exception. Locate the
   governing ruling or correct the contract from the source. Record a genuine
   unresolved meaning locally and continue independent clauses.
3. **Trace the complete route.** Follow source → binding/grant → shared
   construction → compiled effects → modular consumer → observable result.
   Distinguish a missing connection from missing behavior. Reuse an appropriate
   existing effect ID and consumer; do not create another operator for an alias.
4. **Implement the complete admitted effect.** Preserve optional declarations,
   nominated attacks/targets, hand and hit provenance, once-only resources,
   interruption, recovery and expiry where the source requires them. Do not
   replace a player's choice with an arbitrary first attack because an existing
   fixture uses only that attack. Separate excluded clauses explicitly.
5. **Check composition.** Follow weapon, fighter and state contributions
   together. Verify resulting formulas, recipient filters and absence of double
   application. Save exceptions may depend on source: a skill save and an
   equipment save are not interchangeable merely because both are wards.
6. **Update only authorized records.** Agents may amend a reserved partial;
   the coordinator owns the maintained semantic CSV, shared states and
   reservations unless ownership is explicitly delegated. Generated audit CSVs
   are snapshots, not the place to store durable interpretation.

Scripts may serialize explicit decisions and check format, coverage, hashes
or references. **Do not use scripts, keyword classifiers, bulk helpers or
automatic defaults to decide scope, equivalence, clauses, intended behavior
or completion.** Mechanical checks cannot substitute for this manual review.

## Preserve the interpretation for later ports

Use the existing semantic CSV columns; do not create a report per effect,
another semantic schema or a parallel implementation-status register.

| Existing fields | Information that must remain usable by a porting agent |
| --- | --- |
| `origin_id`, `current_id`, `clause_id`, source provenance | Exact origins covered, successor links and printed clauses; retain all compound remainders and exclusions. Preserve the assignment's input fingerprint, and identify the implementation revision separately in retained evidence. Do not silently replace the analysis baseline after a KB edit. |
| `semantic_contract`, `parameters`, `conditions` | Backend-independent trigger, order/timing, consequence/formula, recipient, duration, stacking, limits and exceptions. Include player choices and what observable outcome distinguishes this contract from its variants. |
| `effect_id`, `relation`, `consumer` | Reused effect identity, exact equivalence/variant boundaries and concrete existing consumers. Put proposed future consumers in notes; do not cite an invented symbol as existing. |
| `dependencies`, `implementation_batch`, `notes` | Only real prerequisites; additional pending layers; relevant representation constraints such as per-hit versus per-pool state, save provenance, resource ownership or decision order. Note concrete port risks without designing speculative infrastructure. |
| `implementation_work`, `analysis_status`, `evidence`, `evidence_refs` | Independent interpretation, work and evidence states. Identify the modular boundary and any remaining product/data gap. Reference the small reusable cases actually run and their examined revision. |

Keep the final contract coherent: replace superseded conclusions rather than
appending a contradictory “spec settles this” sentence.
`implementation_work: none` does not certify every backend; record **optimized ports pending** for
new modular behavior. Inspection, declared metadata and executed evidence
remain distinct. Source fingerprints are provenance, not a certificate.

Where relevant, retain the logical dice/decision order, outcomes and resource
state in existing deterministic cases. Later ports should reuse that contract
and compare their real execution with the modular result; equal seeds or
matching compiled fields alone do not establish behavioral parity. A future
agent can consult the original source when needed without repeating the whole
classification study.

## Proportionate verification and completion

Reuse existing family tests and cases. Add only the small number of witnesses
needed to distinguish the changed behavior from a plausible error or an
important boundary. Prefer a phase-level check for a local modifier; use a
strict duel sequence when decisions, state, reactions or expiry require it.
Expected results come from the source/ruling, not from copying the implementation.

Run affected checks only: the relevant family cases and necessary changed
construction/contract/transport checks. For a KB, schema, bundle or generated
artifact change, use its maintained validator/generator. Full semantic,
construction, parity, coverage and mutation campaigns are separate integration
or certification work, not automatic requirements for every effect. Do not
refresh unrelated pins, budgets or expected totals to obtain a green result.

A family is ready for modular review when its admitted clauses have a real
canonical route, correct modular consumption, necessary product inputs and
focused evidence; blocked and excluded clauses retain explicit dispositions.
Review the complete owned diff for assumptions repeated across related origins.
Missing source or a concrete dependency blocks that clause, not unrelated work.

Deliver a concise handoff: changed families and origins, interpretation/ruling
used, modular behavior, focused checks actually run, remaining gaps, and the
location of reusable contracts/cases. Preserve unrelated failures as limitations.
Do not create additional temporary reports, claim other engines are implemented,
launch agents, integrate another agent's patch, commit or push without the
corresponding explicit authorization.
