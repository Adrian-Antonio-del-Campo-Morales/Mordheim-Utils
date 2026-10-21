# Repository tools

`tools/` contains reproducible automation or scripts that support an active
workflow. The usual entry point is `python tools/mordheim-utils.py --help`.
Specialized scripts are grouped by purpose, not language or caller.

## Main entry point

| Tool | Purpose |
|---|---|
| `tools/mordheim-utils.py` | Launch applications and centralize tests, local CI, verification, reports, benchmarks, parity and diagnostics. |

The [test classification reference](test-sequence.md) defines the phase
categories and their dependency order. `test-sequence` executes Python in that
order; the TypeScript/web suites select the same categories through native
Vitest projects from their own commands.

## Knowledge base

Permanent validation and generation:

| Tool | Purpose |
|---|---|
| `tools/knowledge/audit_kb_conformance.py` | Check canonical knowledge against the expected model. |
| `tools/knowledge/audit_schema_strictness.py` | Detect gaps and unintended permissiveness in editorial schemas. |
| `tools/knowledge/generate_knowledge_web.py` | Generate deterministic JSON consumed by the web application. |
| `tools/knowledge/normalize_open_fields.py` | Normalize controlled vocabulary in open editorial fields. |
| `tools/knowledge/presentation_contract.py` | Build the presentable-text contract used by UI audits. |

Comparison of published catalogues against their printed sources:

| Tool | Purpose |
|---|---|
| `tools/knowledge/printed_entries.py` | Read a printed entry as the document prints it: geometry, currency and per-check coverage. |
| `tools/knowledge/source_documents.py` | Resolve a record's `source_refs` to the document that prints it and to its copy in the mirror, through `sources/knowledge/registry/source-documents.yaml`. |
| `tools/knowledge/check_hireling_sources.py` | Compare the published hireling catalogues — Hired Swords and Dramatis Personae, every grade — with the documents that print them. |

Reproducible editorial maintenance:

| Tool | Purpose |
|---|---|
| `tools/knowledge/maintenance/format_yaml.py` | Check or apply canonical YAML formatting without semantic changes. |
| `tools/knowledge/maintenance/normalize_names.py` | Check or fix names and IDs according to KB conventions. |
| `tools/knowledge/maintenance/price-collation.py` | Compare catalogue prices and produce reports using reviewed resolutions. |

## Verification

| Tool | Purpose |
|---|---|
| `tools/verification/mutate-engine.py` | Run controlled mutations to prove tests detect faults. |
| `tools/verification/refresh_spec_digests.py` | Refresh or check executable-specification digests. |
| `tools/verification/update-coverage-budget.py` | Recalculate the versioned deterministic coverage budget. |

## Web interface

| Tool | Purpose |
|---|---|
| `tools/web/build-eligibility.mjs` | Generate the versioned Python bundle from the shared TypeScript eligibility module; `--check` rejects stale output. Exposed as `npm run build:eligibility` / `npm run check:eligibility`. |
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
the knowledge pipeline guards reject the retired `summary` key. Remove one-off
migrations and diagnostics after their result is materialized.
