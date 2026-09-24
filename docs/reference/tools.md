# Repository tools

`tools/` contains reproducible automation or scripts that support an active
workflow. The usual entry point is `python tools/mordheim-utils.py --help`.
Specialized scripts are grouped by purpose, not language or caller.

## Main entry point and shell

| Tool | Purpose |
|---|---|
| `tools/mordheim-utils.py` | Launch applications and centralize tests, local CI, verification, reports, benchmarks, parity and diagnostics. |
| `tools/completions/mordheim-utils.bash` | Bash completion for the launcher. |
| `tools/completions/mordheim-utils.zsh` | Zsh completion for the launcher. |

## Knowledge base

Permanent validation and generation:

| Tool | Purpose |
|---|---|
| `tools/knowledge/audit_kb_conformance.py` | Check canonical or staged knowledge against the expected model. |
| `tools/knowledge/audit_schema_strictness.py` | Detect gaps and unintended permissiveness in editorial schemas. |
| `tools/knowledge/audit_staging_contract.py` | Validate schema, shape, names and catalogues before 2A/2B promotion. |
| `tools/knowledge/derive_kb_contract.py` | Derive and verify the observed structural contract. |
| `tools/knowledge/generate_knowledge_web.py` | Generate deterministic JSON consumed by the web application. |
| `tools/knowledge/normalize_open_fields.py` | Normalize controlled vocabulary in open editorial fields. |
| `tools/knowledge/presentation_contract.py` | Build the presentable-text contract used by UI audits. |
| `tools/knowledge/strip_rule_ref_restatements.py` | Remove duplicated prose when a rule already references shared text. |

Reproducible editorial maintenance:

| Tool | Purpose |
|---|---|
| `tools/knowledge/maintenance/band_translation_status.py` | Report translation coverage by warband. |
| `tools/knowledge/maintenance/combine_kb_yaml.py` | Combine YAML by directory for external review; also exposed as `combine-kb`. |
| `tools/knowledge/maintenance/format_yaml.py` | Check or apply canonical YAML formatting without semantic changes. |
| `tools/knowledge/maintenance/normalize_names.py` | Check or fix names and IDs according to KB conventions. |
| `tools/knowledge/maintenance/price-collation.py` | Compare catalogue prices and produce reports using reviewed resolutions. |
| `tools/knowledge/maintenance/rename_summary_keys.py` | Migrate historical `summary` keys to `effect` in old staging trees. |
| `tools/knowledge/maintenance/translate_band.py` | Apply a reviewed translation file to one warband. |

## 2A/2B ingestion

This group remains temporary but necessary while `sources/2A` and `sources/2B`
are active. Its detailed inventory and removal condition are documented in
[`tools/ingestion/README.md`](../../tools/ingestion/README.md).

| Tools | Purpose |
|---|---|
| `ingest_2a.py`, `ingest_2b.py` | Discover, download, extract, validate and report staging sources. |
| `review_2a.py`, `review_2b.py` | Revalidate editorial values against extracted text. |
| `audit_2a.py`, `audit_2a_sources.py`, `audit_2b.py`, `audit_2ab_fidelity.py` | Audit source fidelity, coverage and consistency. |
| `audit_2b_negative_tests.py` | Prove that the 2B auditor catches representative corruption. |
| `check_2a_dramatis.py`, `check_2b_hirelings.py` | Compare Dramatis Personae and Hired Swords with their sources. |
| `printed_entries.py`, `printed_wordings.py` | Shared geometric source reader and printed-wording registry. |
| `normalize_staging_for_promotion.py` | Normalize packages into pre-promotion canonical shape. |
| `migrate_2b_kb_schema.py`, `migrate_staging_records.py` | Migrate old records still present in staging. |
| `fill_2a_es_effects.py`, `fill_2b_es_effects.py`, `fill_2b_prayer_lores.py`, `repair_2b_flow_i18n.py` | Complete or repair remaining targeted 2A/2B fields. |
| `find_stub_sources.py`, `read_2b_kep_stats.py`, `read_scanned_costs.py` | Find incomplete sources and extract data requiring specialized readers. |

## Verification

| Tool | Purpose |
|---|---|
| `tools/verification/make_test_manifest.py` | Regenerate the Python/TypeScript parity manifest in `outputs/parity/test-manifests/`. |
| `tools/verification/mutate-engine.py` | Run controlled mutations to prove tests detect faults. |
| `tools/verification/refresh_spec_digests.py` | Refresh or check executable-specification digests. |
| `tools/verification/update-coverage-budget.py` | Recalculate the versioned deterministic coverage budget. |

## Web interface

| Tool | Purpose |
|---|---|
| `tools/web/presentation-audit.mjs` | Detect visible text without validated resolution or provenance. |
| `tools/web/presentation-flow-audit.mjs` | Trace raw text to presentation sinks. |
| `tools/web/presentation-type-audit.mjs` | Detect forged resolved-text types. |

Their tests live in `tests/web/tools/`, not under `tools/`.

## Windows packaging

| Tool | Purpose |
|---|---|
| `tools/windows/build_MordheimCombatLab_ONEFILE.bat` | Build the single-file Combat Lab executable. |
| `tools/windows/build_MordheimCombatLab_INSTALLER.bat` | Build the installer from that executable. |
| `tools/windows/MordheimCombatLab.iss` | Inno Setup recipe used by the installer script. |

## Retention rule

Keep a tool only when it is owned by a current documented workflow, a test or
CI gate, the central launcher, or a repeatable operation over active data.
Remove one-off migrations and diagnostics after their result is materialized.
Remove `tools/ingestion/` with its staging references after 2A/2B promotion is
complete.
