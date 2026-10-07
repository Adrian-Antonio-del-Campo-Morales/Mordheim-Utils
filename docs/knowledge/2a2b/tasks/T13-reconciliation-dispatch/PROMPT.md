# Independent reconciliation audit dispatch

Assign exactly one LOT before starting: A-construction, B-construction,
C-combat, D-facts-context-references, E-unresolved, or F-excluded-scope-control.
The first five lots reconcile all included and unresolved entries. F independently
checks exclusions; it is not a prerequisite for starting reconciliation.

## Objective and closed ownership

Work in `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`. Read `manifest.json`
and only take ownership of the IDs in `<LOT>.csv` in this directory. Verify its
SHA-256 and row count. Input lists are frozen assignments, not implementation
truth. Every assigned ID must have exactly one result, including blocked IDs.
Do not expand the assignment when discovering related entries: record their IDs
as dependencies. Multiple assigned entries may describe one mechanic: retain
one result per entry and identify the common implementation target.

Inspect branch, status and applicable AGENTS.md first. Preserve concurrent work.
Do not spawn agents, commit, push, activate mechanics or modify shared files.
All repository code, KB, existing reviews, manifests and assignment lists are
read-only. Own only `<LOT>-results.csv` and `<LOT>-summary.md` in this directory.
Optional scratch scripts/logs belong in `build/audit/reconciliation/<LOT>/`.
Do not regenerate shared web assets, bundles, audit outputs or coverage budgets.

## Required reading and project orientation

Paths below are relative to the repository root. Read in this order; focus on
these sections instead of reading every historical delivery.

### Common foundation: every lot

1. `docs/reference/architecture.md`: Source layout, Dependency boundaries,
   Shared resources and entry points, and Combat engines. Locate the actual
   owner of data, eligibility, compilation, modular execution and verification.
   Combat Lab and Warband Manager are separate products sharing KB and pure
   construction/eligibility decisions; campaign roster state is not duel state.
2. `docs/reference/knowledge-base.md`: Layout, Runtime classification, Anatomy
   of an editorial special rule, shared catalogues, Contract guards, and Path
   of a rule: from YAML to the engines. Understand canonical IDs, references,
   runtime metadata, bindings, mechanic/execution mappings and their consumers.
3. `docs/reference/eligibility.md`: Batch construction contract, Consumer
   workflows, Construction boundary for phased implementation, and Ownership
   and retained adapters. Distinguish legal choices from compiled duel effects
   and from implementation support. Do not rediscover or duplicate shared rules.
4. `docs/guides/implement-and-verify-rules.md`: current operational audit,
   scope review, implementation ownership and reasonable validation workflow.
5. `docs/knowledge/2a2b/tasks/T13.md` and
   `docs/knowledge/2a2b/tasks/T13-T15-remaining-plan.md`: current scope, accepted
   user decisions, modular progress and remaining work. Historical broad battle
   context is subordinate to the current 1v1 boundary in this dispatch.
6. `docs/knowledge/2a2b/README.md`: current product boundary, work protocol and
   active reservations only. Consult
   `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` for relevant existing
   issues, and `T13-audit-scope-review.csv` for the reviewed rationale.

### Targeted reading by lot

- A/B construction: relevant parts of
  `contracts/knowledge-editorial-v1/README.md` (Document map and Conventions),
  then the actual schemas for your profiles, equipment access, skills, items or
  hirelings. Consult `docs/guides/campaign-knowledge.md` (Ownership and read
  path; Identity and modelling) when entries concern hirelings, trading or
  campaign consequences. Use current shared eligibility APIs and Python
  adapters; do not infer legality from UI lists alone.
- C combat: `docs/reference/verification.md` and
  `docs/knowledge/2a2b/tasks/T13-contracts.md` (Characteristics and compilation,
  Explicit local context, Actual consumers and transport). The latter is a
  historical contract explanation: revalidate consumers and retain only context
  consistent with today's scope. Inspect current `execution.yaml`,
  `simulation-mappings.yaml`, compiler bindings and relevant modular phases.
- D facts/context/references: the same contract sections as C, plus
  `docs/guides/campaign-knowledge.md` (Ownership and read path; Identity and
  modelling). Separate a supplied fact/consequence from campaign generation,
  external actors and casting. Resolve aliases to canonical identities.
