# Archive

Retired working documents kept for reference. Nothing in the repository reads them, and the
knowledge base under `sources/knowledge/` is the only source of rules, classification and clauses.

| Document | Retired | Why it is kept |
| --- | --- | --- |
| [`clause-register/`](clause-register/README.md) | 2026-11-11 | The two CSV registers whose clauses moved into the knowledge base, with the migration report and the columns that were not migrated. |
| [`kb-printed-text-gaps.md`](kb-printed-text-gaps.md) | 2026-11-11 | The completed 2026-11-10 review of printed-text gaps between the register and the knowledge base; every disposition was applied. |
| [`e2e-grants-corpus-inventory.md`](e2e-grants-corpus-inventory.md) | 2026-11-11 | The authoring handoff of the E2E grants corpus (paths and register references are historical). |
| [`reason-texts.csv`](reason-texts.csv) | 2026-11-11 | The free-text `reason` of every unbound effect (2,139 rows) with the reason code that replaced it. |
| [`mechanic-texts-2026-11-11.json`](mechanic-texts-2026-11-11.json) | 2026-11-11 | The `effect`/`effect_i18n` prose deleted from every close-combat mechanic, the 27 items that received a mechanic's text and the notes kept on the 27 mechanics nothing prints. |
| [`prose-consolidation-2026-11-11.json`](prose-consolidation-2026-11-11.json) | 2026-11-11 | The shared rules created, renamed, rewritten or retired when duplicated band prose was consolidated, every band rule re-pointed with `rule_ref`, and the three bindings aligned with their identical siblings. |
| [`prose-consolidation-2026-11-11-equipment.json`](prose-consolidation-2026-11-11-equipment.json) | 2026-11-11 | The equipment-restriction consolidation: four shared prohibitions added, `wulfen-no-equipment` renamed, 23 band rules re-pointed with their original texts, and the equivalence notes. |
| [`construction-clauses-ledger-2026-11-12.json`](construction-clauses-ledger-2026-11-12.json) | 2026-11-12 | The full T09 construction ledger: the 35 transfers, the review matrix and reconciliation totals that no code read, beside the 26 open clauses that stay live in `packages/typescript/domain/campaign/construction-clauses.json`. |
| [`clause-register/clause-split-2026-11-11.json`](clause-register/clause-split-2026-11-11.json) | 2026-11-11 | Which identities kept clauses (split or excluded parts) and which lost their single `whole` clause when clause contracts were dropped. |

Deleted outright, recoverable from Git history (commit `84a634db` and earlier):
`sources/knowledge/catalog/rules/implemented-canonical-families.yaml` (a tracker derivable from the
runtime bindings), `sources/knowledge/registry/bindings.yaml` (a staging registry whose staging
trees no longer exist) and `tools/knowledge/clause_registry*.py` (the CSV editing tool).
