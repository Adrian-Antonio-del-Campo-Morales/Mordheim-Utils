# T13 — R0/F044 equipment-access schema contract

Status: implementation ready for independent review. F044 and T13 are **not**
accepted or closed by this document; the coordinator owns the register and the
acceptance. Nothing was committed, pushed or delegated, and no coordinator
README, plan or shared register was edited.

The lot resolves the inherited strictness failure without weakening the audit:
both reported declarations are **retained** and justified member by member
against the maintained reference projection, while a property or enum value
added later to the same declaration stays an unjustified finding, and a mapped
member the documents start exercising turns the justification stale.

## 1. Entry state, dispatch and hashes

- Checkout `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`, branch `2A2B`, HEAD
  `1b7f7cf10b75a9d716c34c64039f5c908caed19e`; 233 dirty entries belonging to
  concurrent lots were preserved; no worktree, branch or stash operation was
  used.
- Dispatch read, never written:
  `build/cache/t13-parallel/equipment-access-schema-dispatch/{entry.json,baseline.txt,backup/**}`.
  Its four owned files and five protected inputs hashed to the recorded
  digests at entry and at closing; the backup copies were not touched.
- Baseline (`baseline.txt`, dispatch run):
  `python -X utf8 -m pytest tests/python/knowledge/test_editorial_schemas.py -q -k "contract_is_strict_about_the_committed_documents or no_strictness_justification_has_gone_stale"`
  → **1 failed, 1 passed, 303 deselected (22.60 s), EXIT 1**. The failure is
  `test_the_contract_is_strict_about_the_committed_documents` (line 368) with
  exactly two findings:

  | Finding | Detail |
  | --- | --- |
  | `unused_property: equipment-access.yaml.schema.json#/$defs/equipment_list` | declared property never present: `notes`, `notes_i18n` (161 documents) |
  | `unused_enum_value: equipment-access.yaml.schema.json#/$defs/equipment_list.applies_to.profile_types[]` | declared value never present: `str:animal`, `str:henchman`, `str:summoned` (`mordheim/underworld-alliance-mim/equipment-access.yaml`) |

  The stale-justification gate passed at entry and still passes.

Owned files, entry → closing (sha256):

| File | Entry | Closing |
| --- | --- | --- |
| `packages/python/knowledge/mordheim_knowledge/editorial_schema_audit.py` | `483ad23e917bfcc5f0258a51ff80235aa29c0a2580ab4a3e49ac2d8f6d71787f` | `714c5f875ea684ce397370fa60958b6a746026a20424776d84edc0781a011db0` (41 346 B) |
| `contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json` | `047a3367236a11bb0c5e55e330b5737b1f6380f8c718fdf8ec075826d7a0cacb` | `a23c07e989fc81e054e9ff25ba13573c047d5ac53cdcd27881be431947252734` (6 814 B) |
| `contracts/knowledge-editorial-v1/README.md` | `cc5ac5e28e836c84666befe1c0600fa38ed996ba198692003be2445f07fa32ca` | `e84b36c18d1cbe5b1d57e644479f6c5c042a9f90d9bbd459fd48500cfd943971` (21 808 B) |
| `tests/python/knowledge/test_editorial_schemas.py` | `89f76a4f15f4f29e3ee57eea4786552936a272d0927ff5ef080b87f82ac078aa` | `f7218f8c805532ad998b84c01f9be63bfcec18600ee93bb3cb35b46a7a85c4c9` (29 186 B) |
| `tests/python/knowledge/test_equipment_access_schema_contract.py` (new) | — | `b1fd328631722fca3fe8f9af17b4afc26169d10cfc45ced83683e93ee7a46ef5` (11 294 B) |
| `tests/typescript/application/rules/equipment-access-contract.test.ts` (new) | — | `9b513a10d5024f2f1fad99e27d4fad1c442fba56afb2f90576156172cbb4745e` (5 019 B) |
| `docs/knowledge/2a2b/tasks/T13-equipment-access-schema.md` (new) | — | recorded in `evidence-index.txt` |

Protected inputs remain byte-identical (section 8): `editorial_schemas.py`
`f9d44245…`, `defs.schema.json` `26cf3981…`,
`bands/mordheim/underworld-alliance-mim/equipment-access.yaml` `da3b447e…`,
`application/rules/warband-reference.ts` `2ffa2115…`,
`application/rules/warband-reference.test.ts` `d7591c2c…`.

