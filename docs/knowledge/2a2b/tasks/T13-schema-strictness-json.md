# T13-F052 — Structured finding members in the strictness CLI JSON

Delivery of lot **F052** by the reserved external executor on branch `2A2B`.
The strict editorial audit has carried precise `Finding.members` since F051, but
the CLI's `--json` projection serialized only kind, schema, path, detail and
documents, so a machine consumer had to parse human prose to learn which
members a finding names. Each element of `reported` now also carries
`members`: a JSON array with exactly the members of its finding, empty when the
finding has none. The change is one line in the existing projection.

**Status: delivered, awaiting independent review.** Nothing here accepts or
closes F052, T13 or T14; no shared register was edited, no ID was assigned, and
no commit or push was made. The reservation and the dispatch boundary are in the
[initiative checklist](../README.md); the finding is
[T13-F052 in the execution follow-up register](T13-execution-follow-ups.md#t13-f052--strictness-cli-json-omits-structured-finding-members);
it was reported as delivery P3 of
[the accepted F051 lot](T13-shared-schema-evidence.md#12-independent-coordinator-acceptance--2026-10-02),
whose auditor and tests are preserved untouched. The auditor contract it serves
is [the editorial contract README](../../../../contracts/knowledge-editorial-v1/README.md).

## 1. Scope and boundary

| | |
| --- | --- |
| Task | F052 — publish `Finding.members` in the strictness CLI JSON without changing any other behavior |
| Owned files | `tools/knowledge/audit_schema_strictness.py` (one added line); new `tests/python/knowledge/test_schema_strictness_cli.py`; this document; evidence under `build/cache/t13-parallel/schema-strictness-json/` |
| Left alone | The accepted F051 auditor `editorial_schema_audit.py` and its algorithm/justifications; `tests/python/knowledge/test_editorial_schemas.py`; `tests/python/knowledge/test_equipment_access_schema_contract.py`; `tests/python/knowledge/test_shared_schema_evidence.py`; contracts, schemas, knowledge base and staging, specifications/pins, engines, eligibility, TypeScript/Web (concurrent F050) and the shared coordination documents |
| Not done | No second serializer, no CLI refactor, no auditor change, no allowlist/justification change, no README or register edit, no new ID, no acceptance or phase closure, no commit or push |

The JSON document, its field order, the `--only` selection, the global
counters, the exit codes and the text report are unchanged; §4 shows the exact
difference.

## 2. Entry

* Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`; the accepted
  F044/F051 working-tree state was used as found and was **not** restored from
  HEAD. On entry, `git status --short` reported 249 dirty paths, all belonging
  to other concurrent lots; 248 produce no change attributable to this lot.
* Entry hashes were captured before any edit in
  `build/cache/t13-parallel/schema-strictness-json/entry-hashes.json`, with a
  byte copy of the CLI saved as `cli-before.py` and its text and `--json`
  outputs frozen as `cli-before--txt.json` / `cli-before--json.json`. The
  capture script writes entry copies only when absent, so repeating it never
  overwrites them (`closing-hashes.json` and `cli-after*` are the close
  captures).

| Input | Entry SHA-256 | Bytes |
| --- | --- | --- |
| `tools/knowledge/audit_schema_strictness.py` | `4acacdbae0f9a5259abef38bb3e2909dd7727ff4cccb225db12f66b944999291` | 3 415 |
| `editorial_schema_audit.py` (accepted F051 state) | `817cc882992262761b4b74de6ee5bd2fa420d1a23713507d6f60af7ae287e999` | 42 205 |
| `editorial_schemas.py` | `f9d4424525f5f204ac739c9a1dbc33023a25162d2ab8be4bffeae51803b469e6` | 14 823 |
| `tests/python/knowledge/test_editorial_schemas.py` | `f7218f8c805532ad998b84c01f9be63bfcec18600ee93bb3cb35b46a7a85c4c9` | 29 186 |
| `tests/python/knowledge/test_equipment_access_schema_contract.py` | `b1fd328631722fca3fe8f9af17b4afc26169d10cfc45ced83683e93ee7a46ef5` | 11 294 |
| `tests/python/knowledge/test_shared_schema_evidence.py` | `d48036f1a8ad13de7398117ef4c8e4b9a4898ba3434143f87a190b5f7cc4b894` | 22 175 |
| `contracts/knowledge-editorial-v1/README.md` (post-F051 P1 state) | `37bf1404b29574df2a75f75718e466755db08c7b263a8c9799de84432147c246` | 22 210 |
| `contracts/knowledge-editorial-v1/defs.schema.json` | `26cf39815f6a221a92e57521fb0bc42f4a0c40ecba9ab0d084b60502298ed7f8` | 16 093 |
| `contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json` | `a23c07e989fc81e054e9ff25ba13573c047d5ac53cdcd27881be431947252734` | 6 814 |
| `docs/knowledge/2a2b/README.md` (post-F051 state) | `3a051e842deb31ea9ff52010378b23a2db9ce37d3e5906164b725d515424a179` | 52 283 |
| `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` | `e5f26f1e844a2ccc1d24cc47cc9856f8f8188a8716b2caad1fa5e8105ccc46a6` | 74 083 |
| `docs/knowledge/2a2b/tasks/T13-shared-schema-evidence.md` | `380425b83d0d8267ebc7fcd6cd014fc75e15c0d76365a0904a2572572f1dead3` | 30 012 |
| `docs/reference/verification.md` | `c840d0784360d3c9a97980eef0f925b97eaac892d6a757082f30637f37d7979b` | 17 870 |

## 3. The defect and its reproducer

```text
python -X utf8 tools/knowledge/audit_schema_strictness.py --json
```

On entry the run exits 0 with 39 findings, 0 hard, 39 justified, 0
unjustified, 0 stale, and every `reported` element carries exactly
`kind`, `schema`, `path`, `detail`, `documents` — `members` is absent
(`cli-before--json.json`). The auditor behind it does expose
`Finding.members` (for example the pooled shared finding
`#/$defs/catalog_status` → `str:draft`); a consumer reading the JSON had to
infer the members from the English `detail`, which is not structured evidence.

The defect is an output-contract gap only: the audit semantics were accepted
with F051 and are not at issue here.

## 4. The change

One added line in the existing `reported` comprehension of `main()`:

```diff
                             "path": finding.path,
                             "detail": finding.detail,
                             "documents": list(finding.documents),
+                            "members": list(finding.members),
                         }
```

Contract for one `reported` element:

| | Before | After |
| --- | --- | --- |
| Fields | `kind`, `schema`, `path`, `detail`, `documents` | the same five plus `members`, in this order |
| `members` | absent | JSON array of strings with exactly `list(Finding.members)`, in the finding's order; `[]` when the finding has none (every hard finding) |

Because the new field is appended after the last existing one, deleting
`members` from every element of the new document reproduces the old document
field for field — the property `compare-json.py` checks on the captured runs.
The text report (`Finding.__str__` plus the summary line), the top-level
counters, the `--only` behavior and the exit code are untouched: the return
value already depended on the global `hard`/`unjustified`/stale lists, not on
`selected`.

## 5. Tests

`tests/python/knowledge/test_schema_strictness_cli.py` (new, 13 tests) loads the
delivered script with `importlib` and runs its real `main()`; the findings
provider (`editorial_schema_audit.audit_strictness`) and, per scenario, the
in-memory allowlist are replaced with `monkeypatch`, which restores them
automatically. No test mutates a live file, the contract or the knowledge base.
Expectations come from the supplied `Finding` objects and the CLI contract, not
from re-parsing `detail`.

| Group | Tests |
| --- | --- |
| The new field | a shared finding publishes every pooled member in order; a local finding publishes its own members; a hard finding without members publishes `[]` |
| The projection contract | all five existing fields and the order are preserved from the findings; the JSON document keeps its six documented top-level fields and the counters |
| Filters, counters, exit | `--only all` keeps finding order; `--only hard` reports only hard findings; `--only soft` reports justified then unjustified; a filter can hide a finding but not its counter or exit effect; a clean state exits 0 even with an empty selection; a stale justification fails the run even under `--only hard` |
| The text report | the text lines and the summary are exactly `str(finding)` plus the global counts, with and without a filter |

One deliberate detail: a scenario that expects exit 0 justifies exactly the
findings it supplies, because the CLI treats an allowlist entry with no finding
as stale — that behavior is part of the tested contract, not a test aid.

## 6. Validation run

| Command | Exit | Result |
| --- | --- | --- |
| `python -X utf8 -m pytest tests/python/knowledge/test_schema_strictness_cli.py -q` | 0 | 13 passed (`pytest-schema-strictness-cli.txt`) |
| `python -X utf8 -m pytest tests/python/knowledge/test_shared_schema_evidence.py -q` | 0 | F051 suite 16 passed (`pytest-shared-schema-evidence.txt`) |
| `python -X utf8 -m pytest tests/python/knowledge/test_editorial_schemas.py tests/python/knowledge/test_equipment_access_schema_contract.py -q` | 0 | F044/F051 gates 316 passed (`pytest-editorial.txt`) |
| CLI text and `--json` captures (`capture.py --phase entry` / `close`) | 0 | 39 findings, 0 hard, 39 justified, 0 unjustified, 0 stale, both before and after |
| `python -X utf8 filters.py` | 0 | counters preserved under `--only hard`/`soft`, documented selection, every reported element has a string array, field set exactly the six keys, 0 elements without `members` |
| `python -X utf8 compare-json.py` | 0 | new JSON identical to the old one after removing `members`, element by element; text byte-identical |
| `python -X utf8 check-members.py` | 0 | `reported` equals the maintained auditor's findings in order and field by field; counters match; 39/39 findings carry members |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q` | 0 | 1 passed |
| `git diff --check -- tools/knowledge/audit_schema_strictness.py` | 0 | clean; `git diff --stat` reports 1 insertion, 0 deletions |

## 7. JSON and text comparison on the committed corpus

| | Findings | Hard | Justified | Unjustified | Stale | Reported | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Before | 39 | 0 | 39 | 0 | 0 | 39 | 0 |
| After | 39 | 0 | 39 | 0 | 0 | 39 | 0 |

* `json_identical_without_members`: true; `every_element_identical_without_members`:
  true — the only delta anywhere in the document is the new field.
* `text_identical`: true, including the last line
  `39 findings: 0 hard, 39 justified, 0 unjustified, 0 stale justifications`.
* `check-members.json`: `reported_matches_the_auditor` and
  `counters_match_the_auditor` are true. The two shared-definition findings
  publish `#/$defs/catalog_status` → `["str:draft"]` and
  `#/$defs/characteristic_name` → `["str:BS", "str:I", "str:Ld", "str:M", "str:W"]`,
  the pooled evidence F051 computes.

## 8. Preservation of F044/F051 and the external boundary

* The accepted F051 auditor is byte-identical (`817cc882…`, 42 205 bytes, entry
  = closing) and was never edited; its 16-test suite and the 316 F044/F051
  gates pass. No allowlist entry, justification, schema or knowledge document
  changed.
* `input-drift.json` compares all captured inputs: the only differences are the
  two owned outputs of this lot — the CLI (entry `4acacdba…` → closing
  `446d8b9b138a9f298c6fc907152b6041f094011e0ae779f9f3d86bc9f17b4e2a`, 3 477
  bytes) and the new test suite (absent → `b0abedaa2bc4a9887e7453cca1e3da78d34295383859bc859f5f03625bd65dfb`,
  11 648 bytes). Every protected input is unchanged.
* The concurrent F050 TypeScript/Web work is outside this lot's boundary: it
  was neither measured nor touched, and nothing here accepts it.

## 9. Limits of this validation

* The real corpus is clean (39/0/39/0/0), so the exit-1 paths (hard,
  unjustified, stale) are exercised with synthetic findings in the unit suite;
  mutating canonical data to force a real failure was out of the question.
* No committed finding currently lacks members (all 39 carry at least one), so
  the `[]` case is covered only in isolation against a supplied hard finding.
  The code path is the same `list(finding.members)`; when canonical data
  produces a memberless finding, that run becomes the corpus witness.
* The unit suite pins the current top-level and per-element field sets. Adding
  a future CLI field must consciously update that test, which is intended: the
  JSON field set is a consumer contract now.
* The maintained corpus itself is exercised by the real CLI runs, `filters.py`
  and `check-members.py`, not by the unit suite, which replaces the findings
  provider in memory.

## 10. Pending proposals

None. The repair is one line, fully tested, and no deferred defect, stale
documentation or unverifiable claim was found in this lot. The two limits in §9
are conditions to revisit when canonical data changes, not work to schedule.

## 11. Handoff

```text
Task/lot: F052 — structured finding members in the strictness CLI JSON
  (external executor, user-launched reservation)
Entry revision: 1b7f7cf10b75a9d716c34c64039f5c908caed19e + the accepted
  F044/F051 working-tree state (entry hashes in
  build/cache/t13-parallel/schema-strictness-json/entry-hashes.json)
Files changed: tools/knowledge/audit_schema_strictness.py (one added line);
  new tests/python/knowledge/test_schema_strictness_cli.py;
  new docs/knowledge/2a2b/tasks/T13-schema-strictness-json.md
Decisions and sources: add `members: list(finding.members)` to the existing
  JSON projection only; take the values from the maintained Finding, never from
  detail; leave the auditor, the allowlist, the filters, the counters, the exit
  code and the text report exactly as accepted
Steps completed: entry capture, one-line change, 13 focused regressions,
  real-CLI before/after capture, JSON/text comparison, member verification
  against the maintained auditor, protected-input hash check, this document
Commands and exit codes: new suite 13 passed; F051 suite 16 passed; F044/F051
  gates 316 passed; real CLI text and --json exit 0 (39/0/39/0/0 before and
  after); filters.py, compare-json.py, check-members.py, capture.py and the
  documentation test all exit 0
Cases really covered: pooled shared finding with several members in order, a
  local finding with one member, a hard finding with `[]`, preservation of
  kind/schema/path/detail/documents, valid JSON with the documented top-level
  fields, --only all|hard|soft, counters under filters, exit 0 on a clean state,
  exit 1 for hard/unjustified/stale hidden by a filter, byte-identical text
Evidence: build/cache/t13-parallel/schema-strictness-json/ (entry-hashes.json,
  cli-before.py, cli-before--txt.json, cli-before--json.json, cli-after--txt.json,
  cli-after--json.json, closing-hashes.json,
  input-drift.json, json-comparison.json, filters.json, check-members.json,
  pytest-*.txt, capture.py, compare-json.py, filters.py, check-members.py)
Blockers/dependencies: none; the change is self-contained in the CLI
Files that may be released: the three files above, on acceptance
Next action for the coordinator: independent review of the one-line projection
  change, the new serialization regressions and the no-drift hash evidence,
  then record F052 in the register and release the reservation. No commit,
  push, acceptance or phase closure is made by this lot.
```

## 12. Independent coordinator acceptance — 2026-10-02

**Accepted; F052 resolved and reservation released.** T13/T14/T15 retain their
own acceptance barriers. Independent proof is retained in
`build/cache/t13-parallel/schema-strictness-json-coordinator-review/review.py`,
`independent-review.json` and `fresh-cli.json`.

- The immutable CLI original matches its entry hash. Removing exactly the new
  `members` projection line from the delivered bytes reproduces the original
  byte for byte: no other code or line-ending change is accepted.
- Fresh focal run: **29 passed** (13 CLI regressions and 16 F051 evidence tests).
  The executor's wider 316-test run remains retained evidence, not a repeated
  reviewer run.
- Fresh real subprocess JSON exits 0 and carries exact members for all 39
  maintained findings. Removing only those arrays gives the captured pre-change
  JSON field for field; a separate fresh text subprocess matches the original
  text exactly. Counts remain 39/0/39/0/0.
- The accepted auditor hash is still `817cc882…`. All 12 captured protected
  entry files were checked: no F052-boundary drift; the two coordinator records
  changed during F050 review and are explicitly classified as coordinator writes.
  No concurrent TypeScript work is claimed as reviewed by this CLI check.
- The delivered CLI SHA-256 is
  `446d8b9b138a9f298c6fc907152b6041f094011e0ae779f9f3d86bc9f17b4e2a`.

The suggested separate versioned output-schema artefact is not assigned as work:
the narrow maintained CLI regression already guards the output contract, and
no independent consumer/version-negotiation requirement was identified. Revisit
that choice if an actual external consumer needs an explicit versioned schema.
This does not create a current implementation gap.

Shared coordination records now resolve F052 and release its paths. No commit,
push, production refactor, specification change or agent launch was performed
during the review.
