# T13 semantic analysis — external agent coordination guide

## Purpose and boundaries

Study all effects admitted to Combat Lab's **1v1 duels**, including effects declared implemented. Identify equivalent behaviour, parameterised variants, compound clauses and reusable consumers. Analyse potentially relevant unclassified clauses explicitly; do not treat missing metadata as exclusion. Preserve explicit exclusions and existing rulings, and record scope conflicts instead of silently admitting deferred subsystems.

Combat Lab is independent of Warband Manager. They share KB and construction/eligibility contracts, not campaign participant identities or battle state. Construction legality belongs to the shared eligibility decision; duel compilation and modular execution have separate responsibilities.

This is an analysis task: **no rule implementation, KB/binding/engine changes, optimized-engine ports, full suites, parity, coverage, commit or push**. Preserve the 1v1 exclusions for group mechanics, independent third fighters, maps/terrain/weather, campaign acquisition and escape/withdrawal. An admitted individual consequence may be supplied without simulating its producer. Analysis does not certify T13 or T14.

This guide creates neither assignments nor reservations. **No agents are launched.** Before dispatch, the coordinator must publish the current inventory, manifest, four closed assignments, and explicit output-file reservations under the [initiative coordination protocol](../README.md). Historical dispatch manifests are evidence, not assignments for this study.

## Required reading

Read the relevant sections, not every historical report:

- [Architecture](../../../reference/architecture.md), [Knowledge Base](../../../reference/knowledge-base.md), [Eligibility](../../../reference/eligibility.md), and [Verification](../../../reference/verification.md).
- [Remaining T13–T15 plan](T13-T15-remaining-plan.md) and [implement/verify guidance](../../../guides/implement-and-verify-rules.md).
- [Effect routing register](T13-effect-routing.yaml) and [summary](T13-effect-routing-summary.md). These record assignments and retained evidence, not proof that all behaviour is implemented.
- [Clarifications](T13-clarifications.yaml) and the pertinent [permanent rulings](../../../decisions/design-rulings.md). Apply the actual decisions to each clause, not just their reference IDs. Halfling culinary names add no bearer restriction; Reptile Venom is excluded from the duel.
- The new manifest and your closed assignment, plus any [follow-up](T13-execution-follow-ups.md) specifically referenced by your entries.

Trace source clauses into current KB contracts, construction, transport and modular consumers. Relevant entry points include [audit extraction](../../../../apps/combat-lab/mordheim_combat_lab/verification/audit_export.py), [binding inventory](../../../../apps/combat-lab/mordheim_combat_lab/verification/inventory.py), and [shared eligibility](../../../../packages/typescript/domain/eligibility/index.ts). Historical reports help locate contracts; verify claims against the examined revision.

## Assignments and ownership

| Agent | Primary family | Own result file |
| --- | --- | --- |
| A | Attacks, weapons, hit/wound resolution and offensive effects | `T13-semantic-analysis-dispatch/A-results.csv` |
| B | Armour, saves, damage resistance, injury consequences and recovery | `T13-semantic-analysis-dispatch/B-results.csv` |
| C | Psychology, Leadership and temporary states, including Fear, Hatred, Frenzy, Stupidity and immunities | `T13-semantic-analysis-dispatch/C-results.csv` |
| D | Construction, recipients, characteristics, grants and mixed clauses without a clear primary family | `T13-semantic-analysis-dispatch/D-results.csv` |

Paths above are relative to this guide's directory and designate **future** outputs. The coordinator owns the final `T13-semantic-analysis.csv`, exporter changes, shared registers and reservations. Agents own only their reserved result file; optional scratch belongs in gitignored `build/audit/semantic-analysis/<agent>/`.

The coordinator groups candidates by behaviour and existing operators, irrespective of band, item, skill or hireling origin. The **manifest wins over the advisory family table**. Every assigned input ID has exactly one owner. An owner analyses all clauses of its input, including those related to another family, and records the cross-family relationship rather than editing another assignment. Everyone may read the full inventory and shared contracts.

The preparation manifest must declare: revision and dirty-input basis; inventory path/hash; assignment paths, row counts and hashes; disjoint owner sets; schema header; authorized output paths; and source/context fingerprint procedure. Do not freeze the old 7,339-row count as a requirement for the new extraction. Include current rows without `t13_origin`; historical linkage is traceability only.

Assign every current `YES` (including reference-only origins), `LATER` and `UNCLASSIFIED` row for individual clause review. Do not defer a whole row because it mentions magic, Rout, advancement or another excluded subsystem: compound text can also contain admitted individual consequences. Assignment preserves the unresolved scope; it does not admit those subsystems. Keyword-based family suggestions are advisory and do not establish semantic equivalence.

## Analysis method

