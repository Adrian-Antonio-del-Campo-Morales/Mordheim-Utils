# Completeness sweep — pre-promotion gate (2026-09-14)

Full sweep of `sources/2B` against all 60 source PDFs and the live external
sources, executed before promotion to the active knowledge base.

## 1. External source: broheim.net (live)

- Live fetch of `warbands.html`: **60 Grade 2b rows observed**.
- Manifest ↔ live match by (broheim_name, source_code): **60/60, 0 problems,
  0 manifest-only, 0 broheim-only**; source-code distribution identical
  (KAZ 8, SAR 11, MOU 10, MIM 13, LUS 4, REL 6, SC 5, KEP 3).

## 2. Source PDFs (60/60)

- Local cache: **60/60 present**.
- SHA-256: local cache hash == manifest hash for all 60.
- **Remote re-download**: fresh fetch of every URL re-hashed — all 60 match
  the manifest. Broheim has not silently changed any source since ingestion.

## 3. Package completeness (60/60)

- Every band has exactly the four canonical documents; no stray files.
- Every document parses and is non-empty.
- All rows status `english-reviewed`; no blockers recorded.

## 4. Content coverage

- 900 special rules across 60 bands; runtime blocks 100% conformant with
  `runtime-schema.yaml` (YES 50 / NO 527 / LATER 323).
- 66 `rule_ref` links resolve against the active KB; 22 rule_ref rules
  deliberately delegate semantics to the shared rule without their own
  effects block; every other rule carries a conformant `effects` block with
  an explicit `reason` when unbound.
- Equipment `item_id` references resolve against the KB or the provisional
  2B catalog; `missing-item-stubs.yaml` has **0 stubs remaining**.
- Spanish i18n: **0 missing** `name_i18n.es` / `effect_i18n.es` across
  387 profiles, 900 rules and 60 band documents.
- Parallel cross-audit (`audit_2b.py`): **problem_count 0**; the 9 info-level
  `profile-name-ocr-unverifiable` entries are all on the scanned KEP bands,
  whose profiles were verified manually at 300/600 dpi.

## 5. Issues the sweep found and fixed

The sweep caught real staging debt left by the transcription passes —
all now fixed:

1. **359 runtime blocks with boolean scopes** (`scope: false` / `true`
   instead of the schema's `"NO"` / `"YES"` strings) and missing
   `effects` classification — normalized across 42 files. The 6 `true`
   (Immune to Poison) rules received the KB-conformant
   `trait.poison-immune` binding plus `rule_ref`.
2. **320 NO/LATER rules without `effects`** — added conformant unbound
   effects with explicit reasons (33 files).
3. **19 YES rules with `effects` misplaced at rule level** — relocated
   inside `runtime` (9 files).
4. **54 files failing `format_yaml.py --check`** — formatted; check now
   passes (one benign 137-char prose line in `catalog/magic-2b.yaml`,
   inside the formatter's own wrapped output).

## 6. Verification

- `ingest_2b.py validate`: **60 rows, 0 problems**
- `pytest tests/knowledge/test_2b_staging.py`: **7/7**
- `format_yaml.py --check sources/2B`: **0 would change, 0 failures**
- `audit_2b.py`: **problem_count 0**

## Verdict

**Nothing remains un-ingested.** All 60 Broheim Grade 2b bands are modeled,
source-verified, hash-pinned, rule/equipment-reference-resolved and
Spanish-translated. The staging tree satisfies every promotion criterion
that does not itself require touching the active KB; the remaining gate is
the promotion run itself (KB merge notes, registry updates, web artifact
regeneration, full test battery).
