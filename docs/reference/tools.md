# Repository tools

`tools/` contains reproducible automation or scripts that support an active
workflow. The usual entry point is `python tools/mordheim-utils.py --help`.
Specialized scripts are grouped by purpose, not language or caller.

## Main entry point

| Tool | Purpose |
|---|---|
| `tools/mordheim-utils.py` | Launch applications and centralize tests, local CI, verification, reports, benchmarks, parity and diagnostics. |

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

Catalogue-vs-source cotejo (permanent; the published catalogues are its target and the 2B staging tree a second invocation):

| Tool | Purpose |
|---|---|
| `tools/knowledge/printed_entries.py` | Read a printed entry as the document prints it: geometry, currency and per-check coverage. |
| `tools/knowledge/printed_wordings.py` | The single registry of printed wordings and delegated price lists. |
| `tools/knowledge/source_documents.py` | Resolve a record's `source_refs` to the document that prints it and to its copy in the mirror, through `sources/knowledge/registry/source-documents.yaml`. |
| `tools/knowledge/check_hireling_sources.py` | Compare the published hireling catalogues — Hired Swords and Dramatis Personae, every grade — with the documents that print them; `--tree 2b` runs the same cotejo over the staging tree. |

Reproducible editorial maintenance:

| Tool | Purpose |
|---|---|
| `tools/knowledge/maintenance/format_yaml.py` | Check or apply canonical YAML formatting without semantic changes. |
| `tools/knowledge/maintenance/normalize_names.py` | Check or fix names and IDs according to KB conventions. |
| `tools/knowledge/maintenance/price-collation.py` | Compare catalogue prices and produce reports using reviewed resolutions. |

## 2A/2B ingestion

This group remains temporary but necessary while `sources/2A` and `sources/2B`
are active. Its detailed inventory and removal condition are documented in
[`tools/ingestion/README.md`](../../tools/ingestion/README.md).

| Tools | Purpose |
|---|---|
| `ingest_2a.py`, `ingest_2b.py` | Discover, download, extract, validate and report staging sources. |
| `audit_2a_sources.py` | Single 2A audit: content and numbers (costs, experience, roster, statlines, skill table) read structurally from the cached pages. |
| `audit_2b.py`, `audit_2ab_fidelity.py` | Audit 2B source fidelity and the cross-tree coverage of both staging trees. |
| `audit_2b_negative_tests.py` | Prove that the 2B auditor catches representative corruption. |
| `normalize_staging_for_promotion.py` | Normalize packages into pre-promotion canonical shape. |

Retired one-pass helpers (fill/migrate/repair/image-reading) were removed with their
verdicts recorded in `sources/2A/*.md` and `sources/2B/*.md`.

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
Permanent audits own invariants after a migration: `audit_kb_conformance.py`
rejects duplicated `rule_ref` prose, while schemas and
`test_rule_prose_keys.py` reject the retired `summary` key. Remove one-off
migrations and diagnostics after their result is materialized.
Remove `tools/ingestion/` with its staging references after 2A/2B promotion is
complete.
