# T13-F051 — Shared-definition evidence pooling in the strict editorial audit

Delivery of lot **F051** by the reserved external executor (agent B) on branch
`2A2B`. The lot repairs one defect of the strict editorial audit: a definition of
`defs.schema.json` shared by several document schemas was judged from the union
of the members each schema missed, and its detail was copied from the first
schema that reported it. The evidence is now pooled member by member, and the
detail is built from the members the finding carries.

**Status: delivered, awaiting independent review.** Nothing here accepts or
closes F051, T13 or T14; no shared register was edited, no ID was assigned, and
no commit or push was made. The reservation and the dispatch boundary are in the
[initiative checklist](../README.md); the finding is
[T13-F051 in the execution follow-up register](T13-execution-follow-ups.md#t13-f051--shared-definition-audit-pools-missing-members-by-union);
the accepted F044 lot it builds on is
[the equipment-access schema contract](T13-equipment-access-schema.md).

## 1. Scope and boundary

| | |
| --- | --- |
| Task | F051 — correct the aggregation of shared-definition member evidence in the editorial auditor |
| Owned files | `packages/python/knowledge/mordheim_knowledge/editorial_schema_audit.py`; new `tests/python/knowledge/test_shared_schema_evidence.py`; this document; evidence under `build/cache/t13-parallel/shared-schema-evidence/` |
| Left alone | `tests/python/knowledge/test_editorial_schemas.py` (unchanged: the repair needed no new case there), `tests/python/knowledge/test_equipment_access_schema_contract.py`, the schemas and the contract README, `tools/knowledge/audit_schema_strictness.py`, the knowledge base and staging, the shared coordination documents |
| Not done | No commit, no push, no agent launch, no acceptance, no phase closure, no justification refreshed to hide a change |

The repair is confined to the pooling layer of `audit_strictness()` plus the raw
evidence accessor it now needs. No second auditor, no general abstraction and no
change to the validators, the finding kinds, the hard-finding checks, the
justification predicates or `dead_definitions()`.

## 2. Entry

* Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`; the F044
  working-tree changes were present and were **not** restored from HEAD.
* Entry hashes captured before any edit, in
  `build/cache/t13-parallel/shared-schema-evidence/entry-hashes.json`, with a
  byte copy of the auditor saved as `auditor-before.py` (never overwritten).

| Input | Entry SHA-256 | Bytes |
| --- | --- | --- |
| `editorial_schema_audit.py` (accepted F044 state) | `714c5f875ea684ce397370fa60958b6a746026a20424776d84edc0781a011db0` | 41 346 |
| `tests/python/knowledge/test_editorial_schemas.py` | `f7218f8c805532ad998b84c01f9be63bfcec18600ee93bb3cb35b46a7a85c4c9` | 29 186 |
| `tests/python/knowledge/test_equipment_access_schema_contract.py` | `b1fd328631722fca3fe8f9af17b4afc26169d10cfc45ced83683e93ee7a46ef5` | 11 294 |
| `contracts/knowledge-editorial-v1/defs.schema.json` | `26cf39815f6a221a92e57521fb0bc42f4a0c40ecba9ab0d084b60502298ed7f8` | 16 093 |
| `contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json` | `a23c07e989fc81e054e9ff25ba13573c047d5ac53cdcd27881be431947252734` | 6 814 |
| `contracts/knowledge-editorial-v1/README.md` | `e84b36c18d1cbe5b1d57e644479f6c5c042a9f90d9bbd459fd48500cfd943971` | 21 808 |
| `tools/knowledge/audit_schema_strictness.py` | `4acacdbae0f9a5259abef38bb3e2909dd7727ff4cccb225db12f66b944999291` | 3 415 |

## 3. The defect

A definition of `defs.schema.json` is declared once and reached from several
document schemas. `(kind, path)` is therefore shared evidence, but the evidence
of each schema was kept apart and then combined as:

* **emission**, only when every schema that declared the path also *missed* a
  member (`reported_by == declared_by`);
* **members**, the union of each schema's missing members;
* **detail**, `setdefault` — the wording of the first schema that reported.

That combination is wrong in both directions. Two schemas using complementary
members back each member between them, yet the union of what each one missed
names all of them; and the preserved detail describes one schema's missing set,
not the members the finding carries.

### 3.1 Reproducer (durable, no ignored evidence needed)

In memory: one shared definition declaring `pair_a`, `pair_b` (and `pair_c` in
the third scenario), two document schemas whose documents observe complementary
members, and the real `audit_strictness()`. `defect-probe.py` runs the captured
pre-repair module and the repaired module over the same scenario and writes
`defect-probe.json`:

| Scenario | Before (accepted F044 module) | After (this lot) |
| --- | --- | --- |
| `alpha` observes `pair_a`, `beta` observes `pair_b` | `unused_property` at `#/$defs/display_text`, members `pair_a, pair_b`, detail `declared property never present: pair_b` | no finding |
| the same, with `pair_c` observed by nobody | members `pair_a, pair_b, pair_c`, detail `…: pair_b, pair_c` | members `pair_c`, detail `…: pair_c` |
| the same, with the mapping `{pair_b, pair_c}` justified | not stale — the wrong member set kept `pair_b` inside the finding | stale: `pair_b` is exercised by `beta` |

The scenario is exactly the one in the register and does not depend on the
F044 review cache: this document and the probe script are enough to rebuild it,
and no maintained page links into the ignored `build/cache/` evidence.

### 3.2 Why the union was wrong for any shared definition

Whether a member is exercised is a question about the whole contract, not about
one schema: `defs.schema.json` exists so several documents share one vocabulary.
The clause "aggregates evidence by definition instead of by use site" was already
the stated contract of the audit in
[the contract README](../../../../contracts/knowledge-editorial-v1/README.md);
the member union contradicted it.

## 4. The repair

### 4.1 Algorithm

Before, per audit: `unexercised()` returned `(kind, path, detail, members)` with
`members = declared − seen` of that one schema, and `audit_strictness()`
pooled the *missing* sets.

Now:

1. `_SchemaAudit.vocabulary()` exposes, per `(kind, path)`, the raw pair
   `(declared, observed)` this schema's documents back — properties, JSON types,
   enum values (in `_key` form, e.g. `str:draft`) and `oneOf`/`anyOf` branch
   indices (`"0"`, `"1"`, …). `Observed` counts a type or value only where it was
   actually seen, and a branch only when it matched.
2. `_SchemaAudit.unexercised()` computes `missing = sorted(declared − observed)`
   from that pair, so local findings are unchanged and the detail comes from the
   same members the finding carries (`_unexercised_detail`).
3. `audit_strictness()` keeps local findings and hard findings exactly as they
   were, and for a path that `_shared_definition()` recognises, pools
   `declared` and `observed` across every audit that reaches it. It emits **one**
   finding attributed to `defs.schema.json` when `declared − observed` over that
   union is non-empty, with `members` = those members and the detail built from
   them. The documented evidence pools the schemas that report the declaration,
   as before.
4. `stale_justifications()` needed no change: it already compares a member
   mapping with the members of the finding, so a member any document exercises
   now leaves the mapping stale instead of hiding inside a union.

The emission condition `reported_by == declared_by` disappeared with the
union-based pooling it protected: with per-member evidence it is subsumed —
a member is reported only when no schema observes it, which is exactly the case
where nobody could have exercised it.

### 4.2 Files

| File | Change |
| --- | --- |
| `editorial_schema_audit.py` | `_SchemaAudit.vocabulary()` added; `unexercised()` rebuilt on it; `_DETAIL_LEADS` + `_unexercised_detail()` added; `audit_strictness()` pools `declared`/`observed` per `(kind, path)` and builds the pooled detail from the pooled members; the now-dead `_SchemaAudit.declared()` accessor (its only caller was the union pooling) removed; the obsolete `rule_runtime.grant` allowlist entry removed with a comment stating why (§5.2); docstrings and module documentation updated |
| `test_shared_schema_evidence.py` (new) | 16 regressions, §6 |
| `T13-shared-schema-evidence.md` (new) | this document |

Final auditor: `817cc882992262761b4b74de6ee5bd2fa420d1a23713507d6f60af7ae287e999`
(42 205 B, CRLF preserved; every line ending is CRLF, 0 bare LF).

## 5. The committed corpus: exactly one finding fewer

`tools/knowledge/audit_schema_strictness.py`, text and `--json`, before and after
(`audit-before.txt|json`, `audit-after.txt|json`); the full identity comparison
is `findings-comparison.json` (`compare-findings.py` runs the captured
pre-repair module and the repaired one over `sources/knowledge`).

| | Findings | Hard | Justified | Unjustified | Stale | Exit |
| --- | --- | --- | --- | --- | --- | --- |
| Before (accepted F044 module) | 40 | 0 | 40 | 0 | 0 | 0 |
| After (this lot) | 39 | 0 | 39 | 0 | 0 | 0 |

`added = []` and `changed = []`: every other finding keeps its identity, its
detail, its members and its document count. Kinds after the repair: 21
`unused_enum_value`, 16 `unused_property`, 1 `unused_type`, 1 `dead_branch`
(local, `hireling-profile-dramatis-personae.yaml.schema.json#/$defs/unique_equipment.counts_as`).

### 5.1 The removed finding — individually explained

```
(defs.schema.json, unused_enum_value, #/$defs/rule_runtime.grant)
  before members:  str:band, str:none, str:profile, str:selectable   (the union)
  before detail:   declared value never present: str:band, str:profile, str:selectable
  before documents: 162
  after:           no finding
```

Measured per-schema evidence at that path (`shared-evidence-table.json`):

| Document schema | Documents | Declared | Observed |
| --- | --- | --- | --- |
| `catalog-skills.yaml.schema.json` | 2 | `band, none, profile, selectable` | `none` (23 rows, `catalog/skills/general.yaml`) |
| `special-rules.yaml.schema.json` | 161 | `band, none, profile, selectable` | `band` (659 rows), `profile` (1 805), `selectable` (437) |

Every value is exercised by a committed document, so the union named three
members the data backs and the detail disagreed with the members it carried.
This is the reported defect at real-corpus scale: the finding had to disappear.
`test_the_grant_vocabulary_has_no_unused_member_left` rebuilds the evidence from
the documents themselves and guards the outcome.

### 5.2 The allowlist entry that went with it

`JUSTIFIED_FINDINGS[("defs.schema.json", "unused_enum_value", "#/$defs/rule_runtime.grant")]`
("grant values of registry/runtime-schema.yaml, compared by the guardian test")
was removed, replaced by a comment that keeps the identity and the reason and
states why it cannot stay: it matches no finding, and an entry that stops
matching a finding is what `test_no_strictness_justification_has_gone_stale`
refuses (the same rule the contract README states). Nothing else in the
allowlist changed — no entry was renamed, narrowed, widened or reworded.

This is a consequence of the repair, not a justification refresh: the auditor
now reports *fewer* findings, and the vocabulary the entry mentioned keeps its
own guard — `test_runtime_enums_match_the_registry_contract` compares the enum
with `registry/runtime-schema.yaml` — and its own field test
(`test_special_rule_runtime_metadata_is_canonical_and_binary`,
`test_profile_special_rules_with_mechanic_ids_are_granted_automatically`). The
coordinator should still review this removal explicitly (§10 P2, P1).

### 5.3 Visibility of the defect class in the committed corpus

`shared-evidence-table.json` counts, for the committed knowledge base:

* 71 `(kind, path)` keys with evidence that belong to a shared definition;
* 43 of them are reached by more than one document schema;
* 10 have per-schema *missing* sets that differ from each other — the surface on
  which the union could misreport;
* 2 have a globally unused member and are the surviving pooled findings:
  `#/$defs/catalog_status` → `str:draft` (14 schemas, all missing it) and
  `#/$defs/characteristic_name` → `str:BS, str:I, str:Ld, str:M, str:W`
  (one schema).

Of the 10 divergent keys, nine were already suppressed by the old emission
condition (for example `#/$defs/rule_runtime.implemented` and
`#/$defs/runtime_effect.binding`), and `#/$defs/rule_runtime.grant` is the one
that was still emitted — because every schema that declared it also missed a
member. That is why the repair moves exactly one identity.

## 6. Tests

`tests/python/knowledge/test_shared_schema_evidence.py` (new, 16 tests, all
passing). Every probe replaces the maintained reader (`audit._documents`), the
merged schema and `dead_definitions()` **in memory**; the real audit runs once
against `sources/knowledge`, behind an `lru_cache`. No test writes to a schema, a
document, the knowledge base or the checkout (F049 isolation).

| Required behaviour | Test |
| --- | --- |
| Complementary use `pair_a`/`pair_b`: neither member is unused | `test_complementary_documents_pool_into_one_shared_declaration` (with a non-vacuity check that each schema alone misses the other's member) |
| One schema uses every member, another none: no global false positive | `test_a_member_used_by_any_schema_is_not_reported_by_another` |
| A member no document observes: one precise finding, detail = members | `test_a_member_no_document_observes_is_reported_once_with_its_own_detail` |
| Pooling with a single contributor behaves as before | `test_a_shared_definition_only_one_schema_reaches_reads_like_before` |
| Local definitions are not pooled | `test_a_local_definition_keeps_its_own_schema` |
| Schema/document order does not change the result | `test_the_pooled_result_is_stable_in_any_order` |
| Properties, types, enum values and branches pool; detail and members agree | `test_detail_and_members_agree_for_every_pooled_kind` |
| A member mapping covers only the members it names | `test_a_member_mapping_covers_only_the_members_it_names` |
| A member added later is not covered by an old mapping | `test_a_member_added_later_is_not_covered_by_an_old_mapping` |
| A member any schema exercises makes the global mapping stale | `test_a_member_any_schema_exercises_makes_the_global_mapping_stale` |
| Legacy text justifications still cover their whole path | `test_a_text_justification_still_covers_every_member_of_its_path` |
| Hard findings and local findings keep their schema | `test_pooling_never_hides_the_looseness_findings` |
| The committed corpus: no hard/unjustified/stale, detail = members | `test_the_committed_audit_still_tells_one_story_per_finding` |
| The surviving shared findings keep identity, members and ordering | `test_the_shared_definition_findings_are_pooled_and_unchanged` |
| The removed corpus finding has no unused member behind it | `test_the_grant_vocabulary_has_no_unused_member_left` |
| The F044 equipment-access mappings are preserved | `test_the_equipment_access_mappings_of_f044_are_preserved` |

`test_editorial_schemas.py` needed no new case: its two strictness gates already
state the corpus-level invariants (`test_the_contract_is_strict_about_the_committed_documents`,
`test_no_strictness_justification_has_gone_stale`) and both pass unchanged.

## 7. Validation run

| Command | Result |
| --- | --- |
| `python -X utf8 -m pytest tests/python/knowledge/test_shared_schema_evidence.py -q` | 16 passed (15.7 s) — `pytest-shared-schema-evidence.txt` |
| `python -X utf8 -m pytest tests/python/knowledge/test_editorial_schemas.py tests/python/knowledge/test_equipment_access_schema_contract.py -q` | 316 passed (146 s) — `pytest-editorial.txt`, the same count as the F044 acceptance |
| the four suites in one run | 333 passed (163.8 s) — `pytest-final.txt` |
| `python -X utf8 tools/knowledge/audit_schema_strictness.py` | 39 findings, 0 hard, 39 justified, 0 unjustified, 0 stale, exit 0 — `audit-after.txt` |
| `python -X utf8 tools/knowledge/audit_schema_strictness.py --json` | exit 0, same counts — `audit-after.json` |
| `python -X utf8 tools/mordheim-utils.py verify --structural --json` | exit 0, `structural_complete: true`, 0 errors, 1 050 profiles; the JSON is **identical** to the F044 artifact `equipment-access-schema/verify-structural.json` — `verify-structural.json` |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q` | 1 passed — every local link in this document resolves |
| `python -X utf8 build/cache/t13-parallel/shared-schema-evidence/compare-findings.py` | before/after finding sets: 40 → 39, one removal, 0 additions, 0 changes |
| `python -X utf8 build/cache/t13-parallel/shared-schema-evidence/defect-probe.py` | the §3.1 table, from the captured pre-repair module and the repaired one |
| `python -X utf8 build/cache/t13-parallel/shared-schema-evidence/closing-check.py` | 705 frozen F044 inputs: 704 match, 1 external drift (F050, §7.1), 0 F051-boundary drift; every boundary file unchanged since entry |

The repair does not touch the structural route: `audit_strictness` is called only
by `tools/knowledge/audit_schema_strictness.py` and the knowledge tests, never by
`verify`, whose structural layer validates through
`editorial_schemas.validate_*`. The structural run above was kept anyway and
reproduced the accepted result byte for byte.

### 7.1 External state observed at the close

The closing hash check (`closing-check.py`, `closing-check.json`) recomputes the
705 inputs the F044 dispatch froze. At the close, 704 match and one does not:
`tests/typescript/application/rules/warband-reference.test.ts`, modified at
`2026-10-02T04:49:39Z` — about half an hour after this lot's entry capture — by
the concurrently reserved **F050 TypeScript dispatch (external agent A)**, whose
diff adds the rendered-citation assertions for that finding and names F050 in
its comment:

| | SHA-256 |
| --- | --- |
| F044 dispatch frozen value | `d7591c2c5ba605c5973493690660d340c3340876dc10fc7c6e401aca1de7387a` |
| At this lot's close | `b05b6ea50263d055b8d642f520bdbf754a465f55fdcbb2d49293855a6c1664d6` |

This lot did not open, edit or restore that file (nor
`packages/typescript/application/rules/warband-reference.ts`, which is
unchanged); the F051 boundary has zero drift, and every other frozen input
matches. The coordinator should attribute the single drift to F050, not to this
lot, and should not read it as an F044 regression.

## 8. F044 preservation

* The two F044 justifications are untouched and still cover exactly the members
  the audit reports: `#/$defs/equipment_list` → `notes, notes_i18n`;
  `#/$defs/equipment_list.applies_to.profile_types[]` → `str:animal, str:henchman,
  str:summoned` (pinned again in the new suite, and by the F044 suite itself).
* Both findings are local to `equipment-access.yaml.schema.json`; the pooling
  change cannot reach them, and `findings-comparison.json` shows their detail,
  members and document counts unchanged.
* `tests/python/knowledge/test_editorial_schemas.py` and
  `tests/python/knowledge/test_equipment_access_schema_contract.py` are
  byte-identical to the entry and pass (316 tests).
* The contract README, `equipment-access.yaml.schema.json` and
  `defs.schema.json` are byte-identical to the entry.

## 9. Limits

* The in-memory probes replace the maintained reader; they prove the pooling
  semantics and the finding shape, not the reading of YAML from disk. The
  real-corpus tests cover that side.
* A *reported* pooled finding of the real corpus can only be a property or an
  enum value today (`catalog_status`, `characteristic_name`). The pooled type and
  branch paths are exercised by synthetic documents, and the branch path also has
  real evidence without a finding: `#/$defs/runtime_effect.binding`, whose branch
  `1` is missed by `catalog-skills.yaml.schema.json` and matched by
  `special-rules.yaml.schema.json` (`shared-evidence-table.json`).
* The evidence table is a measurement of the current knowledge base; it is not a
  pin, and a new document legitimately changes it.
* The `--json` output of the strictness CLI still omits `members`, so machine
  consumers cannot see the member evidence this lot guarantees (§10 P3).
* No browser, product flow, TypeScript or Web path was exercised; F051 is an
  editorial-audit lot and says nothing about F050 or about any visible product
  behaviour.

## 10. Pending proposals

No ID is assigned here; the coordinator owns the register and may route, rename
or reject each one.

**P1 — the strictness section of the contract README lists an example the repair
empties.** *Reproducer:* `grep -n "runtime-schema" packages/python/knowledge/mordheim_knowledge/editorial_schema_audit.py`
now finds only the removal comment, while
`contracts/knowledge-editorial-v1/README.md` still offers "a value of
`registry/runtime-schema.yaml`" among the examples of justified declarations.
*Impact:* documentation names an example with no entry behind it; the runtime
vocabulary is in fact guarded by `test_runtime_enums_match_the_registry_contract`,
which the text does not say. *Dependency:* the F051 acceptance (the README was
read-only in this dispatch). *Owner:* coordinator /
editorial-contract owner. *Resume:* before the next acceptance that quotes the
strictness section. *Close when:* the example list names a live justification or
states the registry guard explicitly, and the documentation run stays green.

**P2 — the F044 acceptance text still says "40 findings".** *Reproducer:*
`python -X utf8 tools/knowledge/audit_schema_strictness.py` now reports 39; the
F044 row of the [initiative checklist](../README.md) and §11 of
[the F044 delivery](T13-equipment-access-schema.md) state 40. *Impact:* a
coordination record keeps a count that no longer matches the gate; a reader may
think the gate regressed or that a finding is missing. *Dependency:* F051
acceptance. *Owner:* coordinator. *Resume:* when F051 is recorded in the
register. *Close when:* those statements describe the current count, link this
delivery, and state that the removed identity was a false finding.

**P3 — the strictness CLI `--json` omits `members`.** *Reproducer:*
`python -X utf8 tools/knowledge/audit_schema_strictness.py --json` lists
`kind/schema/path/detail/documents`, never the members the finding carries.
*Impact:* machine consumers (and the coordinator's spot checks) cannot compare
member evidence; they can only parse the human detail. *Dependency:* the tool
was read-only in this dispatch. *Owner:* tooling owner. *Resume:* next
maintenance of the strictness tool. *Close when:* `--json` reports `members` and
a test pins the shape for a pooled finding.

**P4 — the pooled evidence has no pin for the *reported* type and branch kinds
in the committed corpus.** *Reproducer:* the only real `unused_type` and
`dead_branch` findings are local (`catalog-skills.yaml.schema.json`,
`hireling-profile-dramatis-personae.yaml.schema.json`); the shared paths of those
kinds are only exercised by synthetic documents plus the empty-global-missing
`#/$defs/runtime_effect.binding`. *Impact:* a future change that silences or
breaks pooled type/branch evidence in real data would not be caught by a
corpus-level assertion. *Dependency:* a committed document must exercise
complementary types or branches of one shared definition; none does today.
*Owner:* T13/T15 editorial owner. *Resume:* when such a document or a shared
branch declaration lands, or when a later lot touches the pooling again.
*Close when:* a real-corpus test (or an equivalent evidence artifact) witnesses
the pooled type and branch paths, or their pooling is removed with a reason.

## 11. Handoff

```text
Task/lot: F051 — shared-definition evidence pooling (external agent B)
Entry revision: 1b7f7cf10b75a9d716c34c64039f5c908caed19e + the F044 working-tree
  changes (entry hashes in build/cache/t13-parallel/shared-schema-evidence/entry-hashes.json)
Files changed: packages/python/knowledge/mordheim_knowledge/editorial_schema_audit.py;
  new tests/python/knowledge/test_shared_schema_evidence.py;
  new docs/knowledge/2a2b/tasks/T13-shared-schema-evidence.md
Decisions and sources: pool declared/observed per (kind, path) across the schemas
  that share a definition; build the pooled detail from the pooled members; keep
  local and hard findings, the allowlist predicates and dead_definitions() as
  they were; remove the one allowlist entry whose finding the repair proves false
Steps completed: entry capture, defect probe, repair, 16 regressions, corpus
  comparison, full validation, closing hashes, this document
Commands and exit codes: new suite 16 passed; editorial + equipment-access 316
  passed; strictness CLI text and --json exit 0 (39/0/39/0/0); structural verify
  exit 0 and identical to the F044 artifact (1050 profiles); documentation test
  1 passed; compare/probe/closing scripts exit 0
Cases really covered: complementary members, one unused member, one schema using
  everything, single contributor, local definitions, order stability, member
  scope, added members, member-scoped staleness, text justifications, hard
  findings, the committed corpus and the two F044 mappings
Evidence: build/cache/t13-parallel/shared-schema-evidence/ (entry-hashes.json,
  auditor-before.py, audit-before/after.txt|json, findings-comparison.json,
  defect-probe.json, shared-evidence-table.json, pytest-*.txt,
  verify-structural.json, closing-check.json, the scripts that build them)
Blockers/dependencies: none; the repair is self-contained in the auditor. The
  corpus delta needs the coordinator's explicit review (§5.1, §5.2)
Files that may be released: the three files above, on acceptance
Next action for the coordinator: independent review of the pooling algorithm and
  of the single removed finding/entry, then record F051 in the register; route
  P1–P4 as it sees fit. No commit, push or acceptance is made by this lot.
```

## 12. Independent coordinator acceptance — 2026-10-02

**Accepted; F051 resolved and reservation released.** This is editorial-auditor
acceptance, not T13/T14 closure or acceptance of the concurrent F050 work.

Independent evidence is retained in
`build/cache/t13-parallel/shared-schema-evidence-coordinator-review/review.py`
and `independent-review.json`. The reviewer independently confirmed:

- The immutable original auditor has the accepted F044 hash; the current
  auditor matches the delivery's closing hash. The original is not HEAD bytes.
- The only allowlist deletion is `defs.schema.json / unused_enum_value /
  #/$defs/rule_runtime.grant`; every other value, including the F044 mappings,
  is unchanged. The justification predicates, document reader, dead-definition
  and top-level hard/unjustified functions are AST-identical to the original.
- Full finding records compared independently: **40 to 39, exactly one removal,
  no additions and no changes** to the other identities, detail, members or
  document labels. Direct YAML counts are `band=659`, `profile=1805`,
  `selectable=437`, `none=23`; they exhaust the declared grant enum. The removed
  finding was false, and retaining its justification would be obsolete.
- A separate in-memory `a,b,c` probe observes `a` and `b` in different schemas
  and reports exactly `c`, with matching detail and members. Fresh focused
  tests: **27 passed** (shared evidence plus F044 contract regressions).
  The executor's broader **333 passed** run is retained; it was not repeated.
- Of 705 frozen F044 source/protected inputs, the sole changed path is the
  concurrently reserved F050 `warband-reference.test.ts`. There is no F051
  boundary drift. This review does not accept that external diff. All six
  checked F051 entry-boundary tests/contracts/CLI inputs were unchanged before
  coordinator documentation updates.

Disposition of section 10 proposals:

1. **P1 resolved now:** the contract README removes the obsolete unused-value
   example and states the maintained runtime-enum guard and global evidence rule.
   This documentation edit is by the coordinator, after checking the executor's
   protected bytes; it was not an out-of-reservation executor change.
2. **P2 resolved now:** F044's 40 is preserved as its dated historical result;
   the README and F044 delivery link this subsequent accepted 39-finding state.
   Acceptance history is not rewritten as if F044 originally reported 39.
3. **P3 registered as T13-F052:** CLI JSON does not expose `Finding.members`.
   Add the explicit structured field with a meaningful serialization regression
   in a separate tooling lot; no CLI edit is made by this review.
4. **P4 dismissed as a required repair:** there is no current canonical witness
   for a reported pooled type/branch gap, and source rows must not be invented
   to provide one. Isolated tests cover both kinds and the real corpus exercises
   the shared binding branch's complementary use. Revisit corpus-specific
   assertions when canonical data actually introduces the relevant declaration
   or this aggregation changes. This is a future test-maintenance condition,
   not a current defect or a reason to remove working pooling.

The related register and reservation are updated. No commit, push, agent launch,
engine change, specification refresh or phase closure was performed.
