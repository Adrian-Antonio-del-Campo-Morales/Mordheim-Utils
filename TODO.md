# Project backlog

Unresolved defects, verification work and deferred capabilities. Procedures
belong in the linked guides; counts and execution details belong in generated
reports. A historical pass does not certify the current tree.


## Knowledge-base consolidation — handoff (2026-11-11)

The goal is for every useful fact to have one authoritative home inside `sources/knowledge/`. Redundant data is removed, information with possible future value is archived, and equivalent rule descriptions share text while preserving the intended application of each rule.

At the time of this handoff, the work was staged and uncommitted on top of `84a634db`. The recorded branch was `hfi/027796c0-…/oak`, abbreviated in the original handoff.

The resulting model is documented in `docs/reference/knowledge-base.md`. The archive preserves the previous wording and migration records needed to understand the consolidation.

### Done

- **Clause register folded into the KB.** `clause-contracts.csv` and `source-scope-review.csv` moved to `docs/archive/clause-register/` with a migration report. Coverage identities now come from the KB through `mordheim_knowledge.clauses`. They include core rules, mechanics retained by the runtime, implemented items and `YES` rule effects. The 351 records whose printed text has several observable parts or excludes a part retain 1,114 clauses in the form `{id, scope}`. Undivided records use their own identity as the coverage target.

- **Contract prose removed from the KB.** The register's contract wording is preserved in the archive. Descriptions of what a test observes belong beside the scenario or test function. Explicit clause IDs and scopes remain where needed to distinguish parts of a rule and preserve deliberate exclusions.

- **Coverage tooling migrated.** `tools/knowledge/clauses.py` provides `inventory`, `coverage`, `check` and `report`. It joins the KB inventory with E2E `audit_id` and `covers` declarations and deterministic `@pytest.mark.covers` markers. `check report rules` runs the clause report. Use `python tools/knowledge/clauses.py coverage --pending` to list outstanding declared coverage.

- **Derived trackers retired.** `implemented-canonical-families.yaml` was removed because the family inventory is derivable from bindings. `registry/bindings.yaml` was removed because the staging trees it described no longer exist. The `clause_registry*.py` tooling and the Combat Lab `audit` export were also removed.

- **Mechanic prose removed.** All 507 mechanic descriptions and their `effect`/`effect_i18n` fields were removed from `catalog/mechanics/close-combat.yaml`. Rules, skills and items bound to a mechanic supply the display text, which the web generator projects onto mechanic rows. Twenty-seven items without text received the description previously stored on their mechanic. The 27 mechanics with no record supplying their text retain a short `note`. The previous descriptions are preserved in `docs/archive/mechanic-texts-2026-11-11.json`.

- **Classification reasons converted to codes.** The 2,139 free-text `reason` values became 13 `reason_codes` declared in `registry/runtime-schema.yaml`. Each code has English and Spanish labels. The loader and editorial schema enforce the vocabulary, and Combat Lab renders the appropriate label. The original text is archived in `docs/archive/reason-texts.csv`.

- **Repeated rule prose consolidated.** The shared catalogue grew from 68 to 143 rules. The number of band rules using `rule_ref` rose from 377 to 742, removing 365 local text copies. Equivalent texts that differed only in the recipient's name were rewritten in neutral form, such as “this warrior”. Eleven numbered or duplicate shared IDs were renamed or retired, including `no-pain-undead` and `troll-stupidity`. The four “never gains Experience” texts were consolidated. The record of merges, rewrites and renames is in `docs/archive/prose-consolidation-2026-11-11.json`.

- **Substantive rule variants retained.** Texts with differences affecting rule application remain separate. These include Skaven hatred variants, wooded versus jungle terrain, two versus one random spell, `+D6` versus `6+` dodge saves, and the Red Fury, Monstrosity and Iron Sinews variants. Future consolidation should preserve those distinctions.

- **Web references updated.** The web artefact gained a `delegating-rules` stem so warrior cards can resolve a band rule ID to its shared text. The generator also projects the printing records' descriptions onto mechanic rows.

- **E2E corpus reworked.** Scaffolds stopped copying register text, and identities were re-keyed to current effect IDs. `covers` is optional because undivided identities require no explicit clause list.

- **Statistical deliveries refreshed.** All 5,163 statistical deliveries were re-pointed at the renamed or re-keyed scaffolds after checking that the scenario bodies were unchanged. The delivery edits were limited to `source` and `case.origin`. The script used for this migration was kept outside the repository.

### Verification at handoff

