# Remaining modular engine problems

Record concrete problems encountered during implementation that remain unresolved
and need a later revisit. Ordinary work stays in
[the semantic CSV](tasks/T13-semantic-analysis.csv); execution order stays in
[the work plan](REMAINING_MODULAR_ENGINE_WORK.md). Questions requiring human
authority belong in [Remaining human decisions](REMAINING_HUMAN_DECISIONS.md).

## Register rules

- Resolve problems within the assignment when possible. Record an obstacle only
  with its rule/clause, affected files, observed discrepancy, relevant evidence,
  what was attempted and why it remains unresolved, and the condition for resuming.
- Reuse the entry for the same cause and continue independent implementation.
  An ordinary unfinished task or missing E2E scenario is not itself a defect.
- Reload before editing and preserve concurrent changes. Respect file ownership;
  `tests/E2E/modular-engine/cases/grants` retains its external owner.
- Remove resolved entries after retaining useful decisions/evidence in their
  canonical files. Do not accumulate delivery histories or duplicate CSV contracts.

## Web artefact regeneration — conflicting translated rule labels

- **Latest delivered failure (C15, 2026-10-17):** `conflicting Spanish rule label
  for 'No Missile Weapons'` in knights-of-the-bitter-moors-mim/special-rules.yaml:
  `Sin armas de proyectil` versus `Sin Armas de Proyectil`. The web artefact still
  exposes the old selectable Dwarf inheritance; canonical Python construction
  and modular consumption are corrected. Evidence and ownership limitation in
  `deliveries/C15-Dwarf-inheritance-completed.md`. No coordinator generator rerun.
- **Observed:** the real generator
  `python tools/knowledge/generate_knowledge_web.py --output build/generated/knowledge-web/knowledge-web.json`
  stops in `_build_rules_prose` with
  `GenerationError: conflicting Spanish rule label for 'Mer-Creature'`.
- **Evidence:** Crude Belch and Bull Charge fallbacks have been reconciled with
  their existing canonical Spanish labels. The generator was rerun after the
  Bull Charge correction and advanced to the next genuine collision, Mer-Creature.
  The generator has not been weakened or bypassed. The failing output is retained
  outside the deliverable tree (`modular-web-generation-after-bull-label.txt` in
  the system temporary directory); do not repeat this unchanged generation.
- **Impact:** the shared Python catalogue now loads without an exclusion overlay,
  but the old web artefact cannot certify Aquatic Mutants' current web route.
  Its functional TypeScript test was not rerun against a stale artefact.
- **Resume/close:** reconcile the actual conflicting labels while preserving
  source-specific prose, generate with the maintained tool, then execute
  `tests/typescript/domain/campaign/mutations.test.ts` against the fresh artefact.
  Do not hand-edit generated JSON or weaken validation just to make generation pass.
