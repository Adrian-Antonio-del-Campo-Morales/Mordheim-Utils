# Implement and verify rules

Prerequisites: [Architecture](../reference/architecture.md) and
[Verification](../reference/verification.md).

The modular engine is the rule reference. Its mechanics tests establish the
expected behaviour from written sources; conformance scenarios exercise the connected
KB/compiler/modular pipeline. Statistical parity compares NumPy and native
with that reference. The former semantic YAML runner and NumPy operation
adapters are retired; no parallel specification corpus is required.

## Implement combat behaviour

1. Identify the source clause, recipient, activation, boundaries and exclusions.
   Preserve its identity and consult [adopted rulings](../decisions/design-rulings.md).
2. Classify the effect as construction, modifier, local resolution or stateful flow.
3. Keep equipment/skill eligibility, variants and loadout prerequisites in
   [shared eligibility](../reference/eligibility.md). Use `mordheim_construction`
   for duel compilation, `mordheim_core.effects`, `mordheim_combat.phases` or
   `mordheim_combat.modular` for combat execution.
4. Reuse existing context preparation and phase operators. Inject `DiceSource`
   and `DecisionPolicy`; never consult global randomness or the UI.
5. Express the rule and its relevant limits in
   `tests/engines/modular/mechanics/`. Reuse exact frozen inputs where available.
   Do not substitute a similar fighter or weaken an assertion for a missing key.
6. Use the rules-conformance suite (`tests/conformance/`) for the connection from actual construction to
   observed modular results. Real compilation/eligibility and KB contracts
   belong in `tests/construction/` and `tests/knowledge/` respectively.

Tests should distinguish activation, non-activation, boundaries, consumption,
expiry and applicable interactions. Use explicit dice/decisions for local
results and short sequences for stateful timing. Expectations come from the
written source and adopted rulings, not from the current engine output.

`tests/engines/modular/runtime/` checks simulator contracts such as cancellation,
phase ordering, reproducibility, observation and parallel execution. It does
not replace the mechanics assertions.

## Use the development queue

```powershell
python tools/knowledge/clauses.py coverage --pending          # admitted clauses nobody covers yet
python tools/knowledge/clauses.py coverage --identity <id>    # one identity's clauses and references
python tools/knowledge/clauses.py check                       # unknown references, YES clauses under non-YES effects
python tools/mordheim-utils.py check report rules --output outputs/audit
```

The knowledge base is the queue. Every core rule, kept mechanic, implemented
item and `YES` rule effect is one obligation, split into `clauses: [{id, scope}]`
only when its printed text has several observable parts; the conformance corpus names
them through `audit_id`/`covers` and the deterministic suites through
`@pytest.mark.covers(identity, *clause_ids)`. `rules-inventory.csv` lists every
rule effect, mechanic and item with its scope, binding and `status`
(`covered`, `partial`, `uncovered`); filter it in a spreadsheet.

A coverage export is a structural snapshot of declared references, not executed
behavioural proof: the named scenarios and tests must still run and pass.
Export success means files were written. It does not certify mechanics, conformance
or statistical parity.

| Status | Next step |
| --- | --- |
| `uncovered` / `partial` | Author the missing conformance scenarios or mark the deterministic test that demonstrates the clause. |
| `covered` | Review the named evidence before changing the implementation; coverage is declared, not proven. |
| effect `implemented: NO` with YES clauses | Implement the complete admitted effect, reusing its binding family. |
| clause `YES` under a `NO`/`LATER` effect (`check`) | Reconcile the clause scope with the effect classification. |
| unbound effect | Its `reason` code says why (`pending-classification`, `out-of-scope.*`, `deferred.*`); the archived free text is in `docs/archive/reason-texts.csv`. |

Bindings and `implemented: YES` are declarations, not independent behavioural
proof. Planned bindings require explicit `implemented: NO`; active bindings
require scope `YES`. The structural audit checks binding references and default
profile construction, not whether each combat rule produces the correct result.

Never edit generated CSVs to close a rule. Change canonical declarations,
implementation or owned tests, then regenerate the relevant report when authorized.

## Record decisions

Keep permanent interpretations and their rationale in
[design-rulings.md](../decisions/design-rulings.md), with the exact source.
Historical references to retired semantic specifications are provenance, not
an instruction to restore the old runner. Preserve adopted decisions.

Use `TODO.md` for concrete unresolved defects and unanswered questions. A missing
source must be identified exactly; do not invent a rule. A source ambiguity,
a missing implementation and a failed test are different kinds of pending work.
A ruling by itself does not prove implementation or correct execution.

## Validate the owned change

1. Inspect existing mechanics, construction and conformance checks before adding another.
2. Run the smallest relevant checks only when execution is authorized. Test
   execution and broader integration/certification are separate scopes.
3. Check structural KB/contracts with `check verify`. Verification is structural
   only and does not run a semantic scenario corpus.
4. For optimized-engine changes, use the existing statistical scenario catalogue
   against the modular oracle when that verification is authorized. Do not add
   NumPy per-operation YAML adapters as another rule-authoring system.
5. Record the revision, selection, outcome and limits. A static check, collection,
   skipped native test or successful export is not a passing functional result.

A reusable reproduction should fail before the fix and pass after it, while
preserving unrelated behaviour. Broad batteries, benchmarks, generated data and
publication are not implied by a local rule change.

## Equipment and selection

The eligibility implementation lives in
`packages/typescript/domain/eligibility/index.ts`; Python uses its generated
bundle through `mordheim_construction/eligibility.py`. Do not duplicate the
rule tables in Python, campaign adapters or UI selectors. Follow the
[construction boundary](../reference/eligibility.md#construction-boundary-for-phased-implementation).

Construction tests should start from a valid build and distinguish the exact
restriction from unrelated failures. Cover legal alternatives, prohibited
choices and a neighbouring unrestricted recipient when relevant. A prohibition
must not pass merely because an item is absent from the equipment list.
Keep initial recruitment and later advances separate when the source does.

## Diagnose a failure

Reduce the failure to canonical data, construction, a phase, a short sequence
or the connected pipeline. Inspect the binding, compiled value, context,
resolver and state transfer. Compare with written sources, not the optimized
engine. Fix the narrowest responsible layer and preserve useful evidence.

## Local context and strict replay

Use `prepare_duel_context` for supplied identity, contact/distance and turn facts.
Missing required facts must fail rather than become guessed defaults. Use the
existing strict replay helper for focused whole-duel checks where useful;
backend draw orders are explicit, and equal seeds do not imply equal streams.
These helpers are not a replacement semantic YAML system.