The handoffs report passing format, name, structural, schema-strictness, clause and skeleton/scaffold checks, subject to the pre-existing failures and name-normalisation exceptions listed below.

The knowledge, construction, full E2E battery, Combat Lab non-UI, tooling, Modular engine, web Vitest and TypeScript package suites passed apart from the recorded exceptions. The Combat Lab UI tests require Tkinter.

The comments in `.github/workflows/ci.yml` were updated. CI had yet to run on the branch.

### Open decisions for the user

- **Night Goblins (KAZ) Animosity.** `band--animosity` prints the same text as Crooked Moon's rule, which binds `mechanic.goblin-squabble`. Aligning the KAZ binding changed every KAZ Night Goblin fighter and broke 13 unrelated E2E scenarios. The alignment was reverted, and the rule retains `out-of-scope.group`. Decide whether the two bands should share the simulated behaviour or whether the KAZ rule requires a different interpretation. If the shared binding is adopted, the affected scenarios need to reflect that intended behaviour.

- **Identical armour-restriction texts with different parameters.** Sixteen rules share the wording “may not wear armour” but encode the restriction through different `profile.equipment-restrictions` parameters, including `armour`, `armour-suit` and explicit item IDs. The prose was consolidated while the existing eligibility parameters were preserved. Review whether those parameters represent intended differences or should converge.

- **Clause scope versus effect scope.** `python tools/knowledge/clauses.py check` lists 30 clauses admitted as `YES` under effects classified `NO` or `LATER`. These came from the register and were retained to preserve the existing E2E identities. Reconcile each clause with its effect by deciding whether the effect should be reclassified or the clause should be withdrawn from admitted coverage.

- **Undead recipient variants.** The shared descriptions `no-pain-undead`, `immune-to-psychology-undead`, `immune-to-poison-undead`, `may-not-run-undead` and `cause-fear-undead` refer to “all warriors with the Undead special rule”. They remain separate from the corresponding per-warrior descriptions. Decide whether that recipient distinction warrants separate shared texts or can be represented while consolidating the wording.

### Remaining consolidation work

- **Item text duplicates.** The step-two analysis reported 18 exact and 10 near-duplicate item texts, including `club`/`mace`, the three staffs, `pistol`/`warp_pistol` and boats. Review each group to decide whether a single record or shared description is appropriate, taking account of differences in item properties and rule application. The review list belongs in `outputs/kb-consolidation-review/` and can be regenerated from the KB.

- **Missing item descriptions.** Twenty canonical items still publish no description. The corresponding web test expects 22 and already failed on the committed tree. Resolve the description gaps and the test's expectation as part of the item review.

- **Item coverage.** Of 163 implemented items, 158 have no deterministic test naming them. Use `python tools/knowledge/clauses.py coverage --kind item --pending` to inspect the outstanding declarations.

- **Campaign spells duplicated across lores.** Compare `woodland-incantations` with `wood-elven-spells`, and `forest-goblin-magic.eadbanger` with `goblin-magic.eadbanger`, against the printed sources. Establish whether both lores exist independently or whether one is a reprint, then consolidate confirmed duplication while preserving distinct rules.

- **Equipment-restriction prose.** Many band rules named `*--equipment-restrictions` restate per-profile information already encoded in `profiles.yaml` and the `profile.equipment-restrictions` binding. Decide whether their wording should remain as printed evidence or become references to a small set of neutral shared texts. This is related to the parameter review above, which determines the actual eligibility behaviour.

- **Observables for E2E authors.** The register's contract phrasing now lives in the archive. When a scaffold is next authored, describe the expected observation in the scenario's comments or the test's docstring. Consider a one-off copy of the archived contracts into unauthored scaffold headers where that wording would help the author.

- **Hireling identities and coverage.** Rules in `catalog/hirelings/*/rules.yaml` and inline hireling profile rules are outside the current coverage identity inventory. Add them to `mordheim_knowledge.clauses` when their E2E or marker coverage starts.

- **TypeScript construction ledger.** `packages/typescript/domain/campaign/construction-clauses.json` remains a separate clause-like store owned by the eligibility domain. It was deliberately left outside this migration. Review whether the same consolidation approach can be applied while preserving its eligibility responsibilities.

- **Spanish translation review.** Review the neutralised Spanish descriptions introduced during consolidation against the printed Spanish sources. The shared rules created on 2026-11-11 are identified in `docs/archive/prose-consolidation-2026-11-11.json`.

- **Commit when accepted.** Commit the staged changes once the user accepts them.

### Pre-existing failures and environment blockers

