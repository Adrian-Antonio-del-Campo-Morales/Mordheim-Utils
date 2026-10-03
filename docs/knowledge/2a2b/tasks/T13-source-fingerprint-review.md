# T13 — Source fingerprints and canonical references review

Execution evidence, accepted by the coordinator as the bounded R0 investigation
in section 9. This is not full T13 acceptance or a T14 certificate. The agent
closed no question/follow-up; the coordinator's F027 disposition is recorded below.
It changes no KB,
specification, engine, interface or language file and refreshes no digest or
implementation mark. The [initiative checklist](../README.md) owns task status;
the [follow-up register](T13-execution-follow-ups.md) owns deferred findings.

Entry evidence was captured on 2026-10-01 (UTC), before any judgment about the
current failure set, and the reconciliation was computed from the live working
tree plus committed KB revisions. Companion matrix:
[T13-source-fingerprint-review.csv](T13-source-fingerprint-review.csv) (580 rows:
455 fingerprint findings + 125 canonical-reference findings).

## 1. Examined state and coverage limits

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e` ("chore:
  snapshot UI, localization and T13 planning"). The task entry state was
  recorded before running any check (see §6).
- `sources/knowledge` in the working tree is byte-identical to the committed
  HEAD (`git status --porcelain -- sources/knowledge` empty; `git diff --stat
  HEAD -- sources/knowledge` empty). The KB content that T13.0 observed as
  concurrent worktree changes is committed in this revision.
- Other working-tree files (application code, guides, T13 lot documents) are
  modified or untracked and were preserved untouched. No commit, push, agent
  launch, KB mutation, artifact regeneration or digest refresh was performed.
- Authorized paths: `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.md`,
  `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.csv` and evidence
  under `build/cache/t13-parallel/source-fingerprints/`. At the entry check
  (before 08:00 UTC) the checklist table had no row reserving this dispatch, the
  two maintained files did not exist, and no competing owner was present. The
  closing check (08:37 UTC) found the coordinator's row **R0 — source/fingerprint
  evidence** in the README, reserving exactly these paths for "External agent A,
  launched by user" with an evidence-only scope. The discrepancy is therefore
  resolved by the coordinator's later row; this review did not edit the README.
- Coverage: current semantic verification JSON (working KB), a fresh semantic
  verification of the committed HEAD KB, structural verification, the rule
  inventory, one fresh `tests/python/verification/test_semantics.py` run, and a
  canonical-reference scan over band `special-rules.yaml` files, `catalog/skills`
  files and the register's `shared_rule_reference` rows.
- Not covered: parity/statistical certification, coverage gate, native rebuild
  or native execution, Web/application suites, the T13.2 pytest matrices, and
  any mechanism implementation. This review does not certify semantics.
- Historical reports are reused as context only. Only the fresh runs recorded in
  §6 are evidence of the current failure set. In particular, T13.0's "455
  working / 30 HEAD" table and T13.1's "455 errors" statement are historical;
  §3 states their current relation.
- Comparing digests against a commit shows which content matches a pin. It does
  **not** prove which content produced an old pin, and a moved pin is not by
  itself a defect of any implementation. No source original outside the
  repository was needed: the canonical KB and the committed revisions contained
  the evidence.

## 2. Reproducible procedure

1. Recorded branch, HEAD, `git status`, the `sources/knowledge` diff against
   HEAD and SHA-256 hashes of the relevant inputs (`entry-state.txt`).
2. Ran the existing verifier twice without changing anything: current working
   KB and a read-only `git archive` extraction of committed HEAD
   (`verify-current.json`, `verify-head-current.json`). Also ran inventory and
   structural JSON, and one focused semantic pytest file.
3. Joined the current error identities (specification + canonical target) with
   the semantic specification pins (`tests/specs/semantic/**/*.yaml`) to obtain
   expected digest vs current digest, and with the T13.0 origin register
   (`T13-obligations.csv`) for canonical identities, lots, dispositions and
   questions. Conflict detection used `origin_key`.
4. Recomputed each obligation digest at three revisions using the existing
   algorithm — `sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
   separators=(",", ":")))` over the exact structures `inventory()` fingerprints
   (`{"rule": <KB node>, "context": <profiles/equipment-access/band>}` for
   rule grants, the catalogue row for mechanics): pre-snapshot `eb85e95`, HEAD
   `1b7f7cf` and the working tree. An `_i18n`-stripped recomputation separates
   translation-only moves from non-i18n changes (`analyze.py`,
   `classify-content-split.py`).
5. Resolved empty local `effect` texts by following `rule_ref` /
   `shared_rule_reference` into `catalog/rules/special-rules.yaml`, and checked
   the semantic inventory for obligations whose resolved text is empty.
6. Generated the companion CSV from the reconciliation
   (`generate-deliverable.py`); the generated report is not hand-edited.

## 3. Reconciliation of the current failure set

### 3.1 Current runs

| Run | Errors | Identity set |
| --- | ---: | --- |
| Working tree (`verify --json`, exit 1) | 455 | all `source changed` |
| Committed HEAD `1b7f7cf` KB (exit 1) | 455 | identical pair set to the working run |
| T13.0 working run (2026-09-30) | 455 | identical pair set (historical) |
| T13.1 final run (2026-09-30) | 455 | identical pair set (historical) |
| Pre-snapshot `eb85e95` KB (T13.0 run, historical) | 30 | strict subset of the current 455 |

Structural validation is complete (`1050` profiles compiled, 0 structural
errors). Semantic validation remains incomplete: 718 inventoried obligations,
699 fixtures, 171 verified, 547 pending, `semantic_complete: false`, exit 1.
Every error is a **source-digest pin** difference; there are no `scope changed`,
unknown-target or execution errors in the report (0 scope errors; a `scope_digest`
pin review would read differently).

### 3.2 Superseded split

T13.0 compared the working KB against its then-HEAD (`eb85e95`) and reported
30 errors at HEAD and 455 in the working tree. Commit `1b7f7cf` then committed
that concurrent KB content, so the 425 working-only differences are now part of
committed HEAD and also error. The current state is therefore: **all 455 pins
are stale against both the working tree and HEAD**, and the historical 30 are a
subset of them. The old 30/425 split must not be cited as the current split.

### 3.3 Current split of the 455 findings

| Classification | Pairs | Meaning / evidence |
| --- | ---: | --- |
| `snapshot_translation_only` | 300 | Expected digest equals the pre-snapshot `eb85e95` digest; between `eb85e95` and HEAD only `*_i18n` fields moved (`_i18n`-stripped digests equal). Data/pin reconciliation, not rule-source semantics. |
| `snapshot_content_change` | 125 | Expected digest equals `eb85e95`; the non-i18n difference is **only** in the digest context documents (`profiles.yaml`, `equipment-access.yaml`, `band.yaml`); the non-i18n rule row is unchanged in every one of the 125 (`content-split.json`: 125 `context_only`, 0 `rule_text`). Needs data/context review. |
| `pre_snapshot_pin_mismatch` | 30 | Expected digest differs from `eb85e95` already: the pin was stale before the snapshot. These are exactly the 30 pair identities of the T13.0 historical HEAD run; historical T12 debt under T13-F001. |

Other identity facts for the 455 rows:

- Obligation kinds: 436 `grant` pairs and 19 `mechanic` pairs (3 mechanic ids:
  `skill.step-aside`, `skill.elven-agility`, `skill.vampire-reflexes`).
- 425 unique canonical targets, across 397 unique `(canonical_file,
  canonical_id)` rules in 76 canonical files; 352 specifications carry at least
  one stale pin. Specification categories: `local` 141, `permanent` 98,
  `construction` 92, `contextual` 47, `stateful` 41, `interaction` 29,
  `priority` 7.
- The largest affected files are trollheim `chaos-streets-undead-bloodlines`
  (30 pairs), trollheim `lustria-lizardmen` (27), the mechanics catalogue
  `close-combat.yaml` (19), `carnival-of-chaos` (18), `pit-fighters` (17) and
  `restless-dead` (17).
- Every current digest recomputed from the working KB equals the digest in
  `verify-current.json`, and every current digest equals the `1b7f7cf` digest:
  the two runs are the same content, and the JSON evidence is not stale.

### 3.4 Relation to the T13.0 origin register

None of the 425 stale-pin targets resolves to an origin row: the join on
`(canonical_file, canonical_id)` produces 0 matches, and the 76 affected
canonical files are disjoint from the register's 91 canonical files. The CSV
therefore carries empty `origin_keys`, empty `question_ids` and empty T13 lots
for all 455 fingerprint rows. Consequences:

- No current source-pin failure is attributable to a T13 origin identity, and no
  `T13-Q` question is attached to any of them.
- T13-F001 still owns the inherited baseline reconciliation; this result locates
  the failures outside T13's admitted origin set rather than dismissing them.
- No exact origin join was found in this error set. This does not certify every
  register origin: many pending clauses are outside the executable semantic
  inventory. Nor does disjoint canonical-file identity prove independence from
  shared operators, contexts or eligibility changes. Those dependencies still
  require the regressions specified by the owning mechanism and F035.

### 3.5 Pytest-level failures

The fresh focused run `tests/python/verification/test_semantics.py` (`-q
--tb=no -rf`, 7:01 min) is **4 failed, 3779 passed**, exit 1:

- `test_structural_success_is_not_semantic_success`
- `test_bear_hug_has_a_real_source_link_and_detected_behavioural_mutations`
- `test_unverified_shared_consumer_keeps_editorial_grant_pending`
- `test_redundant_access_mutation_is_justified_not_counted_as_detected`

The coordinator matched all four identities to the four semantic failures in
T13.1's retained `build/cache/t13-1/entry-failures.xml`. Its fifth failure was
`test_audit_export.py::test_resolved_real_question_is_preserved_in_verified_row`,
outside the file executed here. Four versus five is a test-scope difference;
this review does not demonstrate that the audit failure was fixed. The current
run has only a short traceback-free summary, while the older XML records source
pin assertions for these four identities. Retain that distinction rather than
claiming a new diagnosis from failure counts. These test failures are separate
from the 455 specification/target pairs. No global semantic success is claimed.

## 4. Resolved and pending references

### 4.1 Empty local effect texts

- 379 band `special-rules.yaml` rules have an empty local `effect`. All 379
  carry a `rule_ref`; every reference resolves to one of 68 shared rules in
  `catalog/rules/special-rules.yaml` whose `effect` is non-empty. **0 broken or
  dangling references.**
- 125 of those nodes are T13 origins (register rows with a non-empty
  `shared_rule_reference`). For all 125 the register's
  `shared_rule_reference` equals the node's `rule_ref`, and all resolve:
  `empty_local_effect_resolved_by_shared_reference`. Dispositions: 92
  `included`, 22 `campaign`, 5 `source-blocked`, 4 `excluded`, 2 `mixed`.
- The T13-F027 subjects are covered: 12 `shared-rule.immune-to-poison` nodes and
  8 `shared-rule.no-pain` nodes, all classified `included` with planned lots
  `T13.2` + `T13.3`. Other frequent references: `shared-rule.leader` 28,
  `shared-rule.cause-fear-2` 6, `shared-rule.stupidity` 5,
  `shared-rule.immune-to-psychology` 5.
- Five reference rows are question-bearing: T13-Q006 (`black-sheep--stupidity`),
  T13-Q025 (`troll--stupidity`), T13-Q041 (`loremaster--wizard`), T13-Q090
  (`warlock-engineer--wizard`) and T13-Q096 (`bats--living`); all five are
  `source-blocked` and none of their questions is closed here.
- Corpus-level check: none of the 718 semantic inventory obligations has an
  empty resolved text after reference resolution.

### 4.2 Pending references

No broken or missing canonical reference was found in the examined scope. The
F027 disposal criterion was left for the coordinator at agent handoff. Section 9
now accepts canonical shared-reference resolution and closes that missing-text
observation only. This does not certify that shared wording settles every variant's
complete semantics; existing source questions and mechanism acceptance remain
separate. No substitute wording is written.

## 5. Findings that need a coordinator decision

These are the questions retained at agent handoff. Section 9 records the current
coordinator dispositions; the follow-up register owns their resulting status.

1. **Reservation status (re-checked at closing).** At entry the README had no
   row for this dispatch; while this review ran, the coordinator added row R0
   ("source/fingerprint evidence"), reserving exactly the three authorized paths.
   No competing owner exists. The coordinator may decide whether the entry-time
   gap needs a separate process note; no README edit is made here.
2. **300 translation-only pins.** They are stale because committed translation
   fills moved the digest, not because rule semantics changed. Decide between a
   reviewed spec-pin refresh and a narrower review; this lot refreshed nothing.
3. **125 context-data changes.** The rule text is unchanged; the digest moved
   with `profiles.yaml` / `equipment-access.yaml` / `band.yaml` edits (for
   example `equipment_restrictions` entries removed or reworded). Decide who
   reviews that KB data and whether the affected pins are then repinned.
4. **30 pre-snapshot historical pins.** These are the T12-debt identities
   T13-F001 has to route to a source or mechanism owner; the 30 exact targets
   are listed in `findings.json` and in the CSV as
   `source_digest_changed_pre_snapshot`. No disposition is decided here.
5. **Cross-referenced entities.** 33 rows carry a specific follow-up ID because
   their canonical id or shared mechanic resembles an open finding (F002 Iron
   Sinews 2, F010 Vomit Attack 5, F011 Scaly Skin 2, F014 marker abilities 11,
   F016 named skill tables 2, F017 band recipient filters 11; 13 of those also
   reference F035). These are **name-level cross-references in different
   canonical files**, not register joins; the coordinator decides whether any
   consolidation is warranted. The CSV carries the qualifier in
   `unresolved_reason`.
6. **T13-F035 boundary.** The fingerprint review neither replaces nor completes
   the eligibility-extraction revalidation. Where a stale pin touches a rule
   already affected by F004/F016–F021/F028, F035's own resume condition still
   applies to that finding's construction evidence.
7. **The four pytest failures.** Confirm they stay classified as inherited
   (`T13-F001`), not as new defects introduced by T13.2–T13.4 lots.

## 6. Commands, results and evidence paths

All commands from the repository root with `python -X utf8`. Evidence directory:
`build/cache/t13-parallel/source-fingerprints/` (ignored by Git).

| Command | Result | Artifact |
| --- | --- | --- |
| Entry state + input hashes (see below) | — | `entry-state.txt` |
| `tools/mordheim-utils.py verify --json` | exit 1; 455 `source changed`; structural complete | `verify-current.json`, `verify-current.stderr.txt`, `verify-current.exit.txt` |
| `tools/mordheim-utils.py verify --inventory` | exit 0; 718 obligations | `inventory-current.json` |
| `tools/mordheim-utils.py verify --structural --json` | exit 0; structural complete, 0 errors, 1050 profiles | `structural-current.json` |
| `bash extract-kb-revisions.sh` (read-only `git archive`) | `1b7f7cf` and `eb85e95` KB trees extracted | `1b7f7cf-knowledge/`, `eb85e95-knowledge/` |
| `tools/mordheim-utils.py verify --knowledge <1b7f7cf KB> --json` | exit 1; 455; identical pair set to current | `verify-head-current.json`, `.exit.txt` |
| `python -m pytest tests/python/verification/test_semantics.py -q --tb=no -rf` | exit 1; 4 failed, 3779 passed | `pytest-semantics.txt`, `pytest-semantics.exit.txt` |
| `analyze.py` | 455 findings classified; 125 references resolved | `findings.json`, `findings-fingerprint.csv`, `empty-effects.json`, `empty-effects.csv`, `summary.json` |
| `classify-content-split.py` | 125 `context_only`, 0 `rule_text` | `content-split.json` |
| `generate-deliverable.py` | 580 rows written | evidence copy + `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.csv` |

Entry input SHA-256 (recorded in `entry-state.txt`): `T13-obligations.csv`
`2a3b962e…` (the register hash T13.0 delivered; unchanged at closing),
`T13-automatic-grants.csv` `f18e1ddf…`, `T13-selectable-equipment.csv`
`ee0b5ce6…`, README `aa6e7c63…`, follow-up register `c1b4b900…`,
`verification/inventory.py` `e2460dc4…`, `verification/audit.py` `98f0e8a3…`,
`refresh_spec_digests.py` `83fbe815…`. During the work another writer changed
the README (`ec9c44af…`) and the follow-up register (`536e5c90…`); the KB, the
semantic corpus, the engine verification code and the obligation register did
not change. Only the checks that those two documents govern (reservation state
and follow-up citations) were repeated, in §1 and §8.

The CSV has one row per finding:

- 455 fingerprint rows `FP-0001…FP-0455` with `specification_or_case`,
  `canonical_file`, `canonical_id`, `mismatch_kind`
  (`source_digest_changed_snapshot_translation` 300,
  `source_digest_changed_snapshot_context_data` 125,
  `source_digest_changed_pre_snapshot` 30), expected and current digest,
  `source_reference`, evidence pointer, empty `origin_keys`/`question_ids`, the
  follow-up IDs and the proposed owning lot.
- 125 reference rows `EF-0001…EF-0125` with `mismatch_kind`
  `empty_local_effect_resolved_by_shared_reference`, the `rule_ref`, the shared
  effect text SHA-256, the origin key, disposition/lots in the evidence field,
  and `T13-F001`/`T13-F027`/`T13-F029`.
- No historical report is added to the CSV as an independent set; the 30
  pre-snapshot rows are a classified subset of the current 455.

## 7. Proposed entries for the follow-up register

Historical agent proposals below; section 9 and the follow-up register contain
the accepted dispositions and current statuses.

The coordinator inserts these; this review does not assign new `T13-F` IDs.

- **Update T13-F001:** current baseline reconciled on 2026-10-01. Working tree
  == HEAD `1b7f7cf`; current run reproduces 455 identical pair identities (no
  new drift since T13.0/T13.1). Split: 300 translation-only, 125 context-data
  (rule text unchanged), 30 pre-snapshot historical. None of the 425 targets
  intersects the 1,692-origin register. State: open, awaiting routing.
- **Update T13-F027:** all 125 empty-local-effect T13 nodes resolve through
  `rule_ref`/`shared_rule_reference` to non-empty shared rules; 0 broken. The
  immune-to-poison/no-pain subjects are 20 included nodes. No wording written.
  State: open; disposition criterion remains for the coordinator.
- **New entry (process, optional):** the reservation row R0 for this dispatch
  appeared only during execution. If the coordinator wants the entry-time gap
  tracked, record it; otherwise no action is needed.
- **New entry (optional):** name-level cross-references between current stale
  pins and open findings F002/F010/F011/F014/F016/F017/F035 need a coordinator
  decision on whether any are consolidated into those findings.
- No `T13-Q` is closed; no T13/T14 status is changed.

## 8. Post-work file check

The closing check (08:37 UTC) repeated `git status`, re-hashed the entry inputs
and listed the evidence directory. `sources/knowledge`, `tests/specs` and
`T13-obligations.csv` were unchanged, so the verification, inventory and digest
evidence in §3–§4 remains valid and no run needed to be repeated. Two inputs
changed concurrently: `docs/knowledge/2a2b/README.md` (the coordinator added row
R0, see §1) and `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` (F007
updated by the R1 review; the F001/F002/F010/F011/F014/F016/F017/F027/F029/F035
entries consulted here are unchanged). Those two checks were repeated against the
new revision; nothing else was invalidated. Files created by this review are
limited to the two authorized maintained files and the evidence directory; no
other writer appeared inside `build/cache/t13-parallel/source-fingerprints/`.
The working tree carries other agents' changes outside the authorized paths,
which were not inspected further.

## Delivery

Agent handoff summary retained below. Coordinator acceptance and the resulting
dispositions are recorded in section 9.

- **Own files:** [T13-source-fingerprint-review.md](T13-source-fingerprint-review.md),
  [T13-source-fingerprint-review.csv](T13-source-fingerprint-review.csv) and
  evidence/scripts under `build/cache/t13-parallel/source-fingerprints/`.
- **Verified results:** 455 stale source pins (300 translation-only, 125
  context-data, 30 pre-snapshot) with expected/current digests, canonical
  identities and evidence; current == committed HEAD; zero intersection with
  the T13 origin register; 125 empty local effects resolved by canonical
  references with 0 broken; 4 inherited pytest failures identified.
- **Open questions:** coordinator routing of the 30 historical pins and the 425
  snapshot pins; cross-reference consolidation; F027 disposal criterion;
  whether the late R0 reservation needs a process note. No T13-Q is closed.
- **Recommended next action:** the coordinator reviews this matrix, records the
  reservation discrepancy, and routes each class (translation pin refresh,
  context-data review, historical source disposition) to an owner before the
  next dependent mechanism lot or T13.7.

## 9. Coordinator acceptance and dispositions — 2026-10-01

Accepted as the bounded source/fingerprint/reference investigation; reservation
released. The coordinator used the maintained `inventory()`/`fingerprint()` and
current specification pins to independently check all 455 findings against the
live KB and the extracted committed revisions: 300 translation-only, 125 context
changes and 30 pre-snapshot mismatches. The 580 CSV finding keys are unique.
The probe also resolved all 379 empty local band nodes to 68 shared targets,
checked all 125 T13 shared references and confirmed no empty resolved text in
the 718-obligation current inventory. Retained evidence:
`build/cache/t13-parallel/source-fingerprints/coordinator-review.json`.
The external seven-minute semantic run is reused; it was not rerun as a complete
suite. The four failed identities were compared with the retained T13.1 baseline
XML; the separate historical audit failure remains unvalidated here.

| Class | Recorded disposition / next work | Owner and gate |
| --- | --- | --- |
| 300 translation-only pairs | Eligible for a narrowly reviewed pin refresh on this exact manifest; not a semantic rule repair. Verify the expected/current pair and non-i18n equality again at edit entry; change only approved digest fields. | Coordinator accountable; external executor unassigned until a separate user-launched dispatch. Accept exact pin-only diff and targeted verification. |
| 125 context-data pairs | Review the changed profile, access and band facts before repinning. Unchanged rule text does not prove unchanged recipients, eligibility or compiled behavior. Group by actual shared context files and trace affected consumers. | Coordinator performs the contract review, with independent review where interpretation changes; implementation executor unassigned. Accepted context/recipient/loadout evidence precedes any refresh. |
| 30 pre-snapshot pairs | Preserve the exact inherited identities and review their source, contract and mechanism assumptions individually. They are not covered by the translation-only disposition. | Coordinator routes source/mechanism owners before dependent reuse or T13.7; executors unassigned. Reviewed repairs/dispositions precede refresh and T14 certification. |
| F027 shared references | Resolved as a canonical-reference observation: no missing-text repair or duplicate prose is needed. Existing questions and combat proof are unaffected. | Coordinator accepted the reference disposition; recorded in the follow-up register. |
| 33 name/mechanic cross-references | Keep as qualified review hints. Do not merge findings, close origin obligations or assign causality from similar names or disjoint files. | Dependency tracing in the affected source/context/mechanism lot; F035 remains open. |

The existing `refresh_spec_digests.py` currently has only an unrestricted rewrite
and `--check`; it cannot select the 300 reviewed pairs. Do not run its default
rewrite for this disposition. A later pin-edit lot must use an exact pair allowlist
and preserve all unapproved pins, via a minimal extension of the existing tool or
a scoped edit. Do not change the digest algorithm or remove i18n from it here.
This tool limitation is part of F001's resume/closure conditions, not permission
to create a second audit framework.

The late reservation is already documented and resolved; no additional open
process issue is created. F001 stays open with the three repair/review classes;
F035 and all T13-Q questions retain their existing status. No pin, scope, source,
engine, generated artifact, UI/language or test was changed in this acceptance.
Post-edit documentation links are checked in `coordinator-documentation.xml`.
