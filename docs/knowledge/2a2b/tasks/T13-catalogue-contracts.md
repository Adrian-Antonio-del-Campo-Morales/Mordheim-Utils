# T13 — R0/F042–F043 catalogue contract repair

Execution delivery for the lot reserved as **R0 / F042–F043 — catalogue contract
repair** in the [initiative checklist](../README.md), and for the two registered
findings it targets:
[T13-F042](T13-execution-follow-ups.md#t13-f042--sisters-of-sigmar-lacked-the-human-racial-maximum-reference)
(the Sisters of Sigmar rule `band--human-maximum-characteristics` mentions the
Human racial maximum profile without linking its canonical entry) and
[T13-F043](T13-execution-follow-ups.md#t13-f043--hired-sword-eligibility-grammar-test-rejects-localized-notes)
(the hired-sword eligibility grammar test refused the `note_i18n` field that the
maintained editorial contract already admits).

Both findings were **contract/check mismatches, not product defects**. F042 is a
missing catalogue reference repaired in the canonical band document; F043 is a
test that kept its own allowed-key list instead of reading the maintained
contract. The executor **does not accept or close anything**: F042, F043 and T13
keep their status, no shared document (README, plans, follow-up register) was
edited, and no commit or push was made.

## 1. Entry state, dispatch and hashes

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, unchanged at
  closing. The shared tree carried 232 dirty entries of other lots at closing
  (229 at entry); none of them was touched by this lot.
- The coordinator dispatch
  (`build/cache/t13-parallel/catalogue-contracts-dispatch/entry.json`,
  coordinator-owned, read-only here) reserves two owned and four protected
  inputs. The baseline it records failed exactly two tests
  (`2 failed, 41 deselected`, EXIT=1; log retained at
  `catalogue-contracts-dispatch/baseline.txt`).

| Reserved input | Entry SHA-256 (dispatch) | Closing SHA-256 | Outcome |
| --- | --- | --- | --- |
| `tests/python/knowledge/test_campaign_catalogs.py` | `ab29e869b24f08d6109b7ae32eae7e5d359496a72fb1b1e7291162e920c219e6` (47 988 bytes, CRLF) | `2fddb25b19fed5470a0741ce96d9a8001f401941ca6337e68b142904cce11cda` (51 091 bytes) | changed (+105/−31 lines) |
| `sources/knowledge/bands/mordheim/sisters-of-sigmar/special-rules.yaml` | `b778f00a372131e43770adad13848f00342727720d13178b21847cd91505d63b` (10 624 bytes, LF) | `b46094609ee27d5cb067d4d18085c0595cc21e9d3b80e2f265dd594bf292d3dc` (10 710 bytes) | changed (+4/−2 lines) |
| `contracts/knowledge-editorial-v1/campaign-hired-swords-and-dramatis.yaml.schema.json` | `33723ba20555ed26df62399f183c19b91b7140839c05fe8f28ff9a71ab426bea` | same | untouched |
| `contracts/knowledge-editorial-v1/defs.schema.json` | `26cf39815f6a221a92e57521fb0bc42f4a0c40ecba9ab0d084b60502298ed7f8` | same | untouched |
| `sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml` | `ee984be6e65a37e04bf758e5fb63c760c4cfe6f3e7e406471b2daa43e1a5e8c1` | same | untouched |
| `sources/knowledge/catalog/rules/racial-maximums.yaml` | `d734a7f2ac28cbba3f19b28ce40d62a93904e7ba9af74902873cfde71bcff1e1` | same | untouched |

The two owned inputs were copied byte-for-byte into
`build/cache/t13-parallel/catalogue-contracts/backup/` before any edit. A later
re-run of the entry script overwrote that copy; it has been **restored from the
recorded revision with a byte-exact proof** (`backup-restore-proof.json`), and
the entry script is now guarded. Section 8 documents the incident, the recovery
and the raw records preserved. The restored backup bytes equal the dispatch
hashes above.

Baseline red (before any edit, using the entry backups):

```text
python -X utf8 -m pytest tests/python/knowledge/test_campaign_catalogs.py -q \
  -k "band_rules_reference_racial_maximums or hired_swords_eligibility_resolves"
→ 2 failed, 41 deselected  EXIT=1
  FAILED …::test_band_rules_reference_racial_maximums_without_inlining_statlines
         band--human-maximum-characteristics mentions a max profile without ref
  FAILED …::test_hired_swords_eligibility_resolves_and_grammar_is_valid
         campaign.hireling.hired-sword.albino-stormvermin carries note_i18n
```

## 2. Sources and contracts consulted

Documentation: [initiative checklist](../README.md) (reservation row),
[T13-T15 remaining plan](T13-T15-remaining-plan.md),
[execution follow-up register](T13-execution-follow-ups.md) (F042, F043, F001;
F044–F047 read to separate inherited failures),
[T13-profile-save-thresholds](T13-profile-save-thresholds.md) (§6.4, §8, §10),
[verification](../../../reference/verification.md),
[eligibility](../../../reference/eligibility.md) and
[implement and verify rules](../../../guides/implement-and-verify-rules.md).

Contracts and data: the reserved
[hired-swords schema](../../../../contracts/knowledge-editorial-v1/campaign-hired-swords-and-dramatis.yaml.schema.json)
(`$defs.eligibility`),
[defs schema](../../../../contracts/knowledge-editorial-v1/defs.schema.json)
(`$defs.i18n`),
[special-rules schema](../../../../contracts/knowledge-editorial-v1/special-rules.yaml.schema.json),
the committed
[hired-swords catalogue](../../../../sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml),
the
[racial-maximum catalogue](../../../../sources/knowledge/catalog/rules/racial-maximums.yaml),
the
[Sisters of Sigmar rules](../../../../sources/knowledge/bands/mordheim/sisters-of-sigmar/special-rules.yaml)
and `registry/warband-groups.yaml`.

Code and tests: `packages/python/knowledge/mordheim_knowledge/editorial_schemas.py`
(`schema_for`, `validate_document`), `campaign.py`
(`_validate_hired_swords_document`), `hireling_promotion.py`, the TypeScript
eligibility consumers (`domain/campaign/construction.ts`,
`application/campaign/features/hirelings/hirelings-workflow.ts`,
`features/searches/search-workflow.ts`), the maintained web generator
(`tools/knowledge/generate_knowledge_web.py`,
`tools/knowledge/presentation_contract.py`),
`tests/python/knowledge/test_campaign_catalogs.py`,
`tests/python/knowledge/test_editorial_schemas.py` and
`tests/python/knowledge/test_staging_promotion.py`.

### 2.1 Correction of the historical attribution

The earlier delivery (R2/R3, §8 proposal 1) named four band documents
(`amazons-mordheim`, `sisters-of-sigmar`, `tileans`, `witch-hunters`). The
coordinator dispatch scan and this lot's scan of **all** committed bands find
**one** missing reference, `mordheim/sisters-of-sigmar` /
`band--human-maximum-characteristics`. The other three rows already link their
maximum profile at HEAD
(`amazons-mordheim/special-rules.yaml:193`, `tileans/special-rules.yaml:59`,
`witch-hunters/special-rules.yaml:163`), so they were **not** edited. The
historical prose is superseded by the current evidence.

## 3. F042 — the missing racial-maximum reference

### 3.1 What the maintained check requires

`test_band_rules_reference_racial_maximums_without_inlining_statlines` walks
every `bands/**/special-rules.yaml`: an English `effect` that mentions a maximum
*profile* must carry at least one `campaign.limit.racial-maximum.*` reference,
every reference must resolve in `catalog/rules/racial-maximums.yaml`, and a rule
about *characteristic* maximums must not inline a numeric statline. A roster
rule that mentions the maximum *warband size* stays outside the contract.

The lot's scan of the entry state (`scan-maximum-refs.py`) found 79 rules with a
maximum mention, 20 mentioning a maximum profile, **one missing reference**
(Sisters of Sigmar), zero unknown references and zero inlined statlines
(`scan-before.txt`, EXIT=1). The check is advisory catalogue metadata: the rule
is `scope: 'NO'`, `implemented: 'NO'`, `grant: band`, `binding: null` and
`applies_to.band: true`; no combat value, recipient or activation changed.

### 3.2 The canonical reference

`catalog/rules/racial-maximums.yaml` declares
`campaign.limit.racial-maximum.human` (the Human profile, groups
`[warband-group.human]`), and `registry/warband-groups.yaml` lists
`warband-group.human` with `sisters-of-sigmar` among its bands. That entry — not
the faction group `warband-group.sigmar-devoted` — is the reference the clan
rule needs, and the form used by the already-resolved bands is the trailing
parenthetical citation. The Sisters clause keeps its printed meaning: they are
Humans and use the Human racial maximum; the reference is added, the table is
not duplicated.

### 3.3 The change

```diff
-    Sisters of Sigmar are Humans and use the Human racial maximum profile.
+    Sisters of Sigmar are Humans and use the Human racial maximum profile
+    (campaign.limit.racial-maximum.human).
…
-      Las Hermanas de Sigmar son Humanas y usan el perfil máximo racial humano.
+      Las Hermanas de Sigmar son Humanas y usan el perfil máximo racial humano
+      (campaign.limit.racial-maximum.human).
```

Only those two lines changed (`+4/−2`); the `source`, `name_i18n`,
`effect_i18n` keys, `applies_to`, `runtime` block and every other rule of the
81-file corpus are untouched. English and Spanish keep the same reference, so
the translation-consistency suite stays green.

There is **no same-path mirror under `sources/2B`** for this band — the dispatch
records `canonical_sisters_has_no_same_path_2B_mirror: true` and this was
verified — so no staged or artificial mirror was created. The staging-promotion
suite remains green without any staged edit (section 6).

After the edit the same scan reports 79 / 20 / 0 / 0 / 0 and EXIT=0
(`scan-after.txt`). The maintained test passes (section 6), and the web
artefacts publish the new text in both languages (section 7).

### 3.4 Why this respects the contract

- The reference is the canonical catalogue id, resolved against the shared
  catalogue, not a copy of the statline.
- No maximum value, recipient, scope, implementation flag or binding changed;
  the rule stays out of combat as before.
- The citation form matches the convention already used by the bands that pass
  the same check.
- The English `effect` stays the canonical prose and the Spanish `effect_i18n`
  mirrors it.

## 4. F043 — eligibility grammar vs the editorial contract

### 4.1 The discrepancy

The entry test asserted a hardcoded allowed-key set
`{allow_groups, forbid_groups, allow_band_ids, forbid_band_ids, expression,
note}` and rejected the committed row
`campaign.hireling.hired-sword.albino-stormvermin`, whose `eligibility` also
carries `note_i18n`. The maintained contract declares it:
`campaign-hired-swords-and-dramatis.yaml.schema.json#/$defs.eligibility.properties`
has exactly `allow_band_ids`, `allow_groups`, `forbid_band_ids`, `forbid_groups`,
`expression`, `note`, `note_i18n`, with `note_i18n` pointing at
`defs.schema.json#/$defs/i18n` (required `es`, `additionalProperties: false`, an
`en` mirror forbidden). The test — not the data — was behind the contract.

### 4.2 The change (test file only, no data or schema edit)

`tests/python/knowledge/test_campaign_catalogs.py` now reads the contract
instead of copying it:

- import `from mordheim_knowledge import editorial_schemas` (line 22);
- a helper block (lines 391–462) with `HIRED_SWORDS_SCHEMA`,
  `RACIAL_MAXIMUM_REFERENCE`, `MAXIMUM_PROFILE_MENTION`, `INLINED_STATLINE`,
  `racial_maximum_ids()`, `racial_maximum_reference_problems()`,
  `canonical_band_ids()`, `warband_group_ids()`, `eligibility_keys()` — from
  `editorial_schemas.schema_for(HIRED_SWORDS_SCHEMA)["$defs"]["eligibility"]["properties"]` —
  `eligibility_reference_problems()` and `campaign_schema_problems()`;
- `test_band_rules_reference_racial_maximums_without_inlining_statlines` (line 465)
  keeps its scan but collects `problems` from the shared helper, so one rule can
  report several defects instead of stopping at the first;
- `test_hired_swords_eligibility_resolves_and_grammar_is_valid` (line 872)
  validates the committed document with the maintained
  `editorial_schemas.validate_document`, checks every block with the shared
  reference helper and keeps `check_expression` for `expression` nodes.

No new validator, no second copy of the contract, no relaxation: unknown keys,
unknown bands/groups, malformed localized blocks and expression grammar are
still refused (section 5). The assistants `check_expression`, its callers and
the rest of the file are otherwise untouched.

### 4.3 Loader and publication trace — contract, not visible behaviour

- `mordheim_knowledge/campaign.py::_validate_hired_swords_document` (line 370)
  validates entry `profile_id`s, availability procedure ids and cost resources.
  It never reads `eligibility`, let alone `note_i18n`, so the field was never a
  loader failure.
- The TypeScript consumers read `allow_groups`, `forbid_groups`,
  `allow_band_ids`, `forbid_band_ids`, `expression` and — for the rejection
  reason text — `note` (`construction.ts:1125–1135, 1333`;
  `hirelings-workflow.ts:119–136`; `search-workflow.ts`). None reads
  `note_i18n`.
- The promotion writer emits `allow_*`/`forbid_*` and `note` only
  (`hireling_promotion.py:347–374`); the committed `note_i18n` rows come from
  the staged tree through the maintained promotion, which the staging suite
  keeps green.

So F043 is a **contract-level repair**: the accepted keys and the shape of the
localized block are now enforced from the maintained schema, but no runtime
reader consumes `eligibility.note_i18n` today. What *is* proven is that the
localized note survives its maintained publication route: the fresh generator
publishes it in the deferred catalogue as
`campaign/hired-swords-and-dramatis/hired_swords/72/eligibility/note_i18n/es`
and in the presentation artefact as
`presentation_entries/10494/fields/note/{en,es}` (ref
`campaign/hired-swords-and-dramatis/hired_swords/[id=campaign.hireling.hired-sword.albino-stormvermin]/eligibility`),
with 26 eligibility blocks carrying localized notes in
`knowledge-catalogue.json`. `tools/knowledge/presentation_contract.py` lists
`note` among its fields and reads `note_i18n`, which is the maintained
mechanism that produced those entries.

## 5. Regression ledger and mutation evidence

`tests/python/knowledge/test_catalogue_contract_regressions.py` (new, 20 tests)
exercises the maintained helpers and contract — it restates no contract copy:

- **F042 positive:** the Sisters rule resolves; the linked entry is the one the
  band's registry groups declare; every committed band rule resolves its
  references (≥ 20 rules).
- **F042 negative:** a missing reference is still reported; an unknown
  `campaign.limit.racial-maximum.*` is reported; an inlined statline is
  reported; a maximum *warband size* mention is not treated as a racial maximum.
- **F043 positive:** the key set comes from the contract and rejects
  `note_en`/`notes`/`include`/`when`; the committed catalogue validates; Albino
  Stormvermin keeps its English `note` and Spanish `note_i18n` and resolves its
  groups; a valid localized block and an absent block are both accepted.
- **F043 negative:** an unknown eligibility key is rejected by helper *and*
  schema; five malformed `note_i18n` shapes (undeclared locale `fr`, empty
  `es`, `en` mirror, string, empty mapping) are refused by the maintained
  validator; invalid band/group references are refused; `expression` grammar is
  still enforced (valid combinators accepted, broken nodes raise); `expression`
  next to `allow_band_ids` is refused as the schema declares.

Mutation ledger (`mutations.py`, backups in `mutation-stash/`, `restored: True`,
EXIT=0): M1 relax the missing-reference branch → detected by the ledger; M2
restore the stale key set → detected by maintained test and ledger; M3 drop the
Sisters reference again → detected; M4 drop the localized Albino note →
detected; M5 inject an undeclared locale → detected. Five of five mutations were
killed, so the repaired checks still refuse invalid data.

## 6. Verification runs

| Command | Exit | Result |
| --- | --- | --- |
| baseline `-k "band_rules_reference_racial_maximums or hired_swords_eligibility_resolves"` (before edits) | 1 | 2 failed, 41 deselected (dispatch baseline) |
| `scan-maximum-refs.py` before / after | 1 / 0 | 79 rules, 20 mentions, 1 → 0 missing, 0 unknown, 0 inlined |
| focused after (`focused-after.txt`, re-run `closing-focused.txt`) | 0 | 2 passed, 41 deselected (4.14 s) |
| `pytest tests/python/knowledge/test_catalogue_contract_regressions.py -q` (`regressions.txt`, `closing-regressions.txt`) | 0 | 20 passed (7.26 s) |
| `pytest tests/python/knowledge/test_campaign_catalogs.py -q` (`pytest-campaign-catalogs.txt`, `closing-campaign-catalogs.txt`) | 0 | 43 passed (18.78 s) |
| `pytest tests/python/knowledge/test_source_documents.py -q` (`closing-source-documents.txt`) | 0 | 15 passed |
| `pytest tests/python/knowledge/test_editorial_schemas.py -q` (`pytest-editorial-schemas.txt`) | 1 | 1 failed, 304 passed — **inherited F044** (line 368; neither owned file involved) |
| `pytest … test_staging_promotion.py test_2b_staging.py test_2ab_fidelity_rows.py -q` (`pytest-staging.txt`) | 0 | 47 passed, 3 skipped |
| `pytest tests/python/web -q` (`pytest-web.txt`) | 1 | 2 failed, 157 passed — **inherited F045/F046** |
| translation consistency/parity/2B/KB-i18n/campaign loaders (`pytest-translations.txt`) | 0 | 32 passed |
| remaining knowledge suites (`pytest-knowledge-rest.txt`) | 0 | 146 passed, 7 skipped |
| `mutations.py` (`mutations.json/.txt`) | 0 | 5/5 DETECTED, restored |
| `verify --json` before / after (`verify-before/after.json`) | 1 / 1 | byte-identical (sha256 `8f3e6481…`, 1 454 674 bytes) |
| `compare-verify.py` (`verify-comparison.txt`) | 0 | 30 → 30 errors (retained 30, removed 0, added 0); 718 obligations; 565 verified; 153 pending; 1050 profiles |
| `verify --structural --json` (`verify-structural.json`) | 0 | `structural_complete: true`, 1050 profiles |
| generator `--check` before / after regeneration | 0 / 0 | artefact current before; regenerated then current (twice) |
| `pytest tests/python/architecture/test_documentation.py -q` (after this document) | 0 | local Markdown links resolve |
| `git diff --check -- <two owned files>` (`git-diff-check.txt`) | 0 | no whitespace errors |

The 30 `verify` errors are the historical pre-snapshot pins registered as F001;
this lot neither refreshed pins nor hid them, and the before/after identity
comparison is exact. The two inherited catalogue failures named by the dispatch
are now green.

## 7. Generated artefacts

The F042 prose edit made the generated web artefact stale, so it was regenerated
with the maintained generator (`tools/knowledge/generate_knowledge_web.py`,
`generate-after.txt`: 2843 KB initial, 2746 KB deferred catalogue, 161 bands,
1056 profiles, 449 deferred items, 82 skills) and `--check` returned to EXIT=0.
The delta is fully attributable (`artefact-delta-applied.txt`):

- `rules-prose.json`: 3 changed leaves — the Sisters `effect`/`effects.en` and
  `effects.es` now carry the reference;
- `display-text.json`: 3 changed leaves — the same two strings under
  `presentation_entries/[7674]/fields/effect/{en,es}` plus the presentation
  digest;
- `knowledge-web.json`: 3 changed digests (rules prose, display text,
  presentation);
- `knowledge-catalogue.json`: 0 changed leaves.

After regeneration a fresh comparison is 0 changed leaves in all four artefacts
(`artefact-delta-post.txt`), i.e. fresh == regenerated, and no output was
hand-edited.

## 8. Evidence integrity note — backup incident and recovery

This lot must disclose one incident inside its own evidence folder:

1. The entry script `entry-check.py` (original form) copied the two owned
   working-tree files into `backup/` on every run. Re-running it **after** the
   repairs overwrote the pristine entry copies with the edited files and
   likewise overwrote `entry-state.json/.txt`. The canonical sources, tests and
   contracts were never affected; only the evidence copy was lost at that
   moment.
2. The entry bytes are reconstructible from the recorded revision: the band
   YAML equals its `HEAD` blob byte-for-byte, and the test file equals its
   `HEAD` blob with the file's CRLF working-tree line endings (git stores LF).
   `restore-backups.py` rebuilt both, matched them against the dispatch hashes
   (`ab29e869…`, `b778f00a…`) and restored `backup/`;
   `backup-restore-proof.json/.txt` records the reconstruction and the match.
   `entry-check.py` is now guarded: it copies only when no backup exists, keeps
   an existing backup whose hash equals the dispatch, refuses to overwrite one
   that does not, and writes `entry-state.post-entry.*` instead of the canonical
   entry names when the live tree no longer matches the dispatch.
3. The raw records are preserved, not deleted: `entry-check-rerun-post-edit.*`
   (the accidental post-edit run), `entry-state.post-entry.*` (the guarded
   re-run, EXIT=1 because the owned files are edited, backups preserved) and the
   truthful `entry-state.json/.txt` written by `restore-entry-state.py`, which
   labels itself a **restored record** and re-verifies the restored backups and
   the four protected inputs against the dispatch (EXIT=0, `failures: 0`).

The coordinator can therefore still attribute every byte: the entry hashes live
in the coordinator-owned dispatch, the restored backups now hash to exactly
those values, and the incident plus the proof are recorded rather than papered
over.

## 9. Limits, deferred findings and proposals for the register

Limits of this lot:

- **F043 is contract-level.** No loader or campaign consumer reads
  `eligibility.note_i18n`; the repaired check validates the data against the
  maintained schema and the published artefacts keep the localized note, but no
  visible behaviour is demonstrated or changed.
- **F042 is catalogue metadata.** The rule is `scope: 'NO'`; adding the
  reference does not activate anything and no compiled value changed.
- No engine, shared eligibility, specification, fingerprint or pin was touched;
  no `sources/2B` document was written (no mirror exists for this band); no
  README, plan or register was edited; nothing was committed, pushed or
  delegated. The full-tree semantic verify still exits 1 on the 30 F001 pins,
  and the inherited failures below are unrelated to this lot (they reproduce
  with the entry backups).

Proposals for the coordinator to register (F044–F046 exist in the register with
the R2/R3 wording; these are this lot's revalidated and, where noted, corrected
fields; F047 is untouched by this lot):

1. **F044 — equipment-access strict audit (revalidated, F044 as registered).**
   *Problem:* the strict audit reports the equipment-list properties
   `notes`/`notes_i18n` and the `profile_types` enum values `str:animal`,
   `str:henchman`, `str:summoned` as unused by the committed documents.
   *Reproducer:* `python -X utf8 -m pytest tests/python/knowledge/test_editorial_schemas.py -q`
   (1 failed, 304 passed, EXIT=1, assertion at line 368;
   `pytest-editorial-schemas.txt`). *Impact:* editorial strictness gate only; no
   runtime effect and neither file of this lot is involved. *Dependency:*
   schema/editorial owner; the declaration and the documents (or a justified
   exception) must agree. *Moment:* before the next equipment-access schema
   acceptance. *Close when:* every reproduced declaration has a reviewed
   disposition and the strict audit passes without unexplained findings.
2. **F045 — generated KB count pins (revalidated, F045 as registered).**
   *Problem:* `test_size_metrics_are_stable_and_reported` pins
   `items=388`, `campaign_sections=16`; the fresh generation gives
   `items=449`, `campaign_sections=17` while bands 161, profiles 1056 and skills
   82 match. *Reproducer:*
   `python -X utf8 -m pytest tests/python/web/test_kb_artefact_performance.py -q`
   (`pytest-web.txt`; identical with entry backups restored per the R2/R3 lot).
   *Impact:* the performance guard misreports drift and can hide real
   regressions. *Dependency:* generated-web/performance owner; pins must be
   refreshed from a recorded revision, never from a dirty tree. *Moment:* at the
   next web-artefact acceptance (T15). *Close when:* the inventory delta is
   explained, generator/check are current and the maintained performance gate
   passes with real margins.
3. **F046 — parity manifest row (revalidated, F046 as registered).**
   *Problem:* `tests/python/web/parity/python_manifest_test.py` names
   `tests/web/features/campaign/test_equipment_tab.test.tsx`, which does not
   exist in the tree. *Reproducer:*
   `python -X utf8 -m pytest tests/python/web/parity/python_manifest_test.py -q`
   (`pytest-web.txt`). *Impact:* parity manifest cannot be validated end-to-end.
   *Dependency:* desktop/web parity owner and the missing interaction evidence;
   add the test or drop the row with a reviewed reason, never an empty file.
   *Moment:* with the next equipment-interaction or manifest refresh. *Close
   when:* every manifest row resolves to meaningful maintained evidence and the
   parity test passes.
4. **F047 (not a defect of this lot):** the Boglar fire-magic clause still
   lacks a canonical spell-execution witness; it remains routed to T13.5, and
   this lot neither touched it nor the accepted save correction.

No new catalogue defects were found by the full-band scan or by the contract
validator beyond the classes above.

## 10. Files, closing hashes and next action

Written/created by this lot (owned):

| File | Entry | Closing |
| --- | --- | --- |
| `tests/python/knowledge/test_campaign_catalogs.py` | `ab29e869…` | `2fddb25b19fed5470a0741ce96d9a8001f401941ca6337e68b142904cce11cda` |
| `sources/knowledge/bands/mordheim/sisters-of-sigmar/special-rules.yaml` | `b778f00a…` | `b46094609ee27d5cb067d4d18085c0595cc21e9d3b80e2f265dd594bf292d3dc` |
| `tests/python/knowledge/test_catalogue_contract_regressions.py` (new) | — | `cde9f9a79807a770d0ae43d777282c68672669992e083d3ec504aa5b864f1a98` (11 810 bytes) |
| `docs/knowledge/2a2b/tasks/T13-catalogue-contracts.md` (new) | — | recorded in `evidence-index.txt` |

Protected inputs at closing: the four dispatch hashes reported in section 1 are
unchanged. `git status --porcelain` lists exactly these two tracked M entries
for this lot (`closing-status.txt`); every other dirty entry belongs to another
lot.

Evidence: `build/cache/t13-parallel/catalogue-contracts/**` (ignored): the
dispatch reproduction (`baseline-red.txt`), the scan scripts and results
(`scan-*.json/.txt`), the restore scripts and proofs
(`restore-backups.py`, `backup-restore-proof.*`, `restore-entry-state.py`,
`entry-check-rerun-post-edit.*`, `entry-state.post-entry.*`,
`entry-state.json/.txt`), the owned diff (`owned-diff-vs-head.txt`), the
mutation ledger (`mutations.py/.json/.txt`, `mutation-stash/`), the verification
inputs (`verify-before/after.json`, `verify-comparison.*`,
`verify-structural.*`), the editorial checks (`editorial-before/after.txt`), the
generator runs and artefact deltas (`generate-*.txt`, `artefact-*.txt`,
`artefact-after/`, `artefact-delta.py`), the test logs (`pytest-*.txt`,
`closing-*.txt`), the whitespace check (`git-diff-check.txt`), the evidence
index (`evidence-index.py`, `evidence-index.txt`) and the closing check
(`closing-check.py`, `closing-check.json/.txt/.exit.txt`).

Next action for the coordinator: verify the two owned diffs against this
document and the restored-backup proof, confirm the attributable artefact delta,
then route F044–F046 and record acceptance. F042, F043 and T13 remain open;
nothing was accepted, committed or pushed by this lot. `docs/knowledge/2a2b/README.md`
is not part of this reservation and was not edited; its reservation row is the
coordinator's to update with the link to this delivery.

## 11. Independent coordinator acceptance — 2026-10-01

**Accepted at the catalogue-contract boundary.** F042 and F043 are resolved;
the reservation is released. This does not close T13/T14 or certify visible
product behavior.

The coordinator independently checked:

- Reconstructed the two entry byte streams directly from the dispatched HEAD
  (LF-to-CRLF for the Python working-tree file) and matched both to the dispatch
  hashes and restored backups. The recovery is byte-exact; reconstructed entry
  records are not represented as original capture files. No restoration is pending.
- Compared parsed source documents: only the English/Spanish Human references
  change; all rule metadata and other rows remain identical. Compared Python
  ASTs: only the two pertinent existing tests change, with the documented helper
  additions; all other existing functions, including `check_expression`, match.
  The four dispatch-protected inputs still hash to their original values.
- Re-ran the full campaign-catalogue module plus the new regression module:
  **63 passed**. Seven additional in-memory malformed translation/expression
  probes are rejected through the maintained schema validator. No live source
  mutation was used by the coordinator. Retained executor mutation/broad-suite
  results are not described as independent reruns.
- Ran a fresh maintained `verify --json`: exactly the same 30 inherited F001
  error identities, 565 verified and 153 pending; structural complete on 1050
  profiles. The retained before/after JSON also matches byte-for-byte.
- Ran the maintained generator `--check`: current. Independently inspected
  the generated Albino Stormvermin catalogue row and its structured display-text
  record locator: both EN/ES notes equal canonical data. This establishes
  publication, not a visible hiring-flow result.

Independent reproducer/evidence:
`build/cache/t13-parallel/catalogue-contracts-coordinator-review/review.py`,
`independent-review.json`, `fresh-verify.json`, `publication-probe.json` and
`coordinator-test-results.json` (summaries of observed tool outputs).

Reporting corrections and scope review:

- The regression module's introductory comment incorrectly said that no
  publication path reads `note_i18n`; the coordinator corrected the comment to
  distinguish publication from loader/campaign consumption. No test behavior changed.
- M4/M5 in the retained mutation script temporarily wrote the dispatch-protected
  live hired-sword catalogue. The exact original hash is restored and independently
  verified, but those temporary writes exceeded the reservation. No persistent
  catalogue edit is accepted or authorized by this review. **F049** requires an
  isolated mutation replay before this method is reused in the shared checkout.
  The historical evidence and script remain retained; the coordinator did not
  rerun that script or any shared-tree restore operation.
- **F048** tracks the unexecuted EN/ES product presentation of eligibility notes;
  absence of a direct `note_i18n` reader is not by itself a demonstrated UI bug.
  F044–F047 and F001 retain their previously recorded gates and dispositions.

The coordinator recorded acceptance in the initiative README and follow-up
register. No commit/push or agent launch was performed.