## 2. Sources, contracts and consumers consulted

- `docs/knowledge/2a2b/README.md` (reservation row), the F044/F049 entries of
  `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` (F045/F046 read to
  separate unrelated failures), `T13-T15-remaining-plan.md`, and
  `T13-catalogue-contracts.md` §9/§11 (F044 revalidation and the F049
  isolation decision taken after that lot's mutation incident).
- Contract: `contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json`
  (`$defs.equipment_list` and its `applies_to`), `defs.schema.json`
  (`$defs/display_text`, `$defs/i18n`), `profiles.yaml.schema.json` (the
  `profile.type` vocabulary), `README.md` (strictness semantics).
- Auditor: `mordheim_knowledge/editorial_schema_audit.py` (finding kinds,
  `JUSTIFIED_FINDINGS`, `unjustified_findings`, `stale_justifications`) and
  `editorial_schemas.py` (`schema_for`, `problems_of`; reused, never copied).
- Consumers: `tools/knowledge/generate_knowledge_web.py`
  (`_build_campaign_section` → `_build_warband_reference`, which publishes
  every `equipment_lists` row through `_row`, keeping `notes`, `notes_i18n` and
  `applies_to`), and
  `packages/typescript/application/rules/warband-reference.ts`, which resolves
  `notes`/`notes_i18n` per locale (`recordText(list, "notes", locale)`) and
  selects a list's recipients with
  `ids(list.applies_to.profile_types).includes(String(profile.type))`.
  `warband-reference.test.ts` was read as the style/behaviour reference.
- Data: all 161 `bands/*/*/equipment-access.yaml` documents (366 lists),
  all `bands/*/*/profiles.yaml`, and `tests/support/kb-artefact.ts` (how the
  published artefact is assembled). Showing recipients is display only; the
  executable eligibility module was not touched and no permission changed.

## 3. Disposition of each reported declaration

Measured data at entry: of the 366 committed lists, all carry
`id`/`name`/`name_i18n`/`items`/`source`, four carry `loadouts`, exactly one
carries `applies_to` (`underworld-alliance-mim` → `miscellaneous-items` →
`["hero"]`), and **none** carries a list-level note. Canonical profiles use the
whole `profile.type` vocabulary: `hero` 554, `henchman` 484, `animal` 17,
`summoned` 1.

### 3.1 `equipment_list.notes` / `notes_i18n` — retained, justified exactly

- **Not used by the current documents, but backed by a contract and a
  consumer.** The generator publishes the list row unchanged
  (`_build_warband_reference` → `_row`), and the maintained reference sheet
  resolves a list-level note per locale and renders it
  (`warband-reference.ts:128`). Deleting the pair would silently remove a
  capability of the projection that no data has needed *yet*.
- **No canonical data is invented to exercise it.** The finding is genuine:
  the editorial note of a list has simply not been written by any source
  transcribed so far. The declaration is kept with a precise justification and
  a test that proves the projection consumes it (section 6).
- **Schema documentation added** (descriptions only; shape and `enum`
  untouched) so the contract states why the pair is kept.

### 3.2 `applies_to.profile_types`: `animal`, `henchman`, `summoned` — retained, justified exactly

- **Backed by a sibling vocabulary, not by wishful data.** The four values are
  the same vocabulary `profiles.yaml` declares for `profile.type`, and
  canonical profiles exercise all four (section above), with `animal` and
  `summoned` described there as creatures attached to a warband. The consumer
  selects recipients with exactly that vocabulary, and the schema description
  of `applies_to` says the block names the recipients the source prints — a
  henchman or creature list is a valid recipient declaration even if no list
  prints one today.
- **Narrowing the enum to `hero` would misdescribe the shared vocabulary** and
  break future printed recipient blocks; the retained values are justified one
  by one instead.
- Only one equipment-access document prints a recipient block today, which is
  why the audit reports the finding; the value set itself is not orphaned.

## 4. The precision control (why the existing allowlist was not enough)

`JUSTIFIED_FINDINGS` is keyed by `(schema, kind, path)`, and a finding
aggregates the members missing at that path. Adding a whole-path entry for
`#/$defs/equipment_list` would have silently excused **any future property**
added to the definition, and likewise for the recipient enum. The requested
precision is therefore part of the repair.

Changed in `editorial_schema_audit.py` (no general rewrite):

- `Finding` gained a structured `members: tuple[str, ...]` field, populated
  from the same `missing` sets that build the human-readable detail.
- `_SchemaAudit.unexercised()` now returns `(kind, path, detail, members)`;
  `audit_strictness()` passes the members through, and pools them as a union
  when several schemas share a `defs.schema.json` definition.
- `JUSTIFIED_FINDINGS` values may stay a text reason (**whole finding at the
  path**, the previous behaviour — every pre-existing entry is untouched) or be
  a mapping from exact members (property names, `_key` enum values such as
  `str:animal`, branch indices) to their own reason.
- `unjustified_findings()` uses `_justified()`: a mapping covers a finding only
  when every reported member is named; an unmapped member keeps the finding
  unjustified.
- `stale_justifications()` also reports an entry whose mapped member is
  exercised again by the documents (the finding shrinks), forcing the entry to
  be narrowed — the member-level counterpart of the existing staleness gate.

F044 entries (mapping form, exactly the members the audit reports):

```python
("equipment-access.yaml.schema.json", "unused_property", "#/$defs/equipment_list"): {
    "notes": "list-level note of the published reference sheet; resolved per locale by warband-reference.ts",
    "notes_i18n": "Spanish translation of the same list-level note",
},
("equipment-access.yaml.schema.json", "unused_enum_value",
 "#/$defs/equipment_list.applies_to.profile_types[]"): {
    "str:animal": "a beast attached to a warband is a canonical `profile.type` of profiles.yaml",
    "str:henchman": "a list printed for a henchman group is a valid recipient; `henchman` is a canonical `profile.type`",
    "str:summoned": "a summoned creature is a canonical `profile.type` of profiles.yaml",
},
```

Preserved unchanged: closed-object and unknown-key rejection, shape/type
validation, justification staleness detection, unjustified-finding detection,
and every justification unrelated to F044 (no existing entry changed value or
semantics).

## 5. Changes implemented

| File | Change |
| --- | --- |
| `packages/python/knowledge/mordheim_knowledge/editorial_schema_audit.py` | member field, member-aware allowlist and staleness, F044 entries, comments (owned) |
| `contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json` | descriptions for the retained declarations only; `enum`, required keys and `additionalProperties: false` untouched (owned) |
| `contracts/knowledge-editorial-v1/README.md` | the member form of a justification, the disposition and its staleness rule (owned) |
| `tests/python/knowledge/test_editorial_schemas.py` | one line: the mechanism test unpacks the new 4-tuple of `unexercised()` (owned) |
| `tests/python/knowledge/test_equipment_access_schema_contract.py` (new) | 11 tests: disposition, vocabulary, shapes, isolated negative probes |
| `tests/typescript/application/rules/equipment-access-contract.test.ts` (new) | 2 tests: list-level EN/ES note resolution and recipient selection through `WarbandReferences` |
| `docs/knowledge/2a2b/tasks/T13-equipment-access-schema.md` (new) | this delivery |

No KB, 2A/2B tree, production consumer, eligibility module, engine, interface,
specification, pin, budget or generated artefact was modified.

## 6. Evidence: positive, negative and real consumption

**Positive disposition (Python).** The two real findings are present and their
justifications name exactly their members; the equipment-access schema has no
other unjustified or stale finding. The recipient vocabulary equals
`profiles.yaml`'s `profile.type` enum, and canonical profiles exercise
`animal`, `henchman` and `summoned`. Valid notes (`notes` plus `notes_i18n.es`)
validate, and every declared recipient kind validates.

**Negative probes (isolated).**

- A property added to `$defs.equipment_list` (and another added to
  `$defs.equipment_entry`) in an in-memory clone of the merged schema is still
  an unjustified finding, with `illustration` alongside the justified members.
- A fifth recipient value (`swarm`) in the cloned enum is still an unjustified
  finding.
- An isolated synthetic package under `tmp_path` whose list carries `notes`
  leaves the finding with `notes_i18n` only and turns the entry **stale**; the
  same package without notes is neither unjustified nor stale. This proves the
  staleness rule works at member level, and no live or protected file is
  written (F049).
- Malformed note blocks (empty canonical, non-string, `en` mirror, empty or
  non-object `es`), unknown/empty/duplicated recipient values, an empty
  `applies_to` and an undeclared key inside it are all rejected by the
  maintained validator.
- The full maintained audit and its CLI remain green:
  `tools/knowledge/audit_schema_strictness.py` → 40 findings, 0 hard,
  40 justified, 0 unjustified, 0 stale, EXIT 0.

**Real consumption (TypeScript).** The new suite drives the maintained reader
and projector with a synthetic fixture shaped like the generator's output:
`notes`/`notes_i18n` resolve to `"Synthetic list note."` / `"Nota sintética de
la lista."`, and `applies_to.profile_types` selects exactly the matching
profiles (`hero`+`animal` list → hero and beast, not the henchman; `henchman`
list → the henchman only, in ES too; `summoned` list → no profile, the
non-matching control). The fixture is labelled synthetic and changes no
eligibility: it only proves the projection reads the two declarations.

## 7. Verification runs

| # | Command | Exit | Result |
| --- | --- | --- | --- |
| 1 | `pytest tests/python/knowledge/test_equipment_access_schema_contract.py -q` (`pytest-equipment-access.txt`) | 0 | 11 passed (33.44 s) |
| 2 | `pytest tests/python/knowledge/test_editorial_schemas.py -q -k "contract_is_strict_about_the_committed_documents or no_strictness_justification_has_gone_stale"` (`gate-strictness.txt`) | 0 | 2 passed, 303 deselected (21.22 s) — the entry failure is fixed |
| 3 | `pytest tests/python/knowledge/test_editorial_schemas.py -q` (`pytest-editorial-schemas.txt`) | 0 | 305 passed (98.25 s) |
| 4 | `npx vitest run ../../tests/typescript/application/rules/equipment-access-contract.test.ts` (`vitest-equipment-access.txt`) | 0 | 2 passed |
| 4b | `npx vitest run ../../tests/typescript/application/rules/warband-reference.test.ts` (`vitest-warband-reference.txt`) | 1 | 2 failed, 6 passed — **inherited F042 fallout, not this lot** (section 9, proposal 2) |
| 5 | `npx tsc --noEmit` in `packages/typescript` (`typecheck-campaign-web-core.txt`) | 0 | clean. The test tree is outside every `tsconfig`, so this covers the packages (documented limit) |
| 6 | `pytest tests/python/knowledge/test_catalogue_contract_regressions.py tests/python/knowledge/test_campaign_catalogs.py -q` (`pytest-catalogue-regressions.txt`) | 0 | 63 passed (25.51 s) — F042/F043 regressions |
| 7 | `python -X utf8 tools/mordheim-utils.py verify --structural --json` (`verify-structural.json`) | 0 | `structural_complete: true`, 0 structural errors, 1050 profiles |
| 8 | `verify --json` before / after (`verify-before.json`, `verify-after.json`, `verify-comparison.json`) | 1 / 1 | identical: 718 obligations, 565 verified, 153 pending, 30 errors, 1050 profiles; retained 30, removed 0, added 0 |
| 9 | `pytest tests/python/architecture/test_documentation.py -q` (`pytest-documentation.txt`, after the last document edit) | 0 | local Markdown links resolve |
| 10 | `git diff --check -- <owned files>` (`git-diff-check.txt`) | 0 | no whitespace errors |
| — | `tools/knowledge/audit_schema_strictness.py [--json]` (`audit-strictness.*`) | 0 / 0 | 40 findings, 0 hard, 40 justified, 0 unjustified, 0 stale |

The 30 `verify` errors are the historical pre-snapshot pins registered as F001;
this lot refreshed no pin and hid no inherited failure. `git status` lists
exactly the four modified owned files plus the new ones (section 10).

## 8. Isolation proof (F049)

No test or probe in this lot writes a live or protected file. The negative
probes clone the merged schema **in memory** (monkeypatched `schema_for`, clone
only for `equipment-access.yaml.schema.json`) and the staleness probe audits a
synthetic package under `tmp_path`; no temporary write into `sources/knowledge`
or `contracts/` was performed, and no restore operation exists to hide one.

`hash-snapshot.py` recorded the dispatch's `protected_hashes` plus the complete
`knowledge_yaml_hashes` inventory (701 canonical YAML + 4 non-overlapping
protected files = **705 files**) immediately before the test battery and again
at closing: **0 mismatches** against the dispatch digests and **no change**
between the two snapshots (`isolation-before.json`, `isolation-after.json`,
`isolation-after.txt`). The four dispatch backups were hashed at closing too and
still match the entry values; the dispatch directory was never written to.

## 9. Limits, deferred findings and proposals for the register

Limits of this lot:

- **F044's disposition is contract-level.** The list-level note and the
  recipient block have no exercised canonical document yet; the delivery proves
  the projection consumes them (fixtures) and that the audit cannot be widened
  by them, not that a visible product screen loads either today. The generator
  publication path is inspected, not re-run (the artefact is current:
  `generate_knowledge_web.py --check` → EXIT 0, `artefact-check.txt`).
- **Python type checking of the package is not part of this checklist**; the
  module is exercised by its tests and imports cleanly (no dedicated mypy
  target exists in the repository).
- The new TypeScript suite lives in `tests/typescript/**`, outside every
  `tsconfig`; Vitest compiles it (esbuild, types erased), so item 5's typecheck
  cannot see it. This is the pre-existing test-tree gap recorded in T10.
- Member-scoped justifications fix the *forward* risk at the two F044 paths.
  For a shared `defs.schema.json` definition the pooled *detail text* still
  keeps the first schema's member list while the structured members are the
  union; no member mapping exists on a shared definition today, so this
  imprecision is inert and is recorded rather than reworked.

Proposals for the coordinator (not edits to the shared register):

1. **F044 revalidation/disposition (as retitled by this lot).** *Problem:* the
   strict audit reported two equipment-access declarations unused by the
   committed documents. *Reproducer:*
   `python -X utf8 -m pytest tests/python/knowledge/test_editorial_schemas.py -q`
   at entry (`baseline.txt`: 1 failed, 1 passed, 303 deselected; the
   catalogue-contracts lot's full-file run before this one: 1 failed,
   304 passed) and the isolated probes of
   `test_equipment_access_schema_contract.py`. *Impact:* editorial strictness
   only; no runtime effect. *Dependency:* schema/editorial owner; the consumer
   evidence in section 2. *Moment:* before the next equipment-access schema
   acceptance. *Close when:* an independent reviewer confirms the disposition,
   the member scope and the negative controls, and the gates are green.
   Follow-ups inside the disposition: when a canonical list first carries
   `notes`/`notes_i18n`, or a document prints another recipient kind, the
   stale gate will name the entry and the justification must be narrowed —
   automatic, no silent widening.
2. **F050 (new, proposed): the F042 racial-maximum reference reaches the
   reference sheet unresolved.** *Problem:* the accepted F042 KB edit added
   `(campaign.limit.racial-maximum.human)` to the Sisters
   `band--human-maximum-characteristics` effect (EN/ES), but no maintained
   consumer substitutes that token, so the reference sheet renders it raw and
   `warband-reference.test.ts` fails two cases (`not.toContain("campaign.limit.")`,
   both locales). *Reproducer:*
   `cd packages/typescript && npx vitest run ../../tests/typescript/application/rules/warband-reference.test.ts`
   (`vitest-warband-reference.txt`; the same input text is in
   `outputs/web-public/knowledge/rules-prose.json`, whose `--check` is EXIT 0,
   so the artefact is not stale). *Impact:* the TS reference-sheet gate is red
   in the current tree; the raw catalogue id leaks to players. *Attribution:*
   the failing rule's text comes from the F042 working-tree edit of
   `sources/knowledge/bands/mordheim/sisters-of-sigmar/special-rules.yaml`;
   none of this lot's files is an input to that suite. *Dependency:*
   schema/editorial owner or reference-projection owner; a decision is needed
   between resolving `campaign.limit.*` citations in the projection and
   publishing resolved prose. *Moment:* at the next F042 revalidation or
   before any accepted TS run. *Close when:* both locales render the resolved
   reference and the protected suite passes.
3. **Optional architectural note (no owner assigned).** The recipient
   vocabulary is declared twice (`profiles.yaml` and `equipment-access.yaml`).
   Declaring it once in `defs.schema.json` would let the audit pool the
   evidence and remove the duplicate; it touches protected contract files, so
   it stays a proposal, not a change of this lot.

## 10. Files, closing hashes and next action

Written by this lot (owned): the four files of the table in section 1 plus the
two new test modules and this document. `git status --porcelain` for them
(`closing-status.txt`):

```
 M contracts/knowledge-editorial-v1/README.md
 M contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json
 M packages/python/knowledge/mordheim_knowledge/editorial_schema_audit.py
 M tests/python/knowledge/test_editorial_schemas.py
?? tests/python/knowledge/test_equipment_access_schema_contract.py
?? tests/typescript/application/rules/equipment-access-contract.test.ts
```

Evidence: `build/cache/t13-parallel/equipment-access-schema/**` (ignored):
`verify-before/after.json` + `verify-comparison.json`, `verify-structural.json`,
`artefact-check.txt`, `gate-strictness.txt`, `pytest-*.txt`, `vitest-*.txt`,
`typecheck-campaign-web-core.txt`, `audit-strictness.*`, `isolation-before.json`,
`isolation-after.json` and its comparison output, `hash-snapshot.py`,
`compare-verify.py`, the owned diff/status records and `evidence-index.txt`.
The dispatch directory remains immutable and unread by any script except
`entry.json`/`hash-snapshot.py`.

Next action for the coordinator: review the two owned diffs plus the two new
test modules against this document, confirm the member-level dispositions and
the isolation proof, then route the F044 disposition and the proposed F050.
F044 and T13 remain open; nothing was accepted, committed or pushed by this lot.

## 11. Independent coordinator acceptance — 2026-10-02

**Accepted at the equipment-access contract boundary; reservation released.**
F044 is resolved for its two local declaration paths. T13 and product presentation
remain open. Retaining the notes and all four recipient kinds is justified by
the maintained publication/projection contract; no canonical document is invented.

Independent review evidence is retained in
`build/cache/t13-parallel/equipment-access-schema-coordinator-review/review.py`
and `independent-review.json`. The coordinator verified:

- All four immutable dispatch backups match their recorded entry hashes; all
  705 protected/KB files are unchanged. The delivered production hashes match
  the executor's closing hashes, and HEAD remains `1b7f7cf`.
- Removing only schema descriptions gives exactly the original validation
  structure. Every pre-existing text justification retains its original value;
  the only two additions are the reviewed member mappings.
- Fresh Python run: **316 passed** (editorial schemas plus the new contract
  suite). Fresh maintained audit: **40 findings, 0 hard, 0 unjustified, 0 stale**.
  Fresh TypeScript run: new contract suite **2 passed**; existing reference suite
  **6 passed / 2 failed**, both localized raw-reference cases assigned to F050.
- The synthetic TypeScript fixture proves notes in both locales and positive
  hero/animal/henchman recipients; summoned has a negative control, with its
  canonical vocabulary and generic type-filter route inspected separately.
  This acceptance does not claim a visible summoned-list workflow witness.

Two deferred findings are now in the [execution follow-up register](T13-execution-follow-ups.md):

1. **F050:** F042's Human reference reaches the reference projection as a raw
   identifier in EN/ES. Its accepted catalogue repair did not prove product
   presentation. Resolve through the maintained reference/localization route
   before accepting the affected T15 reference flow; preserve the canonical link
   and the meaningful regression assertions.
2. **F051:** shared-definition aggregation has a semantic defect beyond the
   detail-text discrepancy described in section 9. In an isolated two-schema
   probe, one document uses `a` and the other `b`; both members are globally used,
   yet the audit reports an unused-property finding with members `a,b`. The same
   erroneous finding identity/detail is reproduced from the immutable original
   auditor, so this is inherited. There is no current member mapping on a shared
   definition. Repair pooled evidence before introducing one or certifying that
   aggregation in T14; this does not reopen the two local F044 mappings.

The optional shared-enum extraction is not assigned as additional work: the
existing equality regression guards the vocabulary without a contract refactor.
The retained executor verification/typecheck logs supply the broader unchanged
baseline; this coordinator review does not claim a fresh full verification run.
No production repair, commit, push or agent launch was performed by the reviewer.
Coordination records now resolve F044, release the README reservation and assign
F050/F051 without an executor or completion date. The final local-documentation
gate passes (one test); coordination-file whitespace checks are clean.

Subsequent state, 2026-10-02: [F051 was independently accepted](T13-shared-schema-evidence.md#12-independent-coordinator-acceptance--2026-10-02).
The 40 findings above are the historical F044 acceptance result. The current
auditor reports 39 after removing the globally exercised `rule_runtime.grant`
false finding and its obsolete justification; the other 39 findings and both
local F044 mappings are unchanged. F050 presentation remains a separate lot.