1. Verify your assignment, input fingerprints and reservation. Inspect applicable `AGENTS.md`, branch and existing changes. Do not overwrite concurrent work.
2. Resolve canonical source text, references and applicable rulings. Split each admitted compound rule into independently described clauses; retain explicit excluded portions and source-blocked clauses with their disposition.
3. Describe trigger, timing, consequence, target, duration, stacking and exceptions. Distinguish equipment ownership/use legality, source availability and the applicability of a combat effect.
4. Compare with existing contracts and consumers. A binding's kind, ID and parameters are useful candidates; identical bindings or prose are not proof of whole-rule equivalence. Wrong bindings remain findings, not the definition of the intended behaviour.
5. Reuse an existing executable effect ID when its contract is appropriate. Record genuinely new identities as `proposed.<slug>`; these are analysis proposals, not activated KB or runtime IDs. Do not create another family ID when an existing effect ID already expresses the relationship.
6. Classify equivalent effects, parameterised variants, related infrastructure, or independent behaviour. Document which clause is covered so a shared effect never closes the rest of a compound rule implicitly.
7. Inspect the real route through data, projection, construction and modular consumption. Identify missing work without treating declaration, assignment or source inspection as execution evidence. Reuse existing executed evidence only when its inputs and scope match; do not run a new certification campaign.
8. Recommend complete effect-based implementation batches, with local dependencies and observable closing criteria in the semantic contract/notes. Do not make unrelated global decisions prerequisites.

## Manual judgement and targeted corrections

Make semantic decisions by reading each source clause, the applicable rulings and its complete consumer route. Scripts may read/write CSV, serialize explicitly decided values, and check hashes, schema, identity coverage and references. They must not classify by keywords, infer equivalence, split clauses, or supply semantic defaults. Helpers must require explicit scope, relation, work, analysis/evidence states and conditions for every clause; never silently supply `YES`, `equivalent`, `none`, `reviewed`, `inspection`, passive timing or additive stacking.

Before accepting a clause's disposition:

- **Source versus binding:** derive intended behaviour from the resolved source and rulings. A binding proves a declared connection, not the intended meaning. Record a source/binding contradiction rather than inventing a clause to fit the code. An empty local effect is not `source_blocked` until references, aliases and the canonical definition have been checked.
- **Complete composition:** follow contributions from weapon, fighter effects, construction, state and resolver. Check the resulting count/formula, timing and guards; one branch is not the whole effect. Identify the precise mismatch before assigning `behavior`, and the boundaries inspected before assigning `none`.
- **Clause coverage:** split independently resolved consequences and excluded portions. Do not retain an executable `whole` row that repeats its child clauses. Distinct parameters of one inseparable effect need not become separate rows.
- **Scope decisions:** apply permanent rulings to each clause. Excluded map/movement, shooting or group producers must not become implementation requirements. Separate an admitted supplied individual consequence from its excluded external producer; preserve the recipient, duration and usage limits.
- **Evidence:** symbol existence and valid CSV are structural checks. Code inspection is `inspection`; a tiny executed probe supports only its exercised case. Test-file presence alone is not execution evidence or proof of equivalence.

Examples of errors to avoid, to be checked against the examined revision:

| Family | Required distinction |
| --- | --- |
| Art of Silent Death | Include the paired-claw contribution when checking attack totals. For A1, the reviewed operator produced two fist attacks and three claw attacks, meeting the recorded one-extra-claw closing condition. Inspect the critical guard separately; do not claim it restricts this skill to fists/claws when the branch has no such guard. A different intended total needs source/ruling support. |
| Black Hunger | Separate invocation, attack bonus and turn-end backlash from excluded movement. Missing map movement is not an admitted behaviour gap. |
| Rememberer and similar auras | Separate group emission/range from a supplied duelist reroll, retaining its large-target and once-per-game conditions. A third-party source does not itself exclude the individual consequence. |
| Belaying Pin and similar aliases | A mace binding cannot establish an unprinted melee/concussion clause. Resolve source support or record the conflict; classify the printed shooting clause under the existing exclusion. |

For a correction round, retain valid provenance and unaffected clauses. Manually check the affected semantic families and their assigned equivalents, including any rows assembled through the same unsafe defaults. Do not repeat extraction or rebuild the entire audit merely to repair findings. Recount from the final CSV. Structural checks cannot certify that remaining semantic judgements are correct; unresolved meanings stay explicit and do not block independent clauses.

## CSV contract

Partials and the maintained final CSV use the same header, in this order:

```text
origin_id,current_id,clause_id,source_file,source_fingerprint,clause_text,clause_scope,semantic_contract,effect_id,relation,parameters,conditions,consumer,implementation_work,dependencies,implementation_batch,analysis_status,evidence,evidence_refs,notes
```

UTF-8 without BOM, LF, final newline, standard CSV quoting, one physical line per record. Keep prose single-line. Each row describes one clause; `(origin_id, clause_id)` is unique. Every assigned input ID appears as `current_id` in at least one output row, with all its clauses accounted for. A duplicate reference to the same printed clause does not create a second runtime contribution.

