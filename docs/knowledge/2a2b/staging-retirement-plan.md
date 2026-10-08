# Retire the 2A/2B staging trees — external-agent execution plan

## Objective and boundary

Complete the existing promotion into `sources/knowledge`, then remove
`sources/2A`, `sources/2B` and their exclusive dependencies. Applications already
read the canonical KB; this is a reconciliation and retirement batch.

Preserve later implementation, eligibility, translations, variants and adopted
decisions. Do not implement combat rules, modify engines, start optimized ports,
certify T13/T14/T15, commit or push. This guide launches no agents, reserves no
files and does not declare retirement complete.

## Read before starting

- [Architecture](../../reference/architecture.md),
  [KB conventions](../../reference/knowledge-base.md),
  [shared eligibility](../../reference/eligibility.md),
  [tools](../../reference/tools.md) and
  [verification](../../reference/verification.md).
- [Editorial contract](../../../contracts/knowledge-editorial-v1/README.md),
  [permanent rulings](../../decisions/design-rulings.md),
  [consolidated 2A/2B knowledge](2A2B-Knowledge.md) and the maintained
  [semantic development CSV](tasks/T13-semantic-analysis.csv).
- The agent's dispatch, applicable `AGENTS.md`, actual checkout and dirty files.
- Before removing staging: both `manifest.yaml` files; promotion/merge notes,
  discrepancy verdicts and equivalence reviews under `sources/2A` and
  `sources/2B`; `tools/ingestion/README.md`; and the correspondence tables in
  `packages/python/knowledge/mordheim_knowledge/staging_promotion.py`,
  `magic_promotion.py` and `hireling_promotion.py`.

Historical reports are supporting evidence. Current source text, adopted
rulings and canonical consumers govern the reconciliation.

## Coordination and ownership

Each dispatch must state the entry revision, closed package/record set,
authorized files, owner, dependencies and expected handoff. Check reservations
before editing and preserve changes from other writers. This guide is not a
dispatch or authorization to expand an assigned set.

Disjoint band packages may be reconciled in parallel. Shared catalogues,
registries, schemas, tooling, the semantic CSV and shared documentation must
have a single writer or be serialized. Only the coordinator performs the final
retirement after the reconciled contributions have been integrated.

Record cross-package findings with related IDs; do not edit another owner's
assignment. On input drift, re-check the affected records before writing and
continue independent records. No agent may launch other agents automatically.

## Execution sequence

### 1. Establish a recoverable baseline

Check branch/worktree and current changes; do not reset, clean or replace dirty
files. Capture the staging inventory and dependencies, including bands, items,
market entries, magic, hirelings and non-YAML material.

Keep byte-exact recoverable copies of everything to be removed, including
uncommitted content. Use ignored scratch storage under `build/cache/`; do not
create another maintained report collection. Record the relevant entry hashes
and verify that the backup can reproduce the original files.

### 2. Reconcile every staged record

Use the existing promotion correspondence tables to locate canonical records,
redirects, merges, variants and exclusions. The promotion preview may help
enumeration, but do not run its writer against the live KB or demand identical
trees: later canonical improvements legitimately differ from staging.

The initial read-only preview on 2026-10-08 reported 80 conflicts (68 band
documents and 12 hireling records) and a proposed market addition for
`campaign.trading-post.ceremonial-scythe`. These are starting observations, not
a frozen assignment or evidence of missing data. Re-check the current tree;
in particular, inspect whether that market offer belongs in the canonical
catalogue before adding it.

For each record, retain a scratch disposition: already canonical, merged into a
named canonical record, redirected/replaced, or explicitly excluded with a
reason. Every substantive difference must be explained; no valid information
may disappear behind an exclusion.

**Make semantic decisions manually. Read each substantive difference and its
resolved source, recipients, timing, parameters and exceptions.** Tools may
enumerate IDs, align structures, calculate hashes, serialize explicit decisions
and check references. They must not classify meaning or infer equivalence in
bulk from names, keywords, bindings or implementation flags.

Keep source-backed canonical improvements and adopted rulings. Add valid facts
that are genuinely absent, preserving translations and provenance. Preserve
separate identities for real variants; do not introduce duplicate records or
revert runtime metadata merely to restore mirror equality. Sharing a name or
`rule_ref` does not establish semantic equivalence.

### 3. Preserve durable information

Keep source URLs, page/section citations and necessary provenance in the
appropriate canonical records/registries. Retain existing printed-source
readers and wording decisions that still support the canonical KB.

Move still-valid design decisions to the permanent rulings and unresolved
findings to the consolidated 2A/2B document. Keep the exact affected IDs,
source, missing fact or contradiction, next action and completion criterion.
Do not copy entire historical reports or mark unresolved content as covered.

Check the previously identified shared-reference differences around Night
Goblins' Always Hungry, Clan Skryre's Wizard, Strigoi's Living and contextual
Experience/Brainless prose. Preserve any unresolved findings before deleting
their supporting reports; this batch does not invent missing interpretations
or add combat behavior.

Preserve accepted conclusions and origin/clause identities in the semantic CSV.
Change only affected source references or fingerprints when justified by the
actual reconciliation. Do not regenerate over maintained conclusions or
refresh unrelated specification pins. A local source uncertainty must not
block unrelated packages; preserve the available text/provenance and the
explicit unresolved finding so retirement does not erase them.

### 4. Remove exclusive dependencies

Trace imports, callers, CI/test manifests, command modes and documentation
before removing anything. Retire `tools/ingestion/` and promotion/staging-only
modules only after their reusable logic or durable decisions have a canonical
owner. Keep general normalization, source reading and canonical audits.

Adapt permanent audits and useful existing checks to `sources/knowledge`.
Remove completed promotion/mirror tests and staging-exclusive command modes;
preserve actual identity, schema, translation, source and behavior contracts.
Do not retain an obsolete module solely to expose constants to a test.

Update affected test manifests, commands and documentation. APIs consumed by
applications remain stable; explicitly document the retirement of staging-only
CLI modes. Grades/categories `2a` and `2b` and source-cache names are legitimate
metadata, not dependencies to delete.

### 5. Verify, then retire

After integration, check that all staged records have dispositions and every
retained fact has a canonical destination or an explicit unresolved finding.
Verify references and affected consumers before deleting the two trees.

On Windows, resolve and verify the absolute deletion targets within this
checkout; use native operations with literal paths. Never recursively remove a
computed or unchecked target. Restore the relevant boundary from the verified
backup if preservation fails; do not overwrite concurrent work during recovery.

Remove operational references to deleted paths, including those in this guide
and any instructions that still require staging mirrors. Keep only a short
completion note and genuinely open findings in the consolidated document.

## Proportionate verification and completion

- Inventory coverage: every staged record is accounted for, with valid
  destination IDs or justified exclusions; no missing valid facts.
- Load and validate affected canonical documents and resolve their references.
- Run existing focused checks for source/translation/identity contracts moved
  out of staging, plus behavior checks only for actual affected consumers.
- Regenerate web knowledge only if KB data changes, then run its `--check`.
  Never edit generated data manually.
- Check affected links, imports, commands and manifests; no remaining
  operational dependency may require the removed directories.

Do not run full suites, coverage campaigns, parity or phase certification.
Keep structural evidence, manual interpretation and executed behavior evidence
distinct. Report inherited or concurrent failures with their actual impact;
do not count a failed required check as passing.

Close when valid information and later improvements are preserved, unresolved
findings remain actionable, focused required checks pass and staging has no
operational consumers. Deliver only a brief summary of changed areas,
executed checks and remaining limitations. No additional maintained reports,
automatic agent launches, commit or push.