- **Sunstaff Lustria translation.** The item has English-only prose. This causes two Python test failures and three web test failures involving translation and web completeness.

- **Extra Arm with a shield.** The E2E scenario `band--mutations-extra-arm::a-shield-in-the-extra-arm-still-adds-one-attack` also fails on the committed tree.

- **Name normalisation.** `catalog/campaign/mutations.yaml` and `registry/sources.yaml` have pre-existing title-case drift and fail `normalize_names.py --check` on the committed tree. This was left outside the consolidation diff. Run `normalize_names.py --write` in its own change.

- **Generated web artefact.** One web test requires a `build/generated` artefact that was unavailable in the worktree.

- **Combat Lab UI environment.** The UI tests require Tkinter, which was unavailable in the Python environment used for verification.



## Modular integration and E2E coverage

Strict E2E coverage of the modular oracle is unconfirmed. Close it with
`MORDHEIM_E2E_REQUIRE_COMPLETE=1` over `tests/integration/e2e/` on the delivered
revision, preserving the accepted-evidence baseline and clause identities.
Pending clauses: `python tools/knowledge/clauses.py coverage --pending`.
See the [verification reference](docs/reference/verification.md#modular-integration-closure).

## Web projection verification

Verify Dwarf inheritance in the generated web projection, with evidence from
`outputs/web-public/knowledge/knowledge-web.json` (generate it with
`python tools/knowledge/generate_knowledge_web.py`; never hand-edit it).

## Combat Lab checklist popover closes during layout

Unverified report of `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`). Determine whether widget lifecycle
or test focus setup destroys the popover; close when both pass with their
theme, width and scrollbar assertions intact.

## Optimized-backend verification

Qualify NumPy and Native separately against the modular oracle. Native was
ported from NumPy, so agreement between the two never exonerates a deviation
they share. Keep tolerances and reference provenance intact; procedures are in
the [verification reference](docs/reference/verification.md).

- **Native.** Run the native runtime and deterministic replay selections
  (`tests/engines/native/`): attack-event gating, pool allocation and Rapier
  Barrage touch the replay paths. Then requalify `--scenarios big` against
  `modular-100k` and re-sample `native-e2e-100k` from a clean commit.
- **NumPy stored E2E sample.** `numpy-e2e-100k` predates the current engine.
  Re-sample it from a clean commit (the current engine passes every E2E
  delivery against `modular-e2e-100k` at 20,000 duels, including the Raging
  Peasants fist case that diverged in the stored sample).
- **Systematic E2E offset.** Every NumPy E2E delivery passes the six-sigma
  gate, yet the rates lean one way: over the 1,815 distinct inputs the
  first-win z-scores average about +0.2 and the unresolved ones about +0.9
  against `modular-e2e-100k`. The per-case z-scores share one seed, so their
  mean is less significant than it looks. Determine whether this is an engine
  difference or the oracle-provenance problem below.
- **Oracle provenance.** The stored modular samples carry a source digest that
  matches no commit, and modular commits followed them. Confirm which inputs
  those commits can affect, or regenerate the affected samples with
  authorization, before claiming current-engine certification.
- **Survivor condition (NumPy).** Campaigns compare the winner only. On
  `scenario/stateful` (20,000 duels) the winner of a decided duel is not
  Standing in 1.56 % of duels for Modular and 1.98 % for NumPy. Decide whether
  this is an ordering difference in the deciding round, and whether the
  terminal condition should become a compared magnitude.
- **Portable native digests.** `.pyx` and `.pxd` files have no line-ending rule
  in `.gitattributes`, so Windows and Linux checkouts of one commit produce
  different native digests and spurious provenance warnings.
- **Rejected E2E deliveries.** 2,485 deliveries never run: 1,491 need
  `initial_state` overrides or auxiliary participants the shared runner cannot
  express, 530 prescribe scripted decisions and 464 are expected construction
  refusals. The first two groups stay uncertified until the runner supports
  them.

Stored samples live in `tests/engines/parity/reference_samples/` (seed 2026,
50 rounds for E2E). Compare without running either engine:
`python tools/mordheim-utils.py check samples compare --scenarios e2e
--backend <numpy|native> --store <candidate> --reference-store <modular store>`.
Running the modular engine requires explicit authorization.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause. Catalogue text is corrected; motor support remains pending by user decision (2026-11-10). Sunbolt shooting remains outside the duel. |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
| Make unsupported item-to-engine mappings explicit | Ensure catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing messages and remove unused keys. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md). Scope
changes are governed by
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml);
accepted decisions belong in [Design rulings](docs/decisions/design-rulings.md).