| Columns | Meaning and values |
| --- | --- |
| `origin_id`, `current_id` | Preserve the explicitly supplied historical origin/successor pair. If none exists, both equal the current assignment ID. Never infer succession from names. |
| `clause_id`, `clause_text` | Stable descriptive clause key and the printed clause/excerpt covered. Preserve keys for unchanged clauses. When splitting an aggregate `whole`, replace it with clause rows and note the succession; do not duplicate the aggregate's obligations. A whole single-effect rule may use `whole`. |
| `source_file`, `source_fingerprint` | Copy the manifest's source path and fingerprint. The manifest defines hashing of source text, binding and relevant context; fingerprints are input provenance, not semantic certification. |
| `clause_scope` | `YES`, `NO`, `LATER`, or `UNCLASSIFIED`, justified by source/ruling references. Records clause disposition without modifying canonical scope. |
| `semantic_contract` | Concise intended behaviour, including the timing, target and exceptions needed to distinguish variants and an observable completion condition. |
| `effect_id`, `relation` | Existing or proposed effect identity. Relation: `equivalent`, `parameterized_variant`, `related`, `independent`, or `unresolved`. Leave effect ID empty for unresolved/excluded clauses rather than inventing a working consumer. |
| `parameters`, `conditions` | JSON objects (`{}` when empty). Record parameters separately from applicability/timing/duration/stacking/exceptions. An unresolved value is described as unresolved, not replaced by a guessed default. |
| `consumer` | JSON array of concrete `repo-relative-file::symbol` references (`[]` when unresolved/excluded). Identify existing versus proposed consumers in notes. Shared code alone does not establish equivalence. |
| `implementation_work` | `none`, `data`, `connection`, `projection`, `behavior`, `product`, or `assessment`. Select the first unresolved step; record additional required steps in notes. `none` means no identified gap, not certified completion. |
| `dependencies`, `implementation_batch` | JSON array of existing effect/decision/dependency IDs; batch recommendation. Use `[]` and an empty batch where appropriate. Cross-family references and proposed-ID collisions are coordinator consolidation work. |
| `analysis_status` | `reviewed`, `needs_clarification`, `source_blocked`, or `stale_input`. Reviewed meaning is independent of implementation/evidence; stale input must be revalidated before reuse. |
| `evidence`, `evidence_refs` | `none`, `inspection`, `retained_execution`, or `executed`; JSON array of actual references. Use execution labels only for matching, genuinely executed checks. Explain boundaries in notes. |
| `notes` | Remaining work, source conflicts, missing definitions, alternative interpretations, cross-family IDs, and evidence limits. Be concise; no new per-effect reports. |

## Synchronization and handoff

| Stage | Responsible action |
| --- | --- |
| Preparation | Coordinator publishes the frozen extraction, fingerprint method, manifest, closed lists and reservations. Missing preparation is not permission to select a private inventory or expand ownership. |
| Start | Agent verifies its own input and reports any concrete discrepancy through the dispatch channel or its result notes. Preserve all unrelated dirty files. |
| Work | Agent writes only its own partial. Record cross-family effects without reassigning IDs or editing shared files. Continue independent entries when another clause needs a ruling. |
| Input drift | Mark affected rows `stale_input`, retain the supplied fingerprint and name the changed source/context. Do not silently replace the baseline or claim current equivalence. |
| Delivery | Recheck assignment coverage, tuple uniqueness, schema/enums/JSON and input validity. Include blockers and the concise checks actually performed in the handoff message. Do not mark the initiative complete. |
| Consolidation | Coordinator reconciles cross-family equivalents, proposed IDs, conflicts and successor links; reviews discrepancies proportionally rather than repeating every analysis. Merge accepted clauses into the maintained CSV. |

Only the coordinator changes reservations or shared states. A requested ownership expansion follows the existing coordination protocol; it does not authorize edits while pending. The human user launches external agents. No nested agents, commit or push are part of this study.

The coordinator may prepare exporter support in parallel, using this CSV contract and isolated fixtures. That does not authorize agents to edit the exporter. An accepted family can guide implementation before unrelated families finish; overlapping production-file writers still require serialization/reservation.

## Completion and future use

- No assigned input disappears without a disposition; every compound clause remains represented. Coverage is checked against the new manifest, not historical counts.
- Partial schemas agree, ownership is unique, references resolve, and source drift is visible. A conflicting cross-family equivalence remains explicit until consolidated.
- Meaning, required implementation and available evidence remain independent. Neither reviewed analysis nor metadata changes `implemented`, canonical scope or certified T14 evidence.
- The **maintained analysis CSV** is the single owner of these semantic conclusions. Routing continues to own assignment/progress references without duplicating the analysis. Generated audit CSVs will project the conclusions; they must never overwrite the maintained file.
- Exporter integration is subsequent work, not implemented by this guide. It must preserve audit row identity, expose all clause assignments for compound rows, and flag missing/superseded/changed inputs instead of silently reusing conclusions.
- Only assignment/CSV/reference/input-validity checks are required for this study. No full behavioral, parity or coverage gates, additional reports, KB fixes, or phase completion claims.

**Readiness:** this guide defines the contract. The new manifest, assignments, result CSVs, final analysis CSV and exporter integration are not created or activated by publishing it.