- E unresolved and F excluded control: relevant shared catalogue sections of
  `docs/reference/knowledge-base.md`, relevant schemas, and original source
  references for each disputed clause. Read the A/B, C or D targeted material
  when a candidate belongs to that boundary. Absence of metadata does not
  establish exclusion; uncertain full source text stays explicitly unresolved.

Treat historical reports as leads, not evidence of current code. Inspect current
extraction and classification in
`apps/combat-lab/mordheim_combat_lab/verification/audit_export.py`, then follow
maintained loaders, binding consumers and construction APIs for your entries.
If documentation conflicts with current source/code, record the discrepancy and
its impact; do not silently rewrite the agreed product scope or treat passing
code as a resolution of a semantic contradiction.

## Scope

Combat Lab simulates individual 1v1 melee duels. Construction restrictions,
participant facts and qualified supplied consequences can belong to this scope
without simulating their campaign producer. Exclude shooting/casting resolution,
map/weather/terrain, movement, group Rout, third independent participants,
post-duel capture, and escape/early termination without resolving the duel.
For mixed prose, identify admitted and excluded clauses separately. Neither a
binding, a scope decision, an implementation flag nor a historical T13 label
proves that an effect is implemented end to end.

## Procedure

For each assigned entry:
1. Locate current source text, resolve references, and compare the audited raw
   effect SHA-256 using the maintained extraction where applicable. Do not hash
   the flattened display text in the CSV. Record source drift or extraction
   uncertainty; never overwrite the original assignment or trust stale prose.
2. Determine current scope from the actual clauses. E investigates unresolved
   sources; F challenges exclusions for hidden duel/construction clauses.
   Research referenced original sources where needed, recording URLs/pages.
   Do not invent missing wording or quietly turn source uncertainty into NO.
3. For admitted clauses, trace the existing contract, recipients, binding or
   structural facts through the actual consumer. Construction is owned by the
   shared eligibility/construction module; Combat Lab compiles effects and
   resolves melee. Inspect adapters as well as the shared decision.
4. Classify the result as `covered`, `metadata_gap`, `connection_gap`, `partial`,
   `implementation_missing`, `out_of_scope`, `source_blocked`,
   `decision_required`, or `stale_input`. Explain exact missing clauses for
   partials. `covered` requires current source-to-consumer evidence, not just a
   name or a binding. If no practical live access exists, explicitly state it.
5. Reuse existing tests when relevant. Run small existing suites or batched
   read-only probes only when they resolve real uncertainty; do not create a
   maintained test suite, full semantic certification or per-entry integration
   campaign. Distinguish code inspection from executed behavioral evidence.
6. Record real follow-ups with existing IDs where possible, affected targets,
   impact and a concrete closure criterion. Propose repairs; do not implement.

For A/B prioritize effective recipients and shared eligibility, without treating
prices/acquisition as duel mechanics. C checks modular behavior, timing and
composition; optimized engines remain outside this assignment. D distinguishes
supplying a fact from automating its producer and checks reference aliases. E
must identify the exact source/decision needed when unresolved. F reports any
excluded mixed clause that warrants admission and reconciles it when possible.

## Output and closing

Results CSV columns:
`id,source_file,source_state,proposed_scope,admitted_clause,excluded_clause,status,
existing_target,contract_evidence,consumer_evidence,validation_evidence,missing_part,
related_ids,existing_follow_up,next_action,closure_criterion`.
Use UTF-8 and LF. No extra or duplicate IDs; row count must equal the assignment.
Evidence must use current repository paths and symbols (line numbers when useful)
or exact external source references. Do not label unexecuted checks as passed.

Summary: concise counts, grouped actionable gaps, blockers and recommended next
implementation groups. Avoid one prose section per row, temporary documentation
sprawl and duplicated historical reports. Record branch/HEAD, manifest hash,
checks actually run, and concurrent drift affecting conclusions. Revalidate your
input manifest and relevant source/code hashes at closure; mark affected results
stale or blocked when another writer invalidates evidence. No KB/status acceptance
or coordinator register updates. Deliver the two owned files for consolidation.
