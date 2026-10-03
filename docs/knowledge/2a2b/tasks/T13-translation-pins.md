# T13 — R0 translation-only source pins

Execution delivery for the bounded pin-edit lot reserved as **R0 —
translation-only source pins** in the [initiative checklist](../README.md). It
refreshes exactly the 300 `sources[].digest` pairs authorized by the
[read-only manifest](T13-translation-pin-manifest.json) and nothing else. This
document is the agent handoff, not acceptance: the coordinator reviews and
accepts, and no follow-up, question, task status or phase is closed here.

The lot follows the coordinator's disposition of the accepted
[R0 source-fingerprint review](T13-source-fingerprint-review.md) (§9): the 300
translation-only pairs are eligible for a narrowly reviewed pin refresh, while
the 125 context-data and 30 pre-snapshot pairs remain explicitly out of scope
under [T13-F001](T13-execution-follow-ups.md#t13-f001--inherited-semantic-failures-and-stale-source-fingerprints).
No rule, interpretation, scenario, dice set, expectation, mutation, binding,
scope digest, KB document, engine, translation, tool or shared register was
modified.

## 1. Entry review

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`
  (`chore: snapshot UI, localization and T13 planning`), worked and closed on
  the same revision. The working tree also carries other lots' uncommitted
  work, which was preserved untouched.
- The [manifest](T13-translation-pin-manifest.json) was verified before use:
  SHA-256 `1698b0019d5d685153e60245ebcacc804d5d2c1a8cc7b6eac6d49dd1bcf17fd2`,
  exactly the value dispatched, with 300 entries, 104 specification files and
  no duplicate `(file, specification, target)` key.
- All 104 working-tree specification files matched the manifest's
  `entry_spec_sha256` byte-for-byte at entry, including
  `tests/specs/semantic/grants/editorial-selected-blessings-modifications.yaml`
  with its pre-existing accepted Bloated Foulness change.
- `sources/knowledge` was clean against HEAD; the KB did not move during the
  lot. Reservation row R0 still reserves exactly the manifest spec files, the
  new document and `build/cache/t13-parallel/translation-pins/**`.
- The dispatch cited sections 2, 3 and 9 of the accepted review; the document
  contains all three (section 9 is the coordinator acceptance recorded on
  2026-10-01).

Entry input SHA-256 (captured in `entry-state.txt` / `entry-state.json`):

| Input | SHA-256 |
| --- | --- |
| `docs/knowledge/2a2b/README.md` | `ab937531…` (closing `a35319ce…`; concurrent edits by another lot, see §7) |
| `docs/knowledge/2a2b/tasks/T13-T15-remaining-plan.md` | `7aeb0a8a…` (unchanged) |
| `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.md` | `847d5232…` (unchanged) |
| `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.csv` | `72c4eb02…` (unchanged) |
| `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` | `80b499e7…` (closing `407f128e…`; concurrent edits elsewhere in the file) |
| `tests/specs/README.md` | `26d0e968…` (unchanged) |
| `docs/reference/verification.md` | `1dc2e473…` (unchanged) |
| `docs/guides/implement-and-verify-rules.md` | `e0d15965…` (unchanged) |
| `verification/inventory.py` | `e2460dc4…` (unchanged) |
| `verification/audit.py` | `98f0e8a3…` (unchanged) |
| `tools/verification/refresh_spec_digests.py` | `83fbe815…` (unchanged) |

## 2. Sources consulted

Checklist and reservations, remaining plan, the accepted fingerprint/reference
review and its 580-row matrix, the follow-up register (F001, F027, F035), the
semantic specification contract, the verification reference and the
implement-and-verify guide. Code consulted read-only:
[inventory.py](../../../../apps/combat-lab/mordheim_combat_lab/verification/inventory.py)
(`inventory()` / `fingerprint()`),
[audit.py](../../../../apps/combat-lab/mordheim_combat_lab/verification/audit.py)
(the `item.source_digest != source.get("digest")` comparison) and
[refresh_spec_digests.py](../../../../tools/verification/refresh_spec_digests.py).
The refresher's default rewrite was **not** executed: it cannot select pairs and
would have rewritten all 455 stale pins, including the 125 context and 30
historical pairs that are explicitly out of this lot.

The canonical fingerprint is the maintained one:

```text
sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                  separators=(",", ":")).encode("utf-8")).hexdigest()
```

with `value = {"rule": <band/skill row>, "context": {profiles.yaml,
equipment-access.yaml, band.yaml}}` for grants and the
`catalog/mechanics/close-combat.yaml` row for mechanic obligations.

## 3. Revalidation at edit entry (300/300)

A temporary script (`revalidate.py`, evidence folder) revalidated every
manifest entry before touching any file:

1. locate the exact specification by its `id` and the `sources` item by its
   `target` inside that specification (PyYAML `compose` marks, so the located
   scalar is unambiguous even in cluster files that repeat the same target in
   several specifications);
2. require the located `digest` text and value to equal `expected_digest`;
3. recompute the maintained fingerprint against the live KB with the maintained
   `inventory()` and require it to equal `current_digest`;
4. recompute the same fingerprint against the extracted pre-snapshot `eb85e95`
   KB and require it to equal `expected_digest`;
5. recursively strip every key ending in `_i18n` from both complete fingerprint
   inputs (rule plus the three context documents, or the catalogue row) and
   require the stripped structures to be equal — comparing rule text alone was
   not accepted.

Result: **300 ok, 0 blocked** (`revalidation.json`). All 300 had
`full_fingerprints_differ` and equal `_i18n`-stripped structures, confirming
the coordinator's `snapshot_translation_only` classification on the exact edit
entry. The live and `eb85e95` inventories both contain 718 obligations and every
`target` resolved in both.

## 4. Minimal substitution and proofs

`apply.py` (evidence folder) backed up each file byte-for-byte and replaced
only the located hex scalar text; no YAML was reserialized and no global string
replacement was used. After each file it proved four independent properties;
all 104 files passed:

1. **Relookup** — every authorized pair now reads `current_digest`, and the
   full `(specification, target) -> digest` map changed exactly on the
   authorized keys;
2. **Structured diff** — the loaded YAML before/after differs only at
   `specifications/<i>/sources/<j>/digest` leaves of authorized pairs, with
   old `expected_digest` -> new `current_digest`;
3. **Line diff** — line counts unchanged; every differing line is a
   `digest: <64-hex>` line; the number of changed lines per file equals its
   authorized pair count (300 total);
4. **Inverse** — replacing the new hex back at the same spans reproduces the
   original bytes exactly, and those bytes equal the backup.

`post-check.py` reran the proof from the backups independently of the apply
report: 104/104 files ok, exactly 300 changed lines, every backup matching the
manifest `entry_spec_sha256`, every authorized pair now current, the frozen
matrix unchanged, `git diff --check` clean, and `sources/knowledge` still clean.

## 5. Pairs and files

| | Count |
| --- | ---: |
| Authorized pairs examined / updated | 300 / 300 |
| Pairs blocked | 0 |
| Specification files updated | 104 |
| Distinct specifications | 250 |
| Obligation kinds | 281 grant, 19 mechanic |
| Categories | local 99, permanent 59, construction 57, stateful 29, interaction 29, contextual 21, priority 6 |
| Deferred pairs left untouched | 125 context-data + 30 pre-snapshot |

Largest files: `editorial-poison-immunity.yaml` 26, `editorial-no-pain.yaml`
22, `editorial-lustria-scaly-skin.yaml` 18, `interactions/damage-mitigation.yaml`
18, `editorial-category-prohibitions.yaml` 9. Every pair identity and both
digests are in the manifest; per-file before/after hashes are in
`apply-report.json` and the untouched originals in `backup/` (104 files).

## 6. Verification results

### 6.1 Semantic verification, exact before/after

`python -X utf8 tools/mordheim-utils.py verify --json`, same environment before
and after:

| Run | Exit | Errors | Identity set |
| --- | ---: | ---: | --- |
| Before | 1 | 455 | all `source changed` |
| After | 1 | 155 | all `source changed` |
| Removed | | 300 | exactly the 300 manifest identities (set equality verified) |
| Added / unclassified | | 0 / 0 | none |

The 155 remaining errors are exactly the deferred classes: 125
`snapshot_content_change` + 30 `pre_snapshot_pin_mismatch` (join against
`findings.json`, 0 unmatched). Refreshing the 300 pins did not surface any new
error in the unblocked specifications; `semantic_complete` remains `false` as
intended. Aggregate counts moved from 171 verified / 547 pending to 441 verified
/ 277 pending out of 718 obligations — this reflects the unblocked
specifications' additional checks, not certification, and is not forced green.

### 6.2 Structural verification

`python -X utf8 tools/mordheim-utils.py verify --structural --json`, exit 0
before and after: `structural_complete: true`, 1050 profiles compiled, 0
structural errors.

### 6.3 Focused semantic test suite

`python -X utf8 -m pytest tests/python/verification/test_semantics.py -q --tb=no -rf`:

| Run | Result | Notes |
| --- | --- | --- |
| Pre-edit (reused T13/R0 retained run, same pre-edit corpus and KB; `build/cache/t13-parallel/source-fingerprints/pytest-semantics.txt`) | 4 failed, 3779 passed | shapes accepted in the fingerprint review |
| Post-edit (fresh) | **1 failed, 3782 passed** in 640.23 s, exit 1 | same 3783 collected |

The three identities that stopped failing are
`test_bear_hug_has_a_real_source_link_and_detected_behavioural_mutations`,
`test_unverified_shared_consumer_keeps_editorial_grant_pending` and
`test_redundant_access_mutation_is_justified_not_counted_as_detected`; their
pre-edit failures were source-pin assertions, now current. The remaining
identity, `test_structural_success_is_not_semantic_success`, is the **same
failure as before**, with an unchanged cause: `assert report.errors == ()`
fails because the 155 deferred pins remain (traceback retained in
`pytest-semantics-failure-detail.txt`). No test was modified, skipped or
weakened, and no old failure count was forced.

### 6.4 Documentation test

`python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q`
was run after this document was written; result: 1 passed, exit 0. All local
links resolve and no other documentation file was touched by this lot.

## 7. Preservation of prior and concurrent work

- **Bloated Foulness change preserved.** `editorial-selected-blessings-modifications.yaml`
  was among the 104 files. Its backup equals the manifest entry hash, and the
  only difference between backup and edited file is the six authorized digest
  lines; the pre-existing interpretation/expectation diff is intact byte for
  byte.
- **Other writers.** During the lot the coordinator/other lots updated
  `docs/knowledge/2a2b/README.md` and `T13-execution-follow-ups.md` (R4 Barrage
  repair coordination). The R0 reservation row and the cited F001/F027/F035
  entries were re-read at closing; their content and scope are unchanged and
  no file of this lot overlaps them. No other writer touched the 104 spec
  files, the manifest or the matrix.
- **Re-hash at closing.** 104/104 edited files still equal their
  `apply-report.json` after-hashes after the full pytest run (mutation tests
  restore their temporary edits); 104/104 backups still equal the manifest
  entry hashes; the manifest (`1698b0019d…`) and matrix (`72c4eb02…`) are
  unchanged; `sources/knowledge` is clean; the full status shows exactly the
  104 spec files plus this new document for this lot.

## 8. Commands, exit codes and evidence

All commands from the repository root with `python -X utf8`. Evidence:
`build/cache/t13-parallel/translation-pins/` (ignored by Git).

| Step | Command | Exit | Artifact |
| --- | --- | ---: | --- |
| Entry state | `build/cache/t13-parallel/translation-pins/entry-check.py` | 0 | `entry-state.json/.txt` |
| Revalidation | `revalidate.py` | 0 | `revalidation.json/.txt` |
| Apply | `apply.py` | 0 | `apply-report.json`, `backup/**` |
| Independent post-check | `post-check.py` | 0 | `post-check.json` |
| Before semantic | `tools/mordheim-utils.py verify --json` | 1 | `verify-before.json` + stderr/exit |
| After semantic | `tools/mordheim-utils.py verify --json` | 1 | `verify-after.json` + stderr/exit |
| Structural | `tools/mordheim-utils.py verify --structural --json` | 0 | `structural-before/after.json` |
| Focused suite | `python -m pytest tests/python/verification/test_semantics.py -q --tb=no -rf` | 1 | `pytest-semantics-after.txt`, `.exit.txt` |
| Failure detail | single-test rerun with `--tb=long` | 1 | `pytest-semantics-failure-detail.txt` |
| Documentation | `python -m pytest tests/python/architecture/test_documentation.py -q` | 0 | recorded in §6.4 |
| Closing check | `closing-check.py` | 0 | `closing-check.json` |

`git diff --check -- tests/specs` is empty (exit 0); `git diff --numstat` shows
per file only the authorized digest lines (3/3 for `editorial-advanced-loadouts.yaml`,
26/26 for `editorial-poison-immunity.yaml`, and so on), except
`editorial-selected-blessings-modifications.yaml`, whose numstat also contains
the pre-existing accepted change.

## 9. Limits and deferred findings

- No parity/statistical run, coverage gate, native rebuild or execution, Web
  suite, T13.2 pytest matrices or integral CI was executed; the three commands
  above are the agreed scope. The semantic suite and structural layer ran on
  the live working tree with concurrent unrelated jobs active.
- The 125 context-data and 30 pre-snapshot pairs are untouched by design; they
  remain [T13-F001](T13-execution-follow-ups.md#t13-f001--inherited-semantic-failures-and-stale-source-fingerprints)
  work (coordinator contract review / source or mechanism disposition) and
  must not be repinned by this delivery. The four/three resolved semantic
  failures and the remaining `test_structural_success_is_not_semantic_success`
  failure inherit from that same residual set.
- F001's pin-edit gate is satisfied for the 300 pairs (exact allowlist, no
  bulk refresh, i18n keys preserved in the algorithm, pairs revalidated at
  entry); F001 itself stays open and no status is changed. F027 and F035 are
  untouched; no T13-Q question is closed.
- No new finding was discovered. No permanent tool was created; the scripts
  live in the ignored evidence folder as a reconstructible recipe.
- The `refresh_spec_digests.py` limitation recorded in the accepted review
  (no pair filter) remains true after this lot; a future pair-filtered
  extension or the same scoped-edit approach is needed for the remaining
  classes.

## Delivery

- **Own files:** this document plus evidence/scripts under
  `build/cache/t13-parallel/translation-pins/**`; the only working-tree changes
  made by this lot are the 300 `sources[].digest` values in the 104 manifest
  files and this new document. No commit, push, status change, manifest/matrix/register edit or
  tool change.
- **Verified results:** 300/300 pairs revalidated and updated (0 blocked), four
  independent minimality proofs per file, exact 455 -> 155 semantic error
  comparison with 300 removed / 0 added, structural green, focused suite
  4 failed -> 1 failed with identities and cause compared, documentation test
  green.
- **Open questions / deferred:** the 125 context-data and 30 pre-snapshot pairs
  remain with the coordinator under F001; acceptance of this lot belongs to the
  coordinator.
- **Recommended next action:** review the exact pin-only diff and the evidence,
  then route the 125 context-data pairs to their contract/consumer review and
  the 30 pre-snapshot pairs to their source/mechanism owners before any
  dependent reuse or T13.7.

## Coordinator acceptance — 2026-10-01

Accepted as the manifest-limited translation-only pin refresh; reservation
released. Independent spot checks are retained in
`build/cache/t13-parallel/translation-pins/coordinator-review.json`:

- all 300 delivered pins equal a freshly recomputed live fingerprint, including
a re-derived document sample across six files;
- the working tree differs from the byte-exact backups only in the 300
authorized digest lines (deferred pins untouched, the accepted Bloated Foulness
diff byte-for-byte preserved, HEAD unchanged);
- a fresh semantic run reproduces 455 -> 155 with exactly the 300 manifest
error identities removed, 0 added, and the 155 residual identities fully
classified as 125 context-data + 30 pre-snapshot;
- structural verification is green and `test_documentation.py` passes.

The focused-suite improvement (4 failed -> 1 failed) is reused from the
delivered run, not re-run in full; the remaining identity is the inherited
`test_structural_success_is_not_semantic_success` on the residual pins.
[T13-F001](T13-execution-follow-ups.md#t13-f001--inherited-semantic-failures-and-stale-source-fingerprints)
stays open with the 125 and 30 classes; no other finding, question, task status
or phase is closed. Acceptance records are the R0 row and the 2026-10-01
decision in the [initiative checklist](../README.md) and the F001 update in the
follow-up register. No commit or push was made.
