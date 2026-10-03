# T13 — R0 context-data source pins

Execution delivery for the lot reserved as **R0 — context-data source pins** in the
[initiative checklist](../README.md). It applies exactly the 125
`snapshot_content_change` transitions of the read-only
[context-data manifest](T13-context-data-manifest.json) to the
`sources[].digest` scalars of the 48 named specification files, and it proves
that nothing else changed.

The research this lot executes was delivered as
[`T13-context-data-review.md`](T13-context-data-review.md) and accepted by the
coordinator in [section 11 of that review](T13-context-data-review.md#11-coordinator-acceptance-and-class-disposition--2026-10-01)
(G1: 117 pairs, G2: 8 pairs eligible for an exact 125-pair pin-only refresh;
G3 translation additions need no separate ruling). This lot adds the pin edit
only. The executor did **not** mark anything accepted or closed; subsequent
coordinator acceptance is recorded in section 9. T13-F001, T13-F035,
T13-F040 and T13-F041 keep their existing status, and no rule, canonical
document, tool, shared register or product code was modified.

## 1. Entry state and hashes

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`; the working
  tree carried 198 modified/untracked entries from other lots at entry and 219
  after the validation runs (other writers continued). None of them was
  touched, and `sources/knowledge` stayed clean against HEAD both at entry and
  at closing (`0` dirty entries).
- The [manifest](T13-context-data-manifest.json) was verified before any use:
  SHA-256 `86aa8194f1d96ca5d616ab2b26ac8fe930322902a49a82748f5d930f101357cd`,
  exactly the dispatched value. 125 entries, 125 unique `finding_key` values,
  125 unique `(spec_file, specification, target)` keys, 48 specification files,
  17 canonical `special-rules.yaml` files, classification
  `snapshot_content_change`, entry HEAD `1b7f7cf…`, historical snapshot
  `eb85e95`. Its `permissions` field still reads
  “Read-only targets; no pin or canonical edits…”; this lot does **not** edit
  the manifest, and derives its authority from the reserved checklist row and
  the accepted section 11 disposition instead.
- All 48 `entry_spec_sha256` values matched the working tree byte-for-byte at
  entry (`0` mismatches). Because the manifest was written after the accepted
  translation-pin lot, that match also demonstrates the 300 accepted pins are
  part of the input, not a casualty of this lot.
- Byte-for-byte backups of all 48 files were captured before the first write
  (`48/48` identical).

Entry hashes of protected inputs (re-read and unchanged at closing, 18/18):

| Input | SHA-256 |
| --- | --- |
| `docs/knowledge/2a2b/README.md` | `4a2db74290a4ee128203ad6bc292ffb4bb9295d46c844b05dac14ac4834678a7` |
| `docs/knowledge/2a2b/tasks/T13-context-data-manifest.json` | `86aa8194f1d96ca5d616ab2b26ac8fe930322902a49a82748f5d930f101357cd` |
| `docs/knowledge/2a2b/tasks/T13-context-data-review.md` | `0a3000a9b37f15f66c4b3c7f110bd9a79b86daa90c5e4f51e4267e55f6363cc6` |
| `docs/knowledge/2a2b/tasks/T13-context-data-review.csv` | `6aad79e7368385723b800452e3cfbc9361446045ca019282559a474b391d87e9` |
| `docs/knowledge/2a2b/tasks/T13-translation-pins.md` | `1ef049a512910a0828caf84c1411fef30f64c2de5b4a416fca96a976b15367c1` |
| `docs/knowledge/2a2b/tasks/T13-translation-pin-manifest.json` | `1698b0019d5d685153e60245ebcacc804d5d2c1a8cc7b6eac6d49dd1bcf17fd2` |
| `docs/knowledge/2a2b/tasks/T13-execution-follow-ups.md` | `c622ab39bff6d093108db7182702416961f132a8fc0d459105a0c34198f81ec5` |
| `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.md` | `847d5232254396ad955e952c168e59e8932ad5e1ff585e431141c8e4af009ac2` |
| `docs/knowledge/2a2b/tasks/T13-source-fingerprint-review.csv` | `72c4eb027910460d3de973a40c6999fbbc215f7de0807fcbf29ee257d8ca9e2e` |
| `tests/specs/README.md` | `26d0e9688cdc28c0bb249170a380194cd814e0e795b587afb64d5809c40b350e` |
| `docs/reference/verification.md` | `c840d0784360d3c9a97980eef0f925b97eaac892d6a757082f30637f37d7979b` |
| `docs/reference/eligibility.md` | `0bafbf699fb4ea205a2758c6fb7e8d9cc2444e9083b773a1b61ed830eba3667d` |
| `apps/.../verification/inventory.py` | `e2460dc45da41d2dc05ec48bbac43538021d9b9c6d1d1bd2714fa9b862b563e7` |
| `apps/.../verification/audit.py` | `98f0e8a3f2c1aee8cec8317d7e8b1e14b990448dbb3ca0ec2eb6a1ea1950b2e8` |
| `tools/verification/refresh_spec_digests.py` | `83fbe8158a1464e0505c5427472933f14b84f304b7ccf8018541bef6a470ff5d` |
| `tests/python/verification/test_semantics.py` | `c74c20bd00ff81d01e1d4f1f05c90af4c150cdebc1f5b117a7ea2966e75905bd` |
| `tests/python/architecture/test_documentation.py` | `f35fc17e264c9583288ba0387427496b91e31242ff742d78ff17eadd7c17ba65` |
| `sources/knowledge` (whole tree) | `12396a9c11e093ef14d7d38a791be53eb39ccaa09a7bfce29aa67d44944fcf4f` |

The two later inputs differ from the hashes the accepted review captured: the
review document now carries the coordinator's section 11
(`068e95e2…` at emission → `0a3000a9…`), and the follow-up register now carries
the F001/F041 routing (`d684a270…` → `c622ab39…`). Both were re-read at entry
and hold the disposition quoted above; no check in this lot depends on their
older bytes.

## 2. Scope and consulted disposition

Authorized writes, and only these:

1. the 125 `sources[].digest` values named by the manifest, replacing
   `expected_digest` with `current_digest`;
2. this new document;
3. evidence and temporary scripts under
   `build/cache/t13-parallel/context-data-pins/**`.

The manifest pairs are all grant obligations (`target` prefix `rule/`), spread
over `tests/specs/semantic/grants/` (42 files) and `tests/specs/semantic/rules/`
(6 files). Effect families: `skill` 57, `trait` 26, `profile` 12, `compiler` 10,
`mechanic` 9, `special-rule` 5, `weapon` 3, `poison` 2, `profile-rule` 1.
Registered follow-ups: T13-F001 (125), T13-F035 (13), T13-F017 (11),
T13-F014 (8), T13-F010 (3), T13-F016 (2). None of them is closed here.

Not touched: the manifest and the review/CSV, the README and every shared
register, `T13-translation-pins.md` and its manifest, other specification
fields, canonical knowledge, code and tools, and all unrelated working-tree
changes. The 300 accepted translation pins and the 30 historical pins are
preserved (section 5); the accepted Bloated Foulness block in
`tests/specs/semantic/grants/editorial-selected-blessings-modifications.yaml`
is untouched (it is not one of the 48 files).

`tools/verification/refresh_spec_digests.py` was **not** executed in write mode;
its `--check` behaviour was not needed either, because the maintained
`verify --json` runs supply the comparison.

## 3. Procedure

Reproducible from the repository root with `python -X utf8`:

1. `entry-check.py` — records branch/HEAD/status, verifies the manifest hash
   and all 48 `entry_spec_sha256` values, hashes the protected inputs, and
   copies the 48 files byte-for-byte into `backup/`.
2. `tools/mordheim-utils.py verify --json` — baseline error set.
3. `revalidate.py` — for each entry: PyYAML `compose` marks locate the single
   `sources[].digest` scalar for `(specification, target)`, prove it is the only
   occurrence of that target in the file, prove its text equals
   `expected_digest`, recompute the maintained fingerprint over the live KB with
   `inventory()` and require `current_digest`, recompute it over the extracted
   `eb85e95` KB and require `expected_digest`, and record which context
   documents differ beyond `*_i18n` keys. No writes.
4. `apply.py --dry-run` — runs the four minimality proofs for all 48 files
   without writing; then `apply.py` performs the same proofs and writes.
5. `post-check.py` — independent re-derivation from the backups, never
   consulting `apply.py`’s report.
6. `compare-identities.py` — before/after `verify --json` comparison by
   identity.
7. The validation commands of section 6, then `closing-check.py` — re-reads
   every protected input and hashes this lot’s artefacts.

The edit itself never reserialises a document and never does a global text
substitution: each file is read as text, the authorized scalar spans come from
`compose` marks, and only the 64-hex content of those spans is replaced (in
descending offset order). Comments, ordering, formatting, line endings, quotes
and all other bytes are preserved; every file is LF-terminated before and after.

## 4. Revalidation result (125/125, 0 blocked)

- Manifest SHA-256 match: yes; 48/48 entry spec hashes match.
- Pairs: `ok: 125`, `blocked: 0`. For every pair the located scalar is unique in
  its file, equals `expected_digest`, the live `inventory()` fingerprint equals
  `current_digest`, and the `eb85e95` fingerprint equals `expected_digest`.
  Live obligations 718, `eb85e95` obligations 718.
- Context change per pair (`context-diff.py`, independent re-derivation from the
  two data revisions): 51 context documents compared
  (17 band directories × `profiles.yaml`, `equipment-access.yaml`,
  `band.yaml`); 34 differ at all; **17 differ beyond `*_i18n`** and every one of
  them is a `profiles.yaml`; the only non-i18n difference is
  `equipment_restrictions` text removal in **19 profile rows** across those 17
  documents: **29 removed entries, 0 added**. This reproduces the accepted
  review’s 34/29/19 figures and confirms that `equipment-access.yaml` changed
  only in i18n and `band.yaml` not at all. For all 125 pairs the changed context
  document is exactly `profiles.yaml`, so the pin transitions carry the accepted
  class and no additional semantic ruling is implied by this lot.

## 5. Changes and preservation proofs

`apply.py` applied 125 pins in 48 files, 125 changed lines, 0 blocked. Four
proofs ran per file before the write, all true for 48/48 files:

1. **relookup** — the changed `(specification, target)` digest keys equal the
   authorized set for that file, and each new value is `current_digest`.
2. **structured diff** — the loaded-YAML leaf diff between before and after
   contains exactly one entry per authorized pair, each at path
   `("specifications", i, "sources", j, "digest")`, each `expected_digest` →
   `current_digest`.
3. **line diff** — identical line counts; the set of differing line numbers
   equals exactly the replaced digest-line positions; every differing line is a
   `digest: <64 hex>` line; the count equals the file’s authorized pair count.
4. **inverse** — restoring `expected_digest` at the same spans reproduces the
   original bytes, and those bytes equal the backup.

`post-check.py` re-derived all of the above from the live files and the backups
(48/48 files pass all eight checks), plus:

- a **fresh** `inventory()` over the live KB reproduces `current_digest` for all
  125 targets (fingerprints still agree with the updated pins);
- all 18 protected inputs and the whole `sources/knowledge` tree hash are
  unchanged;
- repository-wide, `git diff` against HEAD under `tests/specs` contains exactly
  **425** changed digest lines — 300 accepted translation pins + 125 from this
  lot — and the only non-digest changed lines in the whole specification tree
  are the 6 lines of the pre-existing accepted Bloated Foulness block in
  `editorial-selected-blessings-modifications.yaml`.

Per-file record (pin count, before → after SHA-256 prefix; full hashes in
`apply-report.json`):

| Specification file | Pins | Before → after |
| --- | --- | --- |
| grants/editorial-advanced-dwarf-parries.yaml | 5 | `456657eea53b` → `db5bd3e2e04a` |
| grants/editorial-advanced-loadouts.yaml | 3 | `90c69888b820` → `77112f8fd232` |
| grants/editorial-band-no-pain.yaml | 2 | `6218e6d800c3` → `173a71953db0` |
| grants/editorial-berserker.yaml | 7 | `dbdf3d57d9a2` → `6d7fc4b24145` |
| grants/editorial-blessed-sight.yaml | 1 | `ffd064781710` → `1e6bc8b7c7de` |
| grants/editorial-conditional-charge.yaml | 2 | `86ee33afd91b` → `890539fd775f` |
| grants/editorial-construct-armour.yaml | 1 | `11fa90a101e5` → `b52d1d338d8e` |
| grants/editorial-crushing-blow.yaml | 2 | `b31baf522f6a` → `c5000685f627` |
| grants/editorial-equipment-vows.yaml | 5 | `4bc966272675` → `419c5ca9fe5a` |
| grants/editorial-ferocious-charge.yaml | 6 | `5e184f974cb5` → `5f53c7b6dfb9` |
| grants/editorial-grants.yaml | 6 | `4d2ab0307bed` → `5ceb75911ec8` |
| grants/editorial-hard-head.yaml | 3 | `b350aae69447` → `a9bf5c2ef991` |
| grants/editorial-head-crusher.yaml | 3 | `50fc06475d05` → `dfc2d42370f8` |
| grants/editorial-khemri-injury.yaml | 1 | `ab5af598630f` → `905477bb9e05` |
| grants/editorial-monster-slayer-armour.yaml | 1 | `f658c4f25283` → `7a45812f72ec` |
| grants/editorial-monster-slayer-trollheim.yaml | 3 | `5b06cff8cf49` → `5560b597debd` |
| grants/editorial-monster-slayer.yaml | 3 | `e28a66ca8aa5` → `e844d1566325` |
| grants/editorial-mutations-and-pain.yaml | 1 | `55e2822afafd` → `bf5423d1e85b` |
| grants/editorial-natural-attacks-pending.yaml | 3 | `ffcde66932e3` → `a81a4a54aaec` |
| grants/editorial-no-pain.yaml | 1 | `b7b2fa9d30a3` → `790a73d0cf21` |
| grants/editorial-pit-fighter-profile-grants.yaml | 6 | `7e0e877cca3f` → `827d770ae4d5` |
| grants/editorial-pit-hard-head.yaml | 2 | `dd2fdaa90275` → `6ec27ea2031b` |
| grants/editorial-poison-immunity.yaml | 2 | `06f07fba4081` → `6f532c124109` |
| grants/editorial-savage-equipment.yaml | 1 | `1616941d4a45` → `a746e93e96cc` |
| grants/editorial-savage-extra-attack.yaml | 1 | `fbb7d84ca966` → `152e9f8870ba` |
| grants/editorial-shield-mastery.yaml | 2 | `08b4e6c1c612` → `ef73946e49e0` |
| grants/editorial-special-skill-access.yaml | 3 | `5dd8f858e8a1` → `fd4656fcc1b4` |
| grants/editorial-stacking-hide.yaml | 6 | `db05e85efbf0` → `415646678f04` |
| grants/editorial-thick-skull.yaml | 6 | `48bf72b842ec` → `c77a178f8747` |
| grants/editorial-tomb-lord-flammable.yaml | 2 | `741fe6de25f3` → `be8f9d65252f` |
| grants/editorial-tomb-scorpion-sting.yaml | 2 | `6c0e927ff513` → `71ab19d973b6` |
| grants/editorial-tough-as-steel.yaml | 4 | `5fa992a5bcf6` → `32aa9fb02559` |
| grants/editorial-troll-regeneration.yaml | 3 | `efb76652e9f0` → `67ca8dcba330` |
| grants/editorial-unarmed-and-beastmen-attacks.yaml | 2 | `033bc089b54e` → `cccd4da74bae` |
| grants/editorial-undead-band-poison.yaml | 2 | `301408e6d4d1` → `4218d899ac95` |
| grants/editorial-vomit-attack.yaml | 3 | `5b9c86fd3159` → `98deb7113470` |
| grants/knighthood.yaml | 1 | `3f590bee0050` → `b667ba29a16e` |
| grants/remaining-compiler-grants-a.yaml | 2 | `ca60713a298f` → `f2c47780176b` |
| grants/remaining-construction-choices.yaml | 1 | `35cd706bc4ce` → `b5112c8064ae` |
| grants/remaining-profile-access.yaml | 2 | `9cd351402e51` → `43f6b3881f8e` |
| grants/remaining-restrictions.yaml | 1 | `f6897567b06d` → `83cc9dc71b1f` |
| grants/trollheim-slayer-skill-options.yaml | 1 | `c2572d572604` → `8012332f4e57` |
| rules/animal-friendship.yaml | 1 | `ece29a355d07` → `2d2403177108` |
| rules/black-hunger-force-and-netter.yaml | 2 | `2869e927afb6` → `29b17fb242ec` |
| rules/contextual-bonuses-and-rulings.yaml | 3 | `185352d05183` → `b8efed8d01f8` |
| rules/mighty-biceps.yaml | 2 | `324895c36f4e` → `28fe544029b3` |
| rules/natural-attacks-and-shield-bash.yaml | 1 | `509e14545a53` → `c58523e82f05` |
| rules/optional-charge-replacements.yaml | 2 | `4bb2b2a1453f` → `0618b51652ed` |

All paths are relative to `tests/specs/semantic/`.

## 6. Error identity comparison and validation results

`verify --json` before → after (`error-identity-comparison.json`):

- errors **155 → 30**; removed **125**, added **0**;
- every removed identity is one of the manifest pairs (`125/125`); no removed
  identity lies outside the manifest;
- the 30 surviving identities are **the same set** as the 30 not-in-manifest
  identities of the baseline (`residual identities unchanged: true`), i.e. the
  historical `source_digest_changed_pre_snapshot` class remains unrepaired;
- all 48 manifest files appear in the removals (125 removed lines in 48 files);
- `structural_complete` stayed `true`; `semantic_complete` stayed `false`;
  obligations 718 → 718.

Commands, exit codes and results (stdout/stderr retained in the evidence
folder):

| Command | Exit | Result |
| --- | --- | --- |
| `python -X utf8 tools/mordheim-utils.py verify --json` (before) | 1 | 155 errors = 125 authorized + 30 residual |
| `python -X utf8 build/cache/t13-parallel/context-data-pins/revalidate.py` | 0 | 125/125 ok, 0 blocked |
| `... apply.py --dry-run` | 0 | 48 files, 125 pairs, 0 blocked, no write |
| `... apply.py` | 0 | 48 files applied, 125 pins, 125 lines, 0 blocked |
| `... post-check.py` | 0 | 48/48 files pass, 125 lines, fingerprints ok, protected unchanged, 0 failures |
| `... compare-identities.py` | 0 | 155 → 30, 125 removed, 0 added |
| `python -X utf8 tools/mordheim-utils.py verify --json` (after) | 1 | 30 errors, exactly the residual set |
| `python -X utf8 tools/mordheim-utils.py verify --structural --json` | 0 | `structural_complete: true`, `structural_errors: []`, 1050 profiles compiled |
| `python -X utf8 -m pytest tests/python/verification/test_semantics.py -q --tb=no -rf` | 1 | **1 failed, 3782 passed in 493.79 s** |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q` | 0 | **1 passed in 0.07 s**; document links checked after the last edit of this file |
| `... closing-check.py` | 0 | manifest/HEAD match, 18/18 protected unchanged, KB clean, 48/48 backups |

`verify` still exits 1 because of the 30 residual historical pins; that is
expected and was not forced.

The single semantic failure is the **inherited** identity
`tests/python/verification/test_semantics.py::test_structural_success_is_not_semantic_success`
(`assert report.errors == ()`), the same one F001 records for the pre-existing
residual debt. It was 1 failed / 3782 passed before this lot and is 1 failed /
3782 passed after it; the failing assertion now rests on the 30 historical pins
only (its first reported identity is
`category-prohibitions-battle-monks-of-cathay-poison`, a residual pair that this
lot is not authorized to touch). No test was modified to change that outcome,
and no new failure appeared.

## 7. Blockers, limits and open questions

- **No pair was blocked.** 125/125 revalidated at entry and 125/125 applied.
- The 30 historical `pre-snapshot` pins remain unpinned to the live KB and keep
  `verify` red; they need source/mechanism-owner review and individual
  dispositions (T13-F001), not a bulk refresh.
- This lot proves fingerprints and byte minimality only. It does not assert
  semantic correctness of the affected rules, the historical engine, or the
  restriction *presentation*; the coordinator’s acceptance explicitly left
  presentation to T13-F041/T15, and no renderer or product path was executed.
- The accepted review’s reproductions (five compile probes, 19-profile matrix,
  bundle freshness) were **not** repeated here; they are independent of a pin
  swap, and the dispatch restricted this lot to the pin edit and its checks.
  T13-F035 therefore stays open.
- The dropped free-text `equipment_restrictions` entries are visible in
  `context-diff.txt` (19 rows, 29 removals) for the coordinator’s routing; this
  lot neither restores nor re-authors them, per the accepted disposition.
- Working-tree counts grew during the lot (198 → 219 entries) because other
  lots kept writing; nothing outside the 48 files is attributable to this lot,
  and the whole-tree `sources/knowledge` hash is unchanged.

## 8. Evidence and next action

Evidence: `build/cache/t13-parallel/context-data-pins/**` (ignored). Key files:
`entry-state.json`/`.txt`, `backup/` (48 byte-for-byte originals) with
`backup-hashes.txt`, `revalidation.json`/`.txt`, `context-diff.json`/`.txt`,
`apply-report.json`, `apply-report.dry-run.json`, `post-check.json`/`.txt`,
`baseline-errors.json`, `verify-before/after.json` (+ exit codes and stderr),
`structural-after.json` (+ exit code), `error-identity-comparison.json`/`.txt`,
`pytest-semantics-after.txt` (+ exit code and the focused failure detail),
`pytest-documentation.txt`, `closing-check.json`/`.txt`, `evidence-index.txt`,
and the scripts `entry-check.py`, `revalidate.py`, `apply.py`, `post-check.py`,
`context-diff.py`, `compare-identities.py`, `closing-check.py`.

Next action for the coordinator: verify the delivery as a bounded pin refresh —
confirm the 48 file hashes moved only by the authorized digest lines, confirm
`verify` now reports the 30 residual identities and nothing else, then record
the accepted 300 + 125 pin state in F001 and decide the routing for the 30
historical pairs and for the presentation check that already sits with
T13-F041/T15. Acceptance, register updates and any phase closure belong to the
coordinator; this lot neither accepted itself nor closed F001, F035, F040,
F041 or T13.

## 9. Independent coordinator acceptance — 2026-10-01

**Accepted; reservation released.** Independent evidence is retained separately
under `build/cache/t13-parallel/context-data-pins-coordinator-review/`.
The coordinator did not invoke the executor's apply or post-check tools for the
minimality proof and did not rely on their result flags.

- All 48 backup hashes match the immutable pre-dispatch manifest hashes.
  Parsed originals were independently changed at exactly the manifest-selected
  specification/source leaves and compared with the complete live structures:
  no additional structural change exists.
- One file, `remaining-profile-access.yaml`, uses existing YAML anchors/aliases.
  An additional immutable leaf traversal checks every logical path, including
  repeated aliases, against the exact authorized path/type/value transitions.
  It confirms 125 logical leaf changes and no indirect alias-induced changes.
  This replaces an overly restrictive initial no-alias assumption with an
  alias-aware proof; no delivery or product file needed a repair.
- A separate byte-line comparison verifies exactly 125 authorized hexadecimal
  transitions. Prefixes, suffixes, comments, quoting, line counts and all other
  bytes are preserved. Reconstructing each original from those changed lines
  reproduces the manifest-hashed backup exactly for all 48 files.
- Fresh maintained inventory fingerprints match all 125 new pins. All 300
  accepted translation pins still hold their authorized current values; all
  30 historical pins still hold their original expected values. Protected
  inputs match the executor's entry, except the coordinator-owned README
  reservation change during this review. KB remains clean.
- Fresh `verify --json` exits 1 and reproduces exactly the 30 historical error
  identities retained in the accepted R0 matrix. The previous 155 minus this
  exact set equals the 125 manifest identities; zero new errors. Its structural
  result is green with 1050 profiles and no structural errors.
- The retained full semantic log reports 1 inherited failure / 3782 passes in
  493.79s. Its focused trace contains the same structural-success assertion on
  the 30 residual pins. The expensive suite was not repeated by the coordinator;
  fresh verification and independent pin/byte checks answer the acceptance risks.
  Documentation links are checked after the acceptance edit.

F001 records **425 reviewed pins updated (300 + 125)** and stays open for the
30 historical pairs, which require source/mechanism-owner dispositions before
any edits. F035 fixture/construction revalidation, F040 independent coverage
review and F041/T15 presentation checks remain separate. No rule behavior,
product code, canonical source, extra pin, commit, push or agent launch resulted
from this coordinator review.
